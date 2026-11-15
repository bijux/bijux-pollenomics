from __future__ import annotations

import hashlib
import json

from bijux_pollenomics.collection.sources.landclim import collection
from tests.support.repository import REPOSITORY_ROOT

RAW_ROOT = REPOSITORY_ROOT / "data" / "landclim" / "raw"


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _without_contributor(receipt: dict[str, object], generated_on: str) -> object:
    original = json.loads(json.dumps(receipt))
    original["assets"] = [
        row
        for row in original["assets"]
        if row["filename"] != "landclim_ii_contributors.xlsx"
    ]
    original["asset_count"] = 7
    original["generated_on"] = generated_on
    for dataset in original["datasets"]:
        if dataset["dataset_id"] == "937075":
            dataset["files"].remove("landclim_ii_contributors.xlsx")
    return original


def test_checked_in_receipt_keeps_canonical_identity() -> None:
    receipt = collection.validate_landclim_raw_receipt(RAW_ROOT)

    assert _canonical_digest(receipt) == (
        "d5fa0f35ebf08cc705313413fbd9fc43318e4182543b3c3c3377a15f77b5ebd9"
    )
    assert _canonical_digest(_without_contributor(receipt, "2026-03-31")) == (
        "0e7df7823bf041adfe76518af99c8772796f3e7969b67aab9de3818f5dad03d1"
    )


def test_receipt_builder_keeps_canonical_identity() -> None:
    receipt = collection.validate_landclim_raw_receipt(RAW_ROOT)
    assets = receipt["assets"]
    assert isinstance(assets, list)
    paths = {
        path.name: path
        for path in RAW_ROOT.iterdir()
        if path.is_file() and path.name != "landclim_sources.json"
    }
    urls = {
        str(asset["filename"]): str(asset["source_url"])
        for asset in assets
        if isinstance(asset, dict)
    }

    built = collection._build_landclim_raw_receipt(
        paths,
        urls,
        generated_on="2026-09-05",
    )

    assert _canonical_digest(built) == (
        "839b12ea03d648801da98b2d46bb6feb0e47032db6f6c6d58955d869fd0b4f1e"
    )
    assert _canonical_digest(_without_contributor(built, "2026-09-05")) == (
        "469dfa55548acec2f0ff18a7d538482883d67ddd0f07aef5ec2e331bb28293fe"
    )


def test_unsafe_receipt_filename_keeps_exact_refusal() -> None:
    for value, message in (
        (None, "LandClim raw receipt filename is invalid"),
        ("../asset.csv", "Unsafe LandClim raw receipt filename: ../asset.csv"),
    ):
        try:
            collection._safe_receipt_filename(value)
        except collection.LandClimRawReceiptError as error:
            assert str(error) == message
        else:
            raise AssertionError("unsafe receipt filename was accepted")
