"""The admitted claim consumer can retain original JSON rows without promotion."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadMaterializedAdmissionSnapshot,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.evidence.claims import (
    build_sead_chronology_claim_bundle,
    build_sead_chronology_claim_bundle_from_snapshot,
    write_sead_chronology_claim_bundle,
    write_sead_chronology_claim_bundle_from_snapshot,
)
from bijux_pollenomics.collection.sources.sead.evidence.native_rows import (
    attach_sead_native_source_rows,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_claims import (
    CHRONOLOGY_CLAIM_SPECS,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.models import (
    SeadChronologyClaim,
)


def _tables() -> dict[str, list[dict[str, object]]]:
    tables: dict[str, list[dict[str, object]]] = {
        table: [] for table in SEAD_LINKED_SOURCE_TABLES
    }
    tables.update(
        tbl_sites=[{"site_id": 1, "site_uuid": "site-one"}],
        tbl_sample_groups=[
            {"sample_group_id": 2, "site_id": 1, "sample_group_name": "Group"}
        ],
        tbl_physical_samples=[{"physical_sample_id": 3, "sample_group_id": 2}],
        tbl_analysis_entities=[
            {"analysis_entity_id": 4, "physical_sample_id": 3, "dataset_id": 5}
        ],
        tbl_analysis_values=[{"analysis_value_id": 6, "analysis_entity_id": 4}],
        tbl_datasets=[{"dataset_id": 5, "dataset_name": "Dataset", "biblio_id": None}],
        tbl_age_types=[{"age_type_id": 1, "age_type": "AD", "description": None}],
        tbl_relative_ages=[
            {
                "relative_age_id": 16,
                "relative_age_name": "Period",
                "description": None,
                "abbreviation": None,
                "cal_age_older": None,
                "cal_age_younger": None,
                "c14_age_older": None,
                "c14_age_younger": None,
            }
        ],
    )
    for number, (_, _, primary_key, table) in enumerate(CHRONOLOGY_CLAIM_SPECS, 11):
        tables[table] = [
            {
                **dict.fromkeys(
                    [
                        "age",
                        "chronology_id",
                        "dating_specifier",
                        "age_range",
                        "dating_lab_id",
                        "lab_number",
                        "error_older",
                        "error_younger",
                        "dating_uncertainty_id",
                        "dendro_lookup_id",
                        "season_id",
                        "low_qualifier",
                        "high_qualifier",
                        "method_id",
                    ]
                ),
                primary_key: number,
                "analysis_entity_id": 4,
                "analysis_value_id": 6,
                "relative_age_id": 16,
                "age_type_id": 1,
                "low_value": 1800,
                "high_value": None,
                "age_older": 1845.0,
                "age_younger": None,
                "low_is_uncertain": None,
                "high_is_uncertain": False,
                "notes": "  original\nwhitespace  ",
                "future_field": [None, False, 0, 0.0, "", {"unknown": None}],
            }
        ]
    return tables


def _snapshot(
    tables: dict[str, list[dict[str, object]]],
) -> SeadMaterializedAdmissionSnapshot:
    def encoded(value: object) -> bytes:
        return json.dumps(value, allow_nan=False).encode()

    copied = {
        f"payloads/{table}.json": encoded({"table": table, "rows": rows})
        for table, rows in tables.items()
    }
    copied["manifest.json"] = encoded({"fixture": "captured"})
    copied["country-decisions.json"] = encoded(
        {
            "decisions": [
                {
                    "site_id": 1,
                    "governed_country_code": "SE",
                    "decision": {"decision_method": "source_fixture"},
                }
            ]
        }
    )
    admission = {
        "schema_version": "sead-acquisition-admission.v1",
        "source_family": "sead",
        "run_id": "source-fixture",
        "scope_id": "source-scope",
        "build_id": "source-build",
        "acquisition_manifest_sha256": sha256(copied["manifest.json"]).hexdigest(),
        "acquisition_bundle_sha256": "a" * 64,
        "copied_files": [
            {"path": path, "byte_count": len(body), "sha256": sha256(body).hexdigest()}
            for path, body in copied.items()
        ],
    }
    return SeadMaterializedAdmissionSnapshot(admission, copied)


def _claims(bundle: dict[str, object]) -> list[SeadChronologyClaim]:
    return cast(list[SeadChronologyClaim], bundle["claims"])


def test_native_context_preserves_old_claims_and_json_types() -> None:
    tables = _tables()
    snapshot = _snapshot(tables)
    default = build_sead_chronology_claim_bundle_from_snapshot(snapshot)
    explicit_default = build_sead_chronology_claim_bundle_from_snapshot(
        snapshot, include_native_source_rows=False
    )
    assert json.dumps(default) == json.dumps(explicit_default)
    native = build_sead_chronology_claim_bundle_from_snapshot(
        snapshot, include_native_source_rows=True
    )
    assert len(_claims(native)) == 5
    stripped = deepcopy(native)
    for claim in _claims(stripped):
        del claim["source_native_row"]
    assert stripped == default
    for claim in _claims(native):
        row = claim["source_native_row"]
        assert json.dumps(row) == json.dumps(tables[claim["source_table"]][0])
        assert row["low_is_uncertain"] is None
        assert row["high_is_uncertain"] is False
        assert type(row["low_value"]) is int
        assert type(row["age_older"]) is float
        assert row["notes"] == "  original\nwhitespace  "
        assert claim["propagation_eligibility"] == "refused"
        assert "future_field" not in claim["source_age_value"]
        if claim["claim_type"] == "dating_range":
            assert claim["source_age_value"]["low_is_uncertain"] is False
            assert row["low_is_uncertain"] is None
    # Mutable future source fields belong to this returned packet alone.
    claims = _claims(default)
    attach_sead_native_source_rows(claims, tables)
    cast(list[object], claims[0]["source_native_row"]["future_field"]).append("changed")
    assert (
        len(cast(list[object], tables[claims[0]["source_table"]][0]["future_field"]))
        == 6
    )


def test_file_and_snapshot_writers_keep_default_bytes_and_reopen_native_nulls(
    tmp_path: Path,
) -> None:
    snapshot = _snapshot(_tables())
    for relative, body in snapshot.copied_files.items():
        path = tmp_path / "admitted" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    (tmp_path / "admitted/admission.json").write_text(
        json.dumps(dict(snapshot.admission))
    )
    default = write_sead_chronology_claim_bundle(
        tmp_path / "admitted", tmp_path / "default.json"
    )
    snapshot_default = write_sead_chronology_claim_bundle_from_snapshot(
        snapshot, tmp_path / "snapshot-default.json"
    )
    assert default.read_bytes() == snapshot_default.read_bytes()
    native = write_sead_chronology_claim_bundle(
        tmp_path / "admitted", tmp_path / "native.json", include_native_source_rows=True
    )
    snapshot_native = write_sead_chronology_claim_bundle_from_snapshot(
        snapshot, tmp_path / "snapshot-native.json", include_native_source_rows=True
    )
    assert native.read_bytes() == snapshot_native.read_bytes()
    assert build_sead_chronology_claim_bundle(tmp_path / "admitted") == json.loads(
        default.read_text()
    )
    assert all(
        row["source_native_row"]["low_is_uncertain"] is None
        for row in json.loads(native.read_text())["claims"]
    )

    (tmp_path / "admitted/payloads/tbl_analysis_dating_ranges.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="SEAD admitted byte count changed"):
        build_sead_chronology_claim_bundle(
            tmp_path / "admitted", include_native_source_rows=True
        )


def test_default_does_not_apply_optional_native_key_restrictions() -> None:
    tables = _tables()
    tables["tbl_analysis_dating_ranges"][0]["analysis_dating_range_id"] = "11"
    snapshot = _snapshot(tables)
    assert len(_claims(build_sead_chronology_claim_bundle_from_snapshot(snapshot))) == 5
    with pytest.raises(ValueError, match="native primary key is invalid"):
        build_sead_chronology_claim_bundle_from_snapshot(
            snapshot, include_native_source_rows=True
        )


@pytest.mark.parametrize("invalid", [None, True, "11", 11.0, -1])
def test_noninteger_or_missing_native_keys_are_refused(invalid: object) -> None:
    tables = _tables()
    claims = _claims(
        build_sead_chronology_claim_bundle_from_snapshot(_snapshot(tables))
    )
    tables["tbl_analysis_dating_ranges"][0]["analysis_dating_range_id"] = invalid
    with pytest.raises(ValueError, match="primary key is invalid"):
        attach_sead_native_source_rows(claims, tables)
    assert all("source_native_row" not in claim for claim in claims)


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_row",
        "duplicate_key",
        "unused_row",
        "duplicate_claim",
        "missing_table",
        "wrong_kind",
        "wrong_native_id",
        "padded_claim_id",
    ],
)
def test_ambiguous_or_incomplete_ownership_refuses_instead_of_selecting(
    corruption: str,
) -> None:
    tables = _tables()
    claims = _claims(
        build_sead_chronology_claim_bundle_from_snapshot(_snapshot(tables))
    )
    source = tables["tbl_analysis_dating_ranges"]
    if corruption == "missing_row":
        source.clear()
    elif corruption == "duplicate_key":
        source.append(deepcopy(source[0]))
    elif corruption == "unused_row":
        source.append({**source[0], "analysis_dating_range_id": 99})
    elif corruption == "duplicate_claim":
        claims.append(deepcopy(claims[0]))
    elif corruption == "missing_table":
        del tables["tbl_geochronology"]
    elif corruption == "wrong_kind":
        claims[0]["claim_type"] = "geochronology"
    elif corruption == "wrong_native_id":
        claims[0]["source_native_record_id"] = "99"
    else:
        claims[0]["source_record_id"] = claims[0]["source_native_record_id"] = "011"
    with pytest.raises(ValueError, match="SEAD"):
        attach_sead_native_source_rows(claims, tables)
    assert all("source_native_row" not in claim for claim in claims)
