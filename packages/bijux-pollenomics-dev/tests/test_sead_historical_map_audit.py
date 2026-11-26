"""Synthetic discriminators for historical SEAD map correspondence."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion import sead_map_candidate as owner


def sample() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "record_id": "1",
            "site_uuid": "uuid-1",
            "country": "Sweden",
            "time_start_bp": 0,
            "time_end_bp": 0,
        },
        {
            "record_id": "2",
            "site_uuid": "uuid-2",
            "country": "Finland",
            "time_start_bp": 10,
            "time_end_bp": 20,
        },
        {
            "record_id": "3",
            "site_uuid": "uuid-3",
            "country": "Norway",
            "time_start_bp": None,
            "time_end_bp": None,
        },
        {
            "record_id": "4",
            "site_uuid": "uuid-4",
            "country": "Denmark",
            "time_start_bp": None,
            "time_end_bp": None,
        },
    ]
    source = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": row} for row in rows],
    }
    features = [{**row, "record_id": "sead:site:" + row["record_id"]} for row in rows]
    report = {"denominators": {"exported_sites": 4, "sites_with_display_envelope": 2}}
    return source, features, report


def test_v2_site_projection_accepts_exact_correspondence_and_zero() -> None:
    source, features, report = sample()
    assert owner.validate_historical_site_projection(source, features, report) == 2


@pytest.mark.parametrize("untimed", [1219, 1222])
def test_site_projection_accepts_both_versioned_denominators(untimed: int) -> None:
    rows: list[dict[str, Any]] = [
        {
            "record_id": str(i),
            "site_uuid": f"uuid-{i}",
            "country": "Sweden",
            "time_start_bp": None if i < untimed else 0,
            "time_end_bp": None if i < untimed else 0,
        }
        for i in range(2069)
    ]
    source = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": row} for row in rows],
    }
    features = [{**row, "record_id": "sead:site:" + row["record_id"]} for row in rows]
    intervals = {
        "denominators": {
            "exported_sites": 2069,
            "sites_with_display_envelope": 2069 - untimed,
        }
    }
    assert (
        owner.validate_historical_site_projection(source, features, intervals)
        == untimed
    )


@pytest.mark.parametrize(
    "kind", ["same_count_swap", "partial", "duplicate", "missing", "uuid", "count"]
)
def test_v2_site_projection_rejects_mismatches(kind: str) -> None:
    source, features, report = sample()
    if kind == "same_count_swap":
        features[0]["time_start_bp"], features[1]["time_start_bp"] = (
            features[1]["time_start_bp"],
            features[0]["time_start_bp"],
        )
        features[0]["time_end_bp"], features[1]["time_end_bp"] = (
            features[1]["time_end_bp"],
            features[0]["time_end_bp"],
        )
    elif kind == "partial":
        features[2]["time_start_bp"] = 5
    elif kind == "duplicate":
        features[0]["record_id"] = features[1]["record_id"]
    elif kind == "missing":
        features.pop()
    elif kind == "uuid":
        features[0]["site_uuid"] = "other"
    else:
        report["denominators"]["sites_with_display_envelope"] = 3
    with pytest.raises(ValueError, match="SEAD historical"):
        owner.validate_historical_site_projection(source, features, report)


def test_v2_historical_inputs_bind_source_interval_and_custody() -> None:
    source, _, _ = sample()
    source_bytes = json.dumps(source).encode()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    lineage: dict[str, Any] = {
        "schema_version": "sead-normalized-surface-lineage.v2",
        "source_run_id": "sead-full-evidence-39bfff6a-ce80714e",
        "build_id": "sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725",
        "acquisition_manifest_sha256": "6fc2428046d148f9ce6c158f982afbbbbaea39de2132850a4fb8f41acf8a4c14",
        "parent_admission_sha256": "168ad1efe6fa68cdb7789246a6cce16670377cdbacd14d1673beaab8ddd1ebd1",
        "acquisition_bundle_sha256": "sha256:fdcda26e7de9a09383b0d9aae7ab7f9e8846c7cbf05513da17fdb8e329331ba9",
        "country_membership": {
            "purpose": "historical_admission_cohort",
            "authority_id": "sha256:e67d7e498df146bcdd65c398f67cdf2372298258288bcba9af734486fa2fe8d0",
            "artifact_digest": "sha256:bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
        },
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.geojson": source_sha
        },
        "refresh_input_sha256": {
            "boundary/normalized/nordic_country_boundaries.geojson": "bc248e555d39828187df43e27f6150c73bcbd209ce43cb3e41be2c914510b32f",
            "evidence/evidence_materialization_manifest.json": "383151443d04da5a6e127ea2e4344b4b10bb210137dd1d13b77e50dbfae93508",
        },
    }
    lineage_bytes = json.dumps(lineage).encode()
    lineage_sha = hashlib.sha256(lineage_bytes).hexdigest()
    intervals: dict[str, Any] = {
        "schema_version": "sead-interval-set-review.v1",
        "source_run_id": lineage["source_run_id"],
        "source_build_id": lineage["build_id"],
        "analytic_posture": {
            "record_intervals_are_distinct": True,
            "site_display_envelope_is_analytic_interval": False,
            "qualified_or_contextual_claims_admitted": False,
            "event_propagation_approved": False,
        },
        "input_hashes": {
            "site_geojson_sha256": source_sha,
            "claim_index_sha256": "b9accf421059eebf95b75a8c22fd237f4d51991fbc868e79530d20a694e6cd21",
        },
    }
    custody: dict[str, Any] = {
        "schema_version": "sead-public-source-custody.v1",
        "source_run_id": lineage["source_run_id"],
        "raw_and_public_site_count": 4,
        "excluded_decision_count": 126,
        "excluded_status_counts": {"review": 103, "unassigned": 23},
        "inputs_sha256": {
            "data/sead/normalized/nordic_environmental_sites.geojson": source_sha,
            "data/sead/normalized/source_lineage.json": lineage_sha,
        },
    }
    custody["inputs_sha256"][
        "docs/report/regions/nordic/nordic_environmental_sites.geojson"
    ] = source_sha
    custody["acquisition_bundle_sha256"] = lineage["acquisition_bundle_sha256"]
    interval_bytes, custody_bytes = (
        json.dumps(intervals).encode(),
        json.dumps(custody).encode(),
    )
    pins = cast(
        tuple[str, str, str, str],
        tuple(
            hashlib.sha256(b).hexdigest()
            for b in (source_bytes, lineage_bytes, interval_bytes, custody_bytes)
        ),
    )
    owner.validate_historical_input_bindings(
        source_bytes, lineage_bytes, interval_bytes, custody_bytes, pins, 4
    )
    for kind in ("interval", "lineage", "custody", "pin"):
        mutated = [source_bytes, lineage_bytes, interval_bytes, custody_bytes]
        current_pins = list(pins)
        if kind == "interval":
            interval_changed = deepcopy(intervals)
            interval_changed["input_hashes"]["site_geojson_sha256"] = "0" * 64
            mutated[2] = json.dumps(interval_changed).encode()
            current_pins[2] = hashlib.sha256(mutated[2]).hexdigest()
        elif kind == "lineage":
            lineage_changed = deepcopy(lineage)
            lineage_changed["country_membership"]["authority_id"] = "sha256:" + "0" * 64
            mutated[1] = json.dumps(lineage_changed).encode()
            current_pins[1] = hashlib.sha256(mutated[1]).hexdigest()
        elif kind == "custody":
            custody_changed = deepcopy(custody)
            custody_changed["excluded_decision_count"] = 125
            mutated[3] = json.dumps(custody_changed).encode()
            current_pins[3] = hashlib.sha256(mutated[3]).hexdigest()
        else:
            current_pins[0] = "0" * 64
        with pytest.raises(ValueError, match="SEAD historical"):
            owner.validate_historical_input_bindings(
                mutated[0],
                mutated[1],
                mutated[2],
                mutated[3],
                cast(tuple[str, str, str, str], tuple(current_pins)),
                4,
            )


def test_v2_audit_requires_all_source_pins(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="supplied together"):
        owner.audit(tmp_path, tmp_path, tmp_path, historical_site_sha256="0" * 64)


def test_v2_cli_refuses_default_public_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "audit",
            "--repository",
            str(tmp_path),
            "--candidate",
            str(tmp_path),
            "--browser-receipt",
            str(tmp_path / "browser.json"),
            "--historical-site-sha256",
            "0" * 64,
        ],
    )
    with pytest.raises(ValueError, match="artifact output"):
        owner.main()


def test_v2_browser_binding_rejects_unbound_and_mismatched_receipts(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "index.html").write_text(
        '<script id="atlas-static-bootstrap" type="application/json">{"build_id":"candidate"}</script>'
    )
    (candidate / "x.atlas-nodes.js").write_text("nodes")
    (candidate / "x.atlas-details.js").write_text("details")
    records = [
        {"record_id": f"record-{i}", "chronology": {"records": [{}]}} for i in range(8)
    ]
    generation = {
        "candidate_build_id": "candidate",
        "source_atlas_build_id": "source",
        "source_records": records,
    }
    generation_bytes = json.dumps(generation).encode()
    served = {
        name: hashlib.sha256((candidate / name).read_bytes()).hexdigest()
        for name in ("index.html", "x.atlas-nodes.js", "x.atlas-details.js")
    }
    receipt: dict[str, Any] = {
        "schema_version": "atlas-nordic-source-browser-verification.v2",
        "candidate_generation_sha256": hashlib.sha256(generation_bytes).hexdigest(),
        "candidate_build_id": "candidate",
        "source_atlas_build_id": "source",
        "status": "PASS",
        "runtime_errors": [],
        "served_files_sha256": served,
        "chronology_tables": [
            {
                "width": width,
                "record_id": record["record_id"],
                "rows": 1,
                "all_source_cells_equal": True,
            }
            for width in (390, 1440)
            for record in records
        ],
    }
    owner.validate_historical_browser_binding(candidate, generation_bytes, receipt)
    for kind in ("legacy", "generation", "served", "duplicate", "cells"):
        changed = deepcopy(receipt)
        if kind == "legacy":
            changed["schema_version"] = "atlas-nordic-source-browser-verification.v1"
        elif kind == "generation":
            changed["candidate_generation_sha256"] = "0" * 64
        elif kind == "served":
            changed["served_files_sha256"]["index.html"] = "0" * 64
        elif kind == "duplicate":
            changed["chronology_tables"][0] = deepcopy(changed["chronology_tables"][1])
        else:
            changed["chronology_tables"][0]["all_source_cells_equal"] = False
        with pytest.raises(ValueError, match="SEAD historical browser"):
            owner.validate_historical_browser_binding(
                candidate, generation_bytes, changed
            )
