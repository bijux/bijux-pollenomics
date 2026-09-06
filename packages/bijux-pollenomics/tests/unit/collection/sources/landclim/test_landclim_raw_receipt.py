from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from bijux_pollenomics.collection.sources.landclim.collection import (
    LandClimRawReceiptError,
    validate_landclim_raw_receipt,
)

from tests.support.repository import REPOSITORY_ROOT

_REPOSITORY_ROOT = REPOSITORY_ROOT
_RAW_ROOT = _REPOSITORY_ROOT / "data" / "landclim" / "raw"


def test_checked_in_landclim_receipt_binds_all_raw_assets() -> None:
    receipt = validate_landclim_raw_receipt(_RAW_ROOT)

    assets = receipt["assets"]
    archives = receipt["archive_summaries"]
    assert isinstance(assets, list)
    assert isinstance(archives, list)
    assert receipt["asset_count"] == 7
    assert len(assets) == 7
    assert all(
        isinstance(asset, dict)
        and isinstance(asset["size_bytes"], int)
        and len(str(asset["sha256"])) == 64
        and str(asset["source_url"]).startswith("https://")
        and str(asset["dataset_doi"]).startswith("https://doi.org/")
        for asset in assets
    )
    assert archives == [
        {
            "filename": "landclim_ii_reveals_results.zip",
            "member_count": 50,
            "uncompressed_size_bytes": 9964310,
            "member_manifest_sha256": (
                "0d09ed48245409eca0d8551ef5e25bf60ef49f3e5c807e7e2487e15e7f1a3bfe"
            ),
            "member_digest_basis": "sha256-canonical-json-path-size-sha256",
            "mean_file_count": 25,
            "standard_error_file_count": 25,
            "time_windows": [
                "0-100 BP",
                "100-350 BP",
                "350-700 BP",
                "700-1200 BP",
                "1200-1700 BP",
                "1700-2200 BP",
                "2200-2700 BP",
                "2700-3200 BP",
                "3200-3700 BP",
                "3700-4200 BP",
                "4200-4700 BP",
                "4700-5200 BP",
                "5200-5700 BP",
                "5700-6200 BP",
                "6200-6700 BP",
                "6700-7200 BP",
                "7200-7700 BP",
                "7700-8200 BP",
                "8200-8700 BP",
                "8700-9200 BP",
                "9200-9700 BP",
                "9700-10200 BP",
                "10200-10700 BP",
                "10700-11200 BP",
                "11200-11700 BP",
            ],
        }
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("missing", "inventory mismatch"),
        ("changed", "digest mismatch"),
        ("unlisted", "inventory mismatch"),
    ),
)
def test_landclim_receipt_refuses_missing_changed_and_unlisted_assets(
    tmp_path: Path, mutation: str, message: str
) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(_RAW_ROOT, raw_root)
    asset = raw_root / "landclim_ii_taxa_pft_ppe_fsp_values.csv"
    if mutation == "missing":
        asset.unlink()
    elif mutation == "changed":
        payload = asset.read_bytes()
        asset.write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
    else:
        (raw_root / "unlisted.csv").write_text("unlisted\n", encoding="utf-8")

    with pytest.raises(LandClimRawReceiptError, match=message):
        validate_landclim_raw_receipt(raw_root)


@pytest.mark.parametrize("field", ["dataset_doi", "source_url"])
def test_landclim_receipt_refuses_changed_source_association(
    tmp_path: Path, field: str
) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(_RAW_ROOT, raw_root)
    receipt_path = raw_root / "landclim_sources.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["assets"][0][field] = "not-a-governed-source"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(LandClimRawReceiptError, match="association|source URL"):
        validate_landclim_raw_receipt(raw_root)


def test_landclim_receipt_refuses_changed_archive_member_digest(
    tmp_path: Path,
) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(_RAW_ROOT, raw_root)
    receipt_path = raw_root / "landclim_sources.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["archive_summaries"][0]["member_manifest_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(LandClimRawReceiptError, match="archive member summary"):
        validate_landclim_raw_receipt(raw_root)


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("non_integer_count", "asset_count"),
        ("non_integer_size", "asset size"),
        ("duplicate_archive", "Duplicate LandClim archive"),
        ("duplicate_dataset", "Duplicate LandClim receipt dataset"),
    ),
)
def test_landclim_receipt_refuses_ambiguous_accounting(
    tmp_path: Path, mutation: str, message: str
) -> None:
    raw_root = tmp_path / "raw"
    shutil.copytree(_RAW_ROOT, raw_root)
    receipt_path = raw_root / "landclim_sources.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if mutation == "non_integer_count":
        receipt["asset_count"] = 7.0
    elif mutation == "non_integer_size":
        receipt["assets"][0]["size_bytes"] = float(receipt["assets"][0]["size_bytes"])
    elif mutation == "duplicate_archive":
        receipt["archive_summaries"].append(receipt["archive_summaries"][0])
    else:
        receipt["datasets"].append(receipt["datasets"][0])
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    with pytest.raises(LandClimRawReceiptError, match=message):
        validate_landclim_raw_receipt(raw_root)
