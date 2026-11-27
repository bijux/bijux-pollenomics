"""An explicit overlay may reconcile a narrowly witnessed status correction."""

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
    reconcile_chronology_rows,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
    apply_overlay,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.sead.models import (
    ClaimIndex,
)


def rows() -> tuple[dict[str, Any], dict[str, Any]]:
    original: dict[str, Any] = {
        "chronology_claim_id": "claim:a",
        "claim_type": "relative_period",
        "comparability_status": "context_only",
        "source_site_id": "4570",
        "chronology_eligibility": "refused",
        "observation_link_status": "linked",
        "source_age_value": {
            "relative_age_label": "CAL_1175_AD-",
            "uncertainty_label": "From",
            "interval_source": "relative_age_bounds",
            "time_start_bp": 775,
            "time_end_bp": 775,
        },
        "original_interval_orientation": "point",
    }
    revised = deepcopy(original)
    revised["source_age_value"].update(
        interval_source="unresolved", time_start_bp=None, time_end_bp=None
    )
    revised["original_interval_orientation"] = "unavailable"
    return original, revised


def test_opt_in_version_reconciles_only_witnessed_relative_status() -> None:
    old, new = rows()
    with pytest.raises(ValueError, match="nonderived"):
        reconcile_chronology_rows([old], [new], expected_count=1)
    result = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    assert result == [
        {
            "chronology_claim_id": "claim:a",
            "time_start_bp": None,
            "time_end_bp": None,
            "original_interval_orientation": "unavailable",
            "interval_source": "unresolved",
        }
    ]
    assert old["source_age_value"]["interval_source"] == "relative_age_bounds"


@pytest.mark.parametrize(
    "corruption",
    [
        "family",
        "label",
        "qualifier",
        "previous_source",
        "new_source",
        "bounds",
        "orientation",
        "other_field",
        "type",
    ],
)
def test_opt_in_refuses_unwitnessed_or_extra_source_changes(corruption: str) -> None:
    old, new = rows()
    if corruption == "family":
        old["claim_type"] = new["claim_type"] = "geochronology"
    elif corruption == "label":
        old["source_age_value"]["relative_age_label"] = new["source_age_value"][
            "relative_age_label"
        ] = "CAL_1175_AD"
    elif corruption == "qualifier":
        old["source_age_value"]["uncertainty_label"] = new["source_age_value"][
            "uncertainty_label"
        ] = "Ca."
    elif corruption == "previous_source":
        old["source_age_value"]["interval_source"] = "encoded_relative_age_label"
    elif corruption == "new_source":
        new["source_age_value"]["interval_source"] = "other"
    elif corruption == "bounds":
        new["source_age_value"]["time_start_bp"] = 0
    elif corruption == "orientation":
        new["original_interval_orientation"] = "point"
    elif corruption == "other_field":
        new["chronology_eligibility"] = "eligible"
    else:
        old["source_age_value"]["time_start_bp"] = True
    with pytest.raises(ValueError):
        reconcile_chronology_rows(
            [old], [new], expected_count=1, allow_marked_relative_source=True
        )


def test_apply_copies_status_only_with_explicit_version_and_valid_original() -> None:
    old, new = rows()
    before = deepcopy(old)
    patch = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    index = ClaimIndex(
        rows=[old], by_site={"4570": [old]}, country_counts=Counter({"SE": 1})
    )
    overlay = {
        "schema_version": "sead-historical-derived-chronology-overlay.v2",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["claim:a"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": patch,
    }
    with pytest.raises(ValueError):
        apply_overlay(index, overlay)
    result = apply_overlay(index, overlay, allow_marked_relative_source=True)
    assert (
        old == before and result.rows[0]["source_age_value"] == new["source_age_value"]
    )
    assert (
        result.rows[0]["observation_link_status"] == "linked"
        and result.rows[0]["chronology_eligibility"] == "refused"
    )


@pytest.mark.parametrize(
    "schema, opt_in",
    [
        ("sead-historical-derived-chronology-overlay.v1", True),
        ("sead-historical-derived-chronology-overlay.v2", False),
        ("other", True),
        (1, True),
    ],
)
def test_apply_rejects_schema_downgrade_or_mismatch(
    schema: object, opt_in: bool
) -> None:
    old, new = rows()
    patch = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    index = ClaimIndex(
        rows=[old], by_site={"4570": [old]}, country_counts=Counter({"SE": 1})
    )
    overlay = {
        "schema_version": schema,
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["claim:a"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": patch,
    }
    with pytest.raises(ValueError, match="schema"):
        apply_overlay(index, overlay, allow_marked_relative_source=opt_in)


def test_apply_versioned_overlay_refuses_omitted_marked_status() -> None:
    old, new = rows()
    patch = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    del patch[0]["interval_source"]
    index = ClaimIndex(
        rows=[old], by_site={"4570": [old]}, country_counts=Counter({"SE": 1})
    )
    overlay = {
        "schema_version": "sead-historical-derived-chronology-overlay.v2",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["claim:a"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": patch,
    }
    with pytest.raises(ValueError, match="change missing"):
        apply_overlay(index, overlay, allow_marked_relative_source=True)


def test_marked_source_with_unwitnessed_old_range_refuses() -> None:
    old, new = rows()
    old["source_age_value"]["time_start_bp"] = 700
    old["original_interval_orientation"] = "younger_to_older"
    with pytest.raises(ValueError, match="transition"):
        reconcile_chronology_rows(
            [old], [new], expected_count=1, allow_marked_relative_source=True
        )


def test_versioned_overlay_refuses_missing_witnessed_change() -> None:
    old, _ = rows()
    index = ClaimIndex(
        rows=[old], by_site={"4570": [old]}, country_counts=Counter({"SE": 1})
    )
    overlay = {
        "schema_version": "sead-historical-derived-chronology-overlay.v2",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["claim:a"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 0,
        "changes": [],
    }
    with pytest.raises(ValueError, match="change missing"):
        apply_overlay(index, overlay, allow_marked_relative_source=True)


def test_versioned_apply_refuses_substituted_original_source() -> None:
    old, new = rows()
    patch = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    old["source_age_value"]["uncertainty_label"] = "Ca."
    index = ClaimIndex(
        rows=[old], by_site={"4570": [old]}, country_counts=Counter({"SE": 1})
    )
    overlay = {
        "schema_version": "sead-historical-derived-chronology-overlay.v2",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(
            json.dumps(["claim:a"], separators=(",", ":")).encode()
        ).hexdigest(),
        "changed_claim_count": 1,
        "changes": patch,
    }
    with pytest.raises(ValueError, match="transition"):
        apply_overlay(index, overlay, allow_marked_relative_source=True)


def test_versioned_overlay_survives_real_compact_claim_encoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence.chronology_overlay import (
        _canonical,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead_claims import (
        _sead_claim_table,
    )
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )
    from tests.unit.reporting.map_document.evidence_projection.fixtures.common import (
        _decode_sead_claim_table,
    )

    install_sead_projection_fixture(tmp_path, monkeypatch)
    records, _ = projection._project_sead(tmp_path, sead_projection_layers()[1:])
    site = cast(
        dict[str, Any], next(r for r in records if r["record_id"] == "sead:site:2")
    )
    old = cast(dict[str, Any], _decode_sead_claim_table(site["tabs"]["chronology"])[0])
    old["claim_type"] = "relative_period"
    old["comparability_status"] = "context_only"
    old["source_age_value"].update(
        relative_age_label="CAL_1175_AD-",
        uncertainty_label="From",
        interval_source="relative_age_bounds",
        time_start_bp=775,
        time_end_bp=775,
    )
    old["original_interval_orientation"] = "point"
    new = deepcopy(old)
    new["source_age_value"].update(
        interval_source="unresolved", time_start_bp=None, time_end_bp=None
    )
    new["original_interval_orientation"] = "unavailable"
    changes = reconcile_chronology_rows(
        [old], [new], expected_count=1, allow_marked_relative_source=True
    )
    claim_id = old["chronology_claim_id"]
    overlay = {
        "schema_version": "sead-historical-derived-chronology-overlay.v2",
        "claim_count": 1,
        "claim_id_set_sha256": hashlib.sha256(_canonical([claim_id])).hexdigest(),
        "changed_claim_count": 1,
        "changes": changes,
    }
    index = ClaimIndex(
        rows=[old],
        by_site={old["source_site_id"]: [old]},
        country_counts=Counter({"DK": 1}),
    )
    result = apply_overlay(index, overlay, allow_marked_relative_source=True)
    decoded = _decode_sead_claim_table(_sead_claim_table(result.rows))
    assert _canonical(decoded) == _canonical([new])


def test_versioned_overlay_reaches_projected_claim_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.sead.evidence import (
        chronology_overlay as owner,
    )
    from bijux_pollenomics.reporting.context.points.external import (
        build_external_point_layer,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        build_map_evidence_projection,
        service,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection import (
        sead as projection,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead import (
        projection as stage,
    )
    from bijux_pollenomics.reporting.map_document.evidence_projection.sead.chronology_overlay import (
        HistoricalChronologyRequest,
    )
    from tests.support.sead_evidence import (
        install_sead_projection_fixture,
        sead_projection_layers,
    )
    from tests.unit.reporting.map_document.evidence_projection.fixtures.common import (
        _decode_sead_claim_table,
    )

    install_sead_projection_fixture(tmp_path, monkeypatch)
    for name in (
        "SEAD_GOVERNED_EVIDENCE_RUN_ID",
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        "SEAD_GOVERNED_ADMISSION_SHA256",
    ):
        monkeypatch.setattr(service, name, vars(projection)[name])
    site = tmp_path / "sead/normalized/nordic_environmental_sites.geojson"
    lineage = {
        "normalized_surface_sha256": {
            "normalized/nordic_environmental_sites.geojson": hashlib.sha256(
                site.read_bytes()
            ).hexdigest()
        }
    }
    lineage_bytes = json.dumps(lineage).encode()
    (site.parent / "source_lineage.json").write_bytes(lineage_bytes)
    pin = hashlib.sha256(lineage_bytes).hexdigest()
    observed: list[dict[str, Any]] = []
    real_index = cast(Any, stage).index_claims

    def synthetic_index(bundle: Any) -> ClaimIndex:
        index = real_index(bundle)
        row: dict[str, Any] = deepcopy(dict(index.rows[0]))
        row["claim_type"] = "relative_period"
        row["comparability_status"] = "context_only"
        row["source_age_value"].update(
            relative_age_label="CAL_1175_AD-",
            uncertainty_label="From",
            interval_source="relative_age_bounds",
            time_start_bp=775,
            time_end_bp=775,
        )
        row["original_interval_orientation"] = "point"
        observed.append(row)
        return ClaimIndex(
            rows=[row],
            by_site={row["source_site_id"]: [row]},
            country_counts=index.country_counts,
        )

    monkeypatch.setattr(stage, "index_claims", synthetic_index)

    def synthetic_owner(*args: Any, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["allow_marked_relative_source"] is True
        old = observed[-1]
        new = deepcopy(old)
        new["source_age_value"].update(
            interval_source="unresolved", time_start_bp=None, time_end_bp=None
        )
        new["original_interval_orientation"] = "unavailable"
        changes = reconcile_chronology_rows(
            [old], [new], expected_count=1, allow_marked_relative_source=True
        )
        return {
            "schema_version": "sead-historical-derived-chronology-overlay.v2",
            "source_run_id": vars(projection)["SEAD_GOVERNED_EVIDENCE_RUN_ID"],
            "admission_sha256": vars(projection)["SEAD_GOVERNED_ADMISSION_SHA256"],
            "evidence_manifest_sha256": vars(projection)[
                "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256"
            ],
            "lineage_sha256": pin,
            "claim_count": 1,
            "claim_id_set_sha256": hashlib.sha256(
                json.dumps([old["chronology_claim_id"]], separators=(",", ":")).encode()
            ).hexdigest(),
            "changed_claim_count": 1,
            "changes": changes,
        }

    monkeypatch.setattr(owner, "build_historical_chronology_overlay", synthetic_owner)
    selected = sead_projection_layers()[1:]
    selected[0] = build_external_point_layer(
        json.loads(site.read_bytes()), source_path=site
    )
    result = build_map_evidence_projection(
        tmp_path,
        selected,
        historical_chronology=HistoricalChronologyRequest(
            tmp_path, pin, allow_marked_relative_source=True
        ),
    )
    row = cast(
        dict[str, Any],
        next(r for r in result.detail_records if r["record_id"] == "sead:site:2"),
    )
    decoded = cast(
        dict[str, Any], _decode_sead_claim_table(row["tabs"]["chronology"])[0]
    )
    assert decoded["source_age_value"]["interval_source"] == "unresolved"
    assert (
        decoded["source_age_value"]["time_start_bp"] is None
        and decoded["source_age_value"]["time_end_bp"] is None
    )
    assert decoded["chronology_eligibility"] == observed[-1]["chronology_eligibility"]
    assert decoded["observation_link_status"] == observed[-1]["observation_link_status"]
    assert (
        row["tabs"]["provenance"]["derived_chronology"]["schema_version"]
        == "sead-atlas-derived-chronology.v2"
    )


def test_versioned_reconciliation_refuses_unchanged_witnessed_status() -> None:
    old, _ = rows()
    with pytest.raises(ValueError, match="change missing"):
        reconcile_chronology_rows(
            [old], [deepcopy(old)], expected_count=1, allow_marked_relative_source=True
        )
