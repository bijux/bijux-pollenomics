"""Historical retrieval must bind corrected sites to the original admission."""

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion import sead_country_retrieval as owner


def test_corrected_site_lineage_refuses_wrong_site_or_authority() -> None:
    site_bytes = b"corrected site rows"
    site_digest = hashlib.sha256(site_bytes).hexdigest()
    admission = {
        "run_id": owner.RUN,
        "build_id": "build",
        "acquisition_manifest_sha256": "manifest",
        "parent_admission_sha256": "parent",
        "acquisition_bundle_sha256": "bundle",
    }
    lineage: dict[str, Any] = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": admission["run_id"],
        **{key: value for key, value in admission.items() if key != "run_id"},
        "country_membership": {
            "purpose": "historical_admission_cohort",
            "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
            "artifact_digest": "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
        },
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.csv": site_digest
        },
        "refresh_input_sha256": {
            "boundary/normalized/nordic_country_boundaries.geojson": "bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
            "evidence/evidence_materialization_manifest.json": "383151443d04da5a6e127ea2e4344b4b10bb210137dd1d13b77e50dbfae93508",
        },
    }
    encoded = json.dumps(lineage).encode()
    owner.validate_historical_site_lineage(encoded, admission, site_digest)
    with pytest.raises(ValueError, match="site"):
        owner.validate_historical_site_lineage(encoded, admission, "0" * 64)
    lineage["country_membership"]["authority_id"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="authority"):
        owner.validate_historical_site_lineage(
            json.dumps(lineage).encode(), admission, site_digest
        )
    lineage["country_membership"]["authority_id"] = owner.HISTORICAL_COUNTRY_MEMBERSHIP[
        "authority_id"
    ]
    lineage["refresh_input_sha256"][
        "boundary/normalized/nordic_country_boundaries.geojson"
    ] = "0" * 64
    with pytest.raises(ValueError, match="refresh input"):
        owner.validate_historical_site_lineage(
            json.dumps(lineage).encode(), admission, site_digest
        )
    lineage["refresh_input_sha256"][
        "boundary/normalized/nordic_country_boundaries.geojson"
    ] = "bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f"
    lineage["parent_admission_sha256"] = "different"
    with pytest.raises(ValueError, match="admission identity"):
        owner.validate_historical_site_lineage(
            json.dumps(lineage).encode(), admission, site_digest
        )


def test_explicit_historical_ledger_requires_original_bytes(tmp_path: Path) -> None:
    ledger = tmp_path / "untrusted.json"
    ledger.write_bytes(b"{}")
    with pytest.raises(ValueError, match="Historical review ledger"):
        owner.build(
            tmp_path,
            tmp_path / "out",
            historical_review_ledger=ledger,
            historical_site_sha256="0" * 64,
            historical_lineage_sha256="0" * 64,
        )
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    "options",
    [
        {"historical_site_sha256": "0" * 64},
        {"historical_lineage_sha256": "0" * 64},
        {"historical_review_ledger": Path("old.json")},
    ],
)
def test_historical_mode_requires_all_explicit_inputs(
    tmp_path: Path, options: dict[str, Any]
) -> None:
    with pytest.raises(ValueError, match="must be supplied together"):
        owner.build(tmp_path, tmp_path / "out", **options)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("site_id", [3447, 3457, 3528, 3652])
def test_historical_reconciliation_refuses_excluded_sites(
    site_id: int, synthetic_historical_sead_review: dict[str, Any]
) -> None:
    root = Path(__file__).resolve().parents[4]
    raw = root / owner.RAW
    decisions = json.loads((raw / "country-decisions.json").read_bytes())
    boundary = synthetic_historical_sead_review
    receipt = json.loads((raw / "receipts/tbl_sites.json").read_bytes())
    payload = json.loads((raw / "payloads/tbl_sites.json").read_bytes())
    with (root / owner.PUBLIC).open(encoding="utf-8", newline="") as handle:
        sites = list(csv.DictReader(handle))
    countries = json.loads((raw / "reconciliation/countries.json").read_bytes())
    _, records = owner.reconcile(
        decisions, boundary, receipt, payload, sites, countries
    )
    excluded = next(row for row in records if row["site_id"] == site_id)
    assert excluded["country_decision_status"] == "unassigned"
    assert excluded["normalized_consumer"] == "false"
    tampered = deepcopy(payload)
    tampered["rows"][0]["site_id"] = site_id
    with pytest.raises(ValueError, match="Excluded coordinates entered retrieval"):
        owner.reconcile(decisions, boundary, receipt, tampered, sites, countries)
