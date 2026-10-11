"""Retained ABBO ledger and atomic mathematical diagnostic boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_joint_membership as producer,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_membership,
)


@pytest.fixture(scope="module")
def source() -> tuple[bytes, bytes, bytes]:
    """Load unchanged repository public ledgers without original study execution."""
    root = Path(__file__).resolve().parents[5]
    return (
        (root / abborrtjarne_membership.SUPPORT).read_bytes(),
        (root / producer.MEMBERSHIP).read_bytes(),
        (root / producer.REPORT).read_bytes(),
    )


def test_original_source_accounting_proves_all_sixteen_corners_unattainable(
    source: tuple[bytes, bytes, bytes],
) -> None:
    report = producer.derive(*source)
    assert report["sample_count"] == 107
    assert report["membership_row_count"] == 428
    assert report["source_native_negative_younger_bound_count"] == 5
    assert report["extrema_tuple_count"] == 16
    assert report["simultaneously_attainable_tuple_count"] == 0
    corners = report["corners"]
    assert isinstance(corners, list)
    assert all(
        isinstance(corner, dict) and corner["refusals"] and not corner["assignments"]
        for corner in corners
    )


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "bounds",
        "sample_count",
        "membership_row_count",
        "membership_sha256",
        "membership_status_counts",
    ],
)
def test_missing_retained_contract_field_refuses(
    source: tuple[bytes, bytes, bytes], field: str
) -> None:
    support, membership, data = source
    report = json.loads(data)
    del report[field]
    with pytest.raises(ValueError):
        producer.derive(support, membership, json.dumps(report).encode())


def test_duplicate_json_field_refuses(source: tuple[bytes, bytes, bytes]) -> None:
    support, membership, _ = source
    with pytest.raises(ValueError, match="Duplicate"):
        producer.derive(support, membership, b'{"bounds":[],"bounds":[]}')


def test_duplicate_membership_and_changed_source_counts_refuse(
    source: tuple[bytes, bytes, bytes],
) -> None:
    support, membership, data = source
    with pytest.raises(ValueError, match="Duplicate"):
        producer.derive(
            support, membership + membership.splitlines(keepends=True)[1], data
        )
    with pytest.raises(ValueError):
        producer.derive(
            support.replace(
                b"outside_common_bins,1157,307", b"outside_common_bins,1157,308", 1
            ),
            membership,
            data,
        )
    with pytest.raises(ValueError):
        producer.derive(
            support.replace(
                b"outside_common_bins,1157,307", b"outside_common_bins,1157,+307", 1
            ),
            membership,
            data,
        )


def test_runtime_source_origin_and_hash_identity_are_qualified() -> None:
    root = Path(__file__).resolve().parents[5]
    identities = producer._inputs(root)
    assert str(abborrtjarne_membership.SUPPORT) in identities
    assert str(producer.REPORT) in identities
    assert len(identities) == len(producer.RETAINED_INPUTS) + 3


@pytest.mark.parametrize(
    "module_name",
    ("joint_membership", "abborrtjarne_membership", "abborrtjarne_joint_membership"),
)
def test_shadowed_source_module_origin_refuses(
    module_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = Path(__file__).resolve().parents[5]
    shadow = tmp_path / f"{module_name}.py"
    shadow.write_text("# shadow source\n")
    module = (
        producer
        if module_name == "abborrtjarne_joint_membership"
        else getattr(producer, module_name)
    )
    monkeypatch.setattr(module, "__file__", str(shadow))
    with pytest.raises(ValueError, match="source module must be loaded"):
        producer._inputs(root)


def test_missing_source_refuses(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="regular confined"):
        producer._inputs(tmp_path)


def test_atomic_publication_and_existing_output_refusal(
    source: tuple[bytes, bytes, bytes], tmp_path: Path
) -> None:
    (tmp_path / "artifacts").mkdir()
    target = tmp_path / "artifacts" / "joint-membership"
    source_paths = [
        abborrtjarne_membership.SUPPORT,
        producer.MEMBERSHIP,
        producer.REPORT,
    ]
    for relative, data in zip(source_paths, source, strict=True):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    # Boundary qualification is independently covered above; this case isolates
    # the publication protocol using the real mathematical ledger consumer.
    with patch.object(producer, "_inputs", return_value={}):
        result = producer.run(tmp_path, target)
        assert json.loads((target / "report.json").read_bytes()) == result
        with pytest.raises(ReportRebuildError, match="absent"):
            producer.run(tmp_path, target)


def test_prepublish_source_drift_refuses_without_product(
    source: tuple[bytes, bytes, bytes], tmp_path: Path
) -> None:
    (tmp_path / "artifacts").mkdir()
    target = tmp_path / "artifacts" / "joint-membership"
    for relative, data in zip(
        [
            abborrtjarne_membership.SUPPORT,
            producer.MEMBERSHIP,
            producer.REPORT,
        ],
        source,
        strict=True,
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    with (
        patch.object(
            producer, "_inputs", side_effect=[{}, ValueError("source changed")]
        ),
        pytest.raises(ValueError, match="source changed"),
    ):
        producer.run(tmp_path, target)
    assert not target.exists()
    assert not list((tmp_path / "artifacts").iterdir())


def test_nonartifact_and_symlink_output_refuse(tmp_path: Path) -> None:
    (tmp_path / "artifacts").mkdir()
    with pytest.raises(ReportRebuildError):
        producer.run(tmp_path, tmp_path / "outside")
    link = tmp_path / "artifacts" / "alias"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        producer.run(tmp_path, link / "output")
