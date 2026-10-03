"""Draw-fed LOVE requests keep source, time, taxa and cohort claims aligned."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs import regional_draw_love
from bijux_pollenomics.analysis.lra.inputs.regional_draw_love import (
    validate_regional_draw_love_request,
)

from ..support import regional_draw_love_fixture


def _source() -> SimpleNamespace:
    return SimpleNamespace(
        taxon_ids=("A", "B", "C"),
        bin_id="recent",
        younger_bp=0.0,
        older_bp=100.0,
        regional_site_ids=("small", "large"),
    )


def _payload(root: Path) -> dict[str, object]:
    return regional_draw_love_fixture(
        root,
        bundle=root / "regional",
        checksums_sha256="a" * 64,
    )


def _mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def _rows(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return [_mapping(row) for row in value]


def _rewrite_receipt(
    payload: dict[str, object], root: Path, *, directory: str | None = None
) -> None:
    declaration = _mapping(payload["regional_draw_source"])
    item = next(
        row
        for row in _rows(payload["evidence"])
        if row["evidence_id"] == declaration["receipt_evidence_id"]
    )
    bundle_directory = declaration["directory"]
    checksums_sha256 = declaration["expected_checksums_sha256"]
    receipt_path = item["path"]
    assert isinstance(bundle_directory, str)
    assert isinstance(checksums_sha256, str)
    assert isinstance(receipt_path, str)
    content = (
        json.dumps(
            {
                "schema_version": "regional-draw-source-receipt.v1",
                "bundle_directory": directory or bundle_directory,
                "checksums_sha256": checksums_sha256,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()
    (root / receipt_path).write_bytes(content)
    item["sha256"] = hashlib.sha256(content).hexdigest()


def test_distinct_request_retains_exact_draw_source_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        regional_draw_love,
        "read_multisite_regional_draw_source",
        lambda *args, **kwargs: _source(),
    )
    payload = _payload(tmp_path)
    accepted = validate_regional_draw_love_request(payload, input_root=tmp_path)
    assert accepted.payload()["schema_version"] == ("lra-regional-draw-love-request.v1")
    assert "regional" not in accepted.payload()
    assert accepted.payload()["regional_draw_source"]["cohort_disposition"] == (
        "excluded_from_source"
    )


@pytest.mark.parametrize(
    "case,reason",
    [
        ("regional", "invalid_lra_schema"),
        ("absolute", "regional_draw_source_outside_root"),
        ("parent", "regional_draw_source_outside_root"),
        ("parameter_order", "parameter_taxon_mismatch"),
        ("taxa", "regional_draw_taxon_mismatch"),
        ("bounds", "regional_draw_time_mismatch"),
        ("cohort", "regional_draw_cohort_mismatch"),
        ("receipt", "invalid_regional_draw_source_receipt"),
        ("receipt_binding", "invalid_regional_draw_source_receipt"),
        ("fallspeed", "invalid_lra_schema"),
        ("ring", "invalid_analytical_ring_support"),
    ],
)
def test_ambiguous_or_false_draw_requests_are_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    case: str,
    reason: str,
) -> None:
    source = _source()
    monkeypatch.setattr(
        regional_draw_love,
        "read_multisite_regional_draw_source",
        lambda *args, **kwargs: source,
    )
    payload = _payload(tmp_path)
    if case == "regional":
        payload["regional"] = deepcopy(payload["local"])
    elif case == "absolute":
        _mapping(payload["regional_draw_source"])["directory"] = str(
            tmp_path / "regional"
        )
        _rewrite_receipt(payload, tmp_path)
    elif case == "parent":
        _mapping(payload["regional_draw_source"])["directory"] = "regional/../regional"
        _rewrite_receipt(payload, tmp_path)
    elif case == "parameter_order":
        payload["parameters"] = list(reversed(_rows(payload["parameters"])))
    elif case == "taxa":
        payload["taxa"] = ["C", "B", "A"]
        _rows(_mapping(payload["local"])["samples"])[0]["counts"] = [30, 30, 40]
        payload["parameters"] = list(reversed(_rows(payload["parameters"])))
    elif case == "bounds":
        _rows(_mapping(payload["temporal_matching"])["bins"])[0]["older_bp"] = 101
    elif case == "cohort":
        _rows(_mapping(payload["local"])["samples"])[0]["site_id"] = "small"
    elif case == "receipt":
        payload["evidence"] = [
            row
            for row in _rows(payload["evidence"])
            if row["role"] != "draw_source_receipt"
        ]
    elif case == "receipt_binding":
        _rewrite_receipt(payload, tmp_path, directory="different-regional-product")
    elif case == "fallspeed":
        _rows(payload["parameters"])[0]["fallspeed_m_s"] = 0.005
    else:
        _rows(payload["rings"])[0]["inner_m"] = 10
        _rows(payload["rings"])[0]["mean_m"] = 50
    with pytest.raises(LRARefusal) as raised:
        validate_regional_draw_love_request(payload, input_root=tmp_path)
    assert raised.value.reason_code == reason


@pytest.mark.parametrize("kind", ["final", "intermediate"])
def test_draw_source_paths_refuse_every_symlink_component(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    if kind == "final":
        bundle = tmp_path / "regional-link"
        bundle.symlink_to(target, target_is_directory=True)
    else:
        (target / "regional").mkdir()
        link = tmp_path / "linked-parent"
        link.symlink_to(target, target_is_directory=True)
        bundle = link / "regional"
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=bundle,
        checksums_sha256="a" * 64,
    )
    monkeypatch.setattr(
        regional_draw_love,
        "read_multisite_regional_draw_source",
        lambda *args, **kwargs: pytest.fail("reader must not receive a symlink path"),
    )
    with pytest.raises(LRARefusal) as raised:
        validate_regional_draw_love_request(payload, input_root=tmp_path)
    assert raised.value.reason_code == "regional_draw_source_symlink"


def test_source_overlap_requires_explicit_method_control_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        regional_draw_love,
        "read_multisite_regional_draw_source",
        lambda *args, **kwargs: _source(),
    )
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=tmp_path / "regional",
        checksums_sha256="a" * 64,
        local_site_id="small",
        cohort_disposition="included_method_control",
    )
    accepted = validate_regional_draw_love_request(payload, input_root=tmp_path)
    assert accepted.payload()["regional_draw_source"]["cohort_disposition"] == (
        "included_method_control"
    )
