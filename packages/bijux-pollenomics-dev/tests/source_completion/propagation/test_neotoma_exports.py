"""Reject every non-URL export mutation and preserve exact named physical custody."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def module() -> ModuleType:
    root = next(
        p
        for p in Path(__file__).parents
        if (
            p
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/propagation/neotoma_exports.py"
        ).is_file()
    )
    path = (
        root
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/propagation/neotoma_exports.py"
    )
    spec = importlib.util.spec_from_file_location("neotoma_export_custody", path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def export() -> dict[str, Any]:
    return {
        "selection": {"shared_url": "reference", "window": [0, 100]},
        "records": [{"id": "native1", "count": 4}, {"id": "native2", "count": 0}],
        "claims": {"scientific_admission": False},
    }


def test_exact_declared_leaf_transition_preserves_every_other_value() -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = "captured"
    assert (
        len(module().validate_selection_transition(old, new, "reference", "captured"))
        == 64
    )
    assert old == export()


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "sample-id",
        "order",
        "bool-as-int",
        "extra-key",
        "missing-key",
        "window",
        "provenance",
    ],
)
def test_other_export_mutations_refuse(mutation: str) -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = "captured"
    if mutation == "count":
        new["records"][0]["count"] = 5
    elif mutation == "sample-id":
        new["records"][0]["id"] = "other"
    elif mutation == "order":
        new["records"].reverse()
    elif mutation == "bool-as-int":
        new["claims"]["scientific_admission"] = 0
    elif mutation == "extra-key":
        new["extra"] = None
    elif mutation == "missing-key":
        del new["claims"]
    elif mutation == "window":
        new["selection"]["window"][0] = 1
    else:
        new["provenance"] = {"source": "invented"}
    with pytest.raises(ValueError, match="outside /selection/shared_url"):
        module().validate_selection_transition(old, new, "reference", "captured")


def test_object_field_order_change_refuses() -> None:
    old = export()
    new = dict(reversed(list(deepcopy(old).items())))
    new["selection"]["shared_url"] = "captured"
    with pytest.raises(ValueError, match="outside"):
        module().validate_selection_transition(old, new, "reference", "captured")


@pytest.mark.parametrize("url", ["reference", "another-port", None, 1])
def test_unknown_url_or_type_refuses(url: object) -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = url
    with pytest.raises(ValueError, match="Named shared URL"):
        module().validate_selection_transition(old, new, "reference", "captured")


@pytest.mark.parametrize(
    "raw", [b'{"key":1,"key":2}', b'{"number":NaN}', b'{"number":1e999}', b"[]"]
)
def test_ambiguous_or_nonfinite_json_refuses(raw: bytes) -> None:
    with pytest.raises(ValueError):
        module()._object(raw)


@pytest.mark.parametrize("path", ["../outside", "/outside", "data/../outside"])
def test_confined_physical_custody_refuses_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError):
        module()._file(tmp_path, path)


def readiness_reference() -> dict[str, Any]:
    code = module()
    return {
        "source_identity": {
            "export_sha256": {site: before for site, before, _ in code.EXPECTED_EXPORTS}
        },
        "denominators": {"refused": 256, "events": 0, "estimator_invocations": 0},
        "claims": {"first_observed_events_admitted": False},
        "attempts": [{"count": 4}],
    }


def readiness_current() -> dict[str, Any]:
    row = readiness_reference()
    row["source_identity"]["export_sha256"] = {
        site: after for site, _, after in module().EXPECTED_EXPORTS
    }
    return row


def test_only_two_named_readiness_digest_changes_are_permitted() -> None:
    module().validate_readiness_transition(readiness_reference(), readiness_current())


@pytest.mark.parametrize(
    "field",
    [
        "events",
        "refused",
        "estimator_invocations",
        "promotion",
        "attempt",
        "extra-site",
    ],
)
def test_any_other_readiness_scientific_change_refuses(field: str) -> None:
    row = readiness_current()
    if field in row["denominators"]:
        row["denominators"][field] += 1
    elif field == "promotion":
        row["claims"]["first_observed_events_admitted"] = True
    elif field == "attempt":
        row["attempts"][0]["count"] = 5
    else:
        row["source_identity"]["export_sha256"]["another"] = "unknown"
    with pytest.raises(ValueError, match="outside the two export digests"):
        module().validate_readiness_transition(readiness_reference(), row)


def test_physical_reference_symlink_refuses(tmp_path: Path) -> None:
    (tmp_path / "source").write_text("original")
    (tmp_path / "alias").symlink_to(tmp_path / "source")
    with pytest.raises(ValueError, match="confined regular"):
        module()._file(tmp_path, "alias")


def physical_certificate(
    root: Path,
) -> tuple[dict[str, Any], tuple[tuple[str, str, str], ...]]:
    """Own tiny declared source/capture files without authenticating production data."""
    import gzip
    import hashlib
    import json

    def write(name: str, raw: bytes) -> str:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    manifest_sha = write("native/manifest.json", b'{"source":"controlled"}')
    rows: list[dict[str, Any]] = []
    members: list[dict[str, Any]] = []
    expected: list[tuple[str, str, str]] = []
    for site in ("12", "3009"):
        original: dict[str, Any] = {
            "selection": {"shared_url": "original-" + site},
            "chronology": {"younger_bp": None, "older_bp": None, "raw_age": 0},
            "records": [
                {"id": "native-" + site, "count": 0, "source_denominator": None}
            ],
            "claims": {"scientific_admission": False, "refusal": "unreviewed"},
        }
        captured = deepcopy(original)
        captured["selection"]["shared_url"] = "captured-" + site
        raw = json.dumps(original, separators=(",", ":")).encode()
        shown = json.dumps(captured, separators=(",", ":")).encode()
        storage = gzip.compress(raw, mtime=0)
        reference_path = "references/" + site + ".json.gz"
        member = "observations/" + site + ".json"
        reference_sha = hashlib.sha256(raw).hexdigest()
        shown_sha = write("capture/" + member, shown)
        exported_path = "published/" + site + ".json"
        assert write(exported_path, shown) == shown_sha
        rows.append(
            {
                "site_id": site,
                "export_path": exported_path,
                "reference_path": reference_path,
                "reference_storage_sha256": write(reference_path, storage),
                "reference_sha256": reference_sha,
                "content_bytes": len(raw),
                "export_sha256": shown_sha,
                "captured_member": member,
                "reference_shared_url": "original-" + site,
                "export_shared_url": "captured-" + site,
                "all_other_ordered_json_sha256": module().validate_selection_transition(
                    original, captured, "original-" + site, "captured-" + site
                ),
            }
        )
        members.append({"path": member, "sha256": shown_sha, "bytes": len(shown)})
        expected.append((site, reference_sha, shown_sha))
    capture = {
        "source_candidate": "controlled",
        "scientific_admission": False,
        "files": members,
    }
    capture_sha = write("capture/capture.json", json.dumps(capture).encode())
    return {
        "source_manifest": {"path": "native/manifest.json", "sha256": manifest_sha},
        "browser_capture": {
            "path": "capture/capture.json",
            "sha256": capture_sha,
            "source_candidate": "controlled",
        },
        "exports": rows,
    }, tuple(expected)


def test_current_capture_requires_exact_published_physical_bytes(
    tmp_path: Path,
) -> None:
    proof, expected = physical_certificate(tmp_path)
    module()._validate_captured_exports(tmp_path, proof, expected, published=True)
    (tmp_path / "published/12.json").write_text('{"changed":"physical"}')
    with pytest.raises(ValueError, match="current/captured export bytes differ"):
        module()._validate_captured_exports(tmp_path, proof, expected, published=True)


def test_retained_capture_is_a_separate_epoch_from_published_bytes(
    tmp_path: Path,
) -> None:
    proof, expected = physical_certificate(tmp_path)
    (tmp_path / "published/12.json").write_text('{"later":"publication"}')
    module()._validate_captured_exports(tmp_path, proof, expected, published=False)
    with pytest.raises(ValueError, match="current/captured export bytes differ"):
        module()._validate_captured_exports(tmp_path, proof, expected, published=True)


def test_declared_current_capture_and_site_scope_are_exact(tmp_path: Path) -> None:
    proof, expected = physical_certificate(tmp_path)
    wrong = (expected[0], ("other", expected[1][1], expected[1][2]))
    with pytest.raises(ValueError, match="Named two-export scope differs"):
        module()._validate_captured_exports(tmp_path, proof, wrong, published=True)
    (tmp_path / "capture/capture.json").write_text('{"tampered":true}')
    with pytest.raises(ValueError, match="physical browser capture differs"):
        module()._validate_captured_exports(tmp_path, proof, expected, published=True)


@pytest.mark.parametrize(
    "mutation",
    ["null-zero", "zero-false", "refusal", "record-id", "field-order", "nonfinite"],
)
def test_rebound_physical_capture_never_waives_non_url_source_fields(
    tmp_path: Path, mutation: str
) -> None:
    import hashlib
    import json

    proof, expected = physical_certificate(tmp_path)
    current = json.loads((tmp_path / "published/12.json").read_bytes())
    if mutation == "null-zero":
        current["chronology"]["younger_bp"] = 0
    elif mutation == "zero-false":
        current["records"][0]["count"] = False
    elif mutation == "refusal":
        current["claims"]["refusal"] = "admitted"
    elif mutation == "record-id":
        current["records"][0]["id"] = "another-native"
    elif mutation == "field-order":
        current = dict(reversed(list(current.items())))
    else:
        current["chronology"]["raw_age"] = float("nan")
    raw = json.dumps(current, separators=(",", ":")).encode()
    digest = hashlib.sha256(raw).hexdigest()
    (tmp_path / "published/12.json").write_bytes(raw)
    (tmp_path / "capture/observations/12.json").write_bytes(raw)
    capture = json.loads((tmp_path / "capture/capture.json").read_bytes())
    capture["files"][0].update(sha256=digest, bytes=len(raw))
    capture_raw = json.dumps(capture).encode()
    (tmp_path / "capture/capture.json").write_bytes(capture_raw)
    proof["browser_capture"]["sha256"] = hashlib.sha256(capture_raw).hexdigest()
    proof["exports"][0]["export_sha256"] = digest
    expected = ((expected[0][0], expected[0][1], digest), expected[1])
    with pytest.raises(ValueError, match="outside /selection/shared_url|Nonfinite"):
        module()._validate_captured_exports(tmp_path, proof, expected, published=True)


def test_physical_capture_scientific_false_cannot_be_integer_zero(
    tmp_path: Path,
) -> None:
    import hashlib
    import json

    proof, expected = physical_certificate(tmp_path)
    capture = json.loads((tmp_path / "capture/capture.json").read_bytes())
    capture["scientific_admission"] = 0
    raw = json.dumps(capture).encode()
    (tmp_path / "capture/capture.json").write_bytes(raw)
    proof["browser_capture"]["sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="source/admission differs"):
        module()._validate_captured_exports(tmp_path, proof, expected, published=True)
