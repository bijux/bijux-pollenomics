"""Public animal output audit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.public_outputs import (
    build_public_animal_output_audit,
    build_public_animal_output_honesty,
)
from bijux_pollenomics.adna.governance.audit_catalogs.rendering import (
    render_public_animal_output_audit_markdown,
    render_public_animal_output_honesty_markdown,
)

from .fixtures import write_country_summary, write_world_summary

pytestmark = pytest.mark.generated_artifacts


def test_public_audit_reports_absent_public_outputs_honestly(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    public_audit = build_public_animal_output_audit(catalog_data_root, report_root)
    markdown = render_public_animal_output_audit_markdown(public_audit)

    assert "ships no mapped non-human animal atlas layers" in markdown
    assert "Tracked sample rows" in markdown


def test_public_audit_counts_species_layers_from_shipped_atlas_summary(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    write_world_summary(report_root)

    public_audit = build_public_animal_output_audit(catalog_data_root, report_root)
    markdown = render_public_animal_output_audit_markdown(public_audit)

    sheep_row = next(
        row
        for row in public_audit["species_rows"]
        if row["species_latin_name"] == "Ovis aries"
    )
    assert sheep_row["atlas_layer_count"] == 1
    assert "ships `2` mapped non-human animal atlas layer rows" in markdown


def test_public_audit_counts_country_outputs_from_country_summary(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    write_country_summary(report_root)

    public_audit = build_public_animal_output_audit(catalog_data_root, report_root)
    markdown = render_public_animal_output_audit_markdown(public_audit)

    sheep_row = next(
        row
        for row in public_audit["species_rows"]
        if row["species_latin_name"] == "Ovis aries"
    )
    assert sheep_row["country_output_count"] == 1
    assert "country-resolved animal output hits" in markdown


def test_output_honesty_reconciles_tracked_mapped_and_blocked_samples(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    honesty = build_public_animal_output_honesty(catalog_data_root, report_root)
    totals = honesty["totals"]
    markdown = render_public_animal_output_honesty_markdown(honesty)

    assert totals["tracked_sample_count"] == 1451
    assert totals["mapped_sample_count"] + totals["blocked_sample_count"] == 1451
    assert totals["unresolved_sample_count"] == 0
    assert totals["country_published_sample_count"] == 0
    assert sum(row["tracked_sample_count"] for row in honesty["rows"]) == 1451
    assert "Tracked sample rows: `1451`" in markdown
