"""Tests for source-separated archaeological site coordinate evidence."""

from __future__ import annotations

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_project_sample_chronology_rows,
)
from bijux_pollenomics.adna.projects.evidence.coordinates import (
    resolve_project_coordinate_provenance,
)
from bijux_pollenomics.adna.projects.evidence.sites import (
    resolve_project_site_evidence,
)
from bijux_pollenomics.adna.projects.registry.localities import (
    resolve_project_locality_leads,
)
from bijux_pollenomics.adna.projects.registry.samples import (
    _matching_locality_lead,
    build_species_curated_sample_rows,
)
from bijux_pollenomics.adna.projects.registry.sites.assembly import (
    _matching_locality_row,
)
from bijux_pollenomics.adna.projects.sample_master.tables.pig_panel import (
    PIG_SITE_COORDINATE_EVIDENCE_PATH,
    build_pig_panel_join_audit,
    load_pig_site_coordinate_evidence,
)

from .support import (
    ARCHIVE_SOURCE_PATH,
    DATA_ROOT,
    WORKBOOK_SOURCE_PATH,
    governed_inputs,
)


def test_pig_coordinate_evidence_preserves_site_level_uncertainty() -> None:
    records = load_pig_site_coordinate_evidence(DATA_ROOT)

    assert [record.sample_label for record in records] == ["AA015", "AA016"]
    assert [record.archive_native_sample_id for record in records] == [
        "SAMEA5160867",
        "SAMEA5160868",
    ]
    assert all(record.coordinate_basis == "named_site_geocoding" for record in records)
    assert all(record.coordinate_confidence == "approximate" for record in records)
    assert all("not_specimen_findspot" in record.spatial_scope for record in records)


def test_join_audit_admits_coordinates_only_for_the_two_evidence_records() -> None:
    rows, archive_text = governed_inputs()
    audit = build_pig_panel_join_audit(
        source_path=WORKBOOK_SOURCE_PATH,
        rows=rows,
        archive_source_path=ARCHIVE_SOURCE_PATH,
        archive_text=archive_text,
        coordinate_evidence=load_pig_site_coordinate_evidence(DATA_ROOT),
    )
    mapped = {row.sample_label: row for row in audit if row.latitude_text}

    assert set(mapped) == {"AA015", "AA016"}
    assert all(
        row.map_admission == "admitted_approximate_site_anchor"
        for row in mapped.values()
    )
    assert all(row.coordinate_confidence == "approximate" for row in mapped.values())
    assert all(
        "not_specimen_findspot" in row.coordinate_spatial_scope
        for row in mapped.values()
    )
    assert all(
        row.map_admission == "refused_missing_source_coordinates"
        for row in audit
        if row.sample_label not in mapped
    )


def test_pig_coordinate_provenance_separates_sample_and_coordinate_sources() -> None:
    rows = resolve_project_coordinate_provenance("PRJEB30282")
    by_site = {row.site_label: row for row in rows}

    assert set(by_site) == {"Bundsø", "Trelleborg"}
    assert by_site["Bundsø"].source_artifact_path == PIG_SITE_COORDINATE_EVIDENCE_PATH
    assert "systemnr 86607" in by_site["Bundsø"].source_locator
    assert by_site["Bundsø"].geocoder_or_gazetteer.startswith(
        "https://www.kulturarv.dk/ffpublic/wfs"
    )
    assert "central point" in by_site["Trelleborg"].source_locator
    assert by_site["Trelleborg"].geocoder_or_gazetteer.endswith(
        "ManagementPlan_Web_lille.pdf"
    )
    assert all(row.mapping_posture == "mappable_point" for row in rows)
    assert all(row.coordinate_confidence == "approximate" for row in rows)
    assert all("not a specimen findspot" in row.interpretation_note for row in rows)
    assert {
        site: (row.time_start_bp, row.time_end_bp, row.dating_basis)
        for site, row in by_site.items()
    } == {
        "Bundsø": (4700, 4700, "archaeological_context"),
        "Trelleborg": (1000, 1000, "archaeological_context"),
    }


def test_pig_site_rows_and_locality_leads_keep_coordinates_per_site() -> None:
    site_rows = resolve_project_site_evidence("PRJEB30282")
    direct_rows = {
        row.site_label: row
        for row in site_rows
        if row.site_label in {"Bundsø", "Trelleborg"}
    }
    assert {
        row.site_label: (
            row.latitude_text,
            row.longitude_text,
            row.coordinate_basis,
            row.time_start_bp,
            row.time_end_bp,
            row.dating_basis,
        )
        for row in direct_rows.values()
    } == {
        "Bundsø": (
            "55.02158609",
            "9.77344984",
            "named_site_geocoding",
            4700,
            4700,
            "archaeological_context",
        ),
        "Trelleborg": (
            "55.39416667",
            "11.26527778",
            "named_site_geocoding",
            1000,
            1000,
            "archaeological_context",
        ),
    }
    context_row = next(row for row in site_rows if row.site_label not in direct_rows)
    assert context_row.site_label == "Near East and Europe pig domestication transect"
    assert context_row.coordinate_basis == "inferred_region_centroid"

    leads = resolve_project_locality_leads("PRJEB30282")
    assert {
        lead.locality_text: (lead.latitude_text, lead.longitude_text) for lead in leads
    } == {
        "Bundsø": ("55.02158609", "9.77344984"),
        "Trelleborg": ("55.39416667", "11.26527778"),
    }


def test_only_archive_proven_domestic_samples_gain_site_coordinates() -> None:
    rows = build_species_curated_sample_rows("Sus scrofa domesticus")
    mapped = {
        row.archive_native_sample_id: (
            row.site_label,
            row.latitude_text,
            row.longitude_text,
            row.coordinate_basis,
            row.dating_basis,
        )
        for row in rows
        if row.latitude_text or row.longitude_text
    }

    assert mapped == {
        "SAMEA5160867": (
            "Bundsø",
            "55.02158609",
            "9.77344984",
            "named_site_geocoding",
            "archaeological_context",
        ),
        "SAMEA5160868": (
            "Trelleborg",
            "55.39416667",
            "11.26527778",
            "named_site_geocoding",
            "archaeological_context",
        ),
    }
    archive_only = [
        row
        for row in rows
        if row.project_accession == "PRJEB30282" and not row.latitude_text
    ]
    assert len(archive_only) == 341
    assert all(row.inclusion_status == "archive_identity_only" for row in archive_only)
    assert all(row.longitude_text == "" for row in archive_only)
    assert all(
        "no domestication classification" in row.inclusion_note for row in archive_only
    )


def test_pig_ages_remain_approximate_archaeological_context_points() -> None:
    rows = build_project_sample_chronology_rows(DATA_ROOT, "PRJEB30282")
    by_accession = {
        row.repo_stable_sample_id.rsplit(":", maxsplit=1)[-1].upper(): row
        for row in rows
        if row.repo_stable_sample_id
        in {"prjeb30282:samea5160867", "prjeb30282:samea5160868"}
    }

    assert {
        accession: (
            row.time_start_bp,
            row.time_end_bp,
            row.chronology_evidence_class,
            row.chronology_precision_posture,
            row.dating_basis,
            row.chronology_conflict_note,
        )
        for accession, row in by_accession.items()
    } == {
        "SAMEA5160867": (
            4700,
            4700,
            "archaeological_context_date",
            "sample_approximate_or_modeled",
            "archaeological_context",
            "",
        ),
        "SAMEA5160868": (
            1000,
            1000,
            "archaeological_context_date",
            "sample_approximate_or_modeled",
            "archaeological_context",
            "",
        ),
    }


def test_duplicate_site_matches_fail_closed() -> None:
    leads = resolve_project_locality_leads("PRJEB30282")
    bundso_lead = next(row for row in leads if row.locality_text == "Bundsø")
    site_rows = resolve_project_site_evidence("PRJEB30282")
    bundso_site = next(row for row in site_rows if row.site_label == "Bundsø")

    with pytest.raises(
        ValueError, match="Multiple locality leads match the same sample locality"
    ):
        _matching_locality_lead((bundso_lead, bundso_lead), "Bundsø", "Denmark")
    with pytest.raises(
        ValueError, match="Multiple site evidence rows match the same sample locality"
    ):
        _matching_locality_row((bundso_site, bundso_site), "Bundsø", "Denmark")
