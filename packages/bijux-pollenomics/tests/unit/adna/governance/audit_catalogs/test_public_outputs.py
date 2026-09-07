"""Public animal output audit tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs import public_outputs
from bijux_pollenomics.adna.governance.audit_catalogs.public_outputs import (
    build_public_animal_output_audit,
    build_public_animal_output_honesty,
)
from bijux_pollenomics.adna.governance.audit_catalogs.rendering import (
    render_public_animal_output_audit_markdown,
    render_public_animal_output_honesty_markdown,
)

from .fixtures import write_atlas_candidates, write_country_summary, write_world_summary

pytestmark = pytest.mark.generated_artifacts


def test_public_audit_reports_absent_public_outputs_honestly(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    public_audit = build_public_animal_output_audit(catalog_data_root, report_root)
    markdown = render_public_animal_output_audit_markdown(public_audit)

    assert "ships no mapped non-human animal atlas localities" in markdown
    assert "Tracked sample rows" in markdown


def test_public_audit_counts_species_layers_from_governed_atlas_candidates(
    catalog_data_root: Path,
    report_root: Path,
) -> None:
    write_world_summary(report_root, sheep_locality_count=3)
    write_atlas_candidates(catalog_data_root, sheep_locality_count=3)

    public_audit = build_public_animal_output_audit(catalog_data_root, report_root)
    markdown = render_public_animal_output_audit_markdown(public_audit)

    sheep_row = next(
        row
        for row in public_audit["species_rows"]
        if row["species_latin_name"] == "Ovis aries"
    )
    assert sheep_row["atlas_locality_count"] == 3
    assert "ships `3` mapped non-human animal atlas localities" in markdown


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

    assert honesty["schema_version"] == "animal-output-honesty.v2"
    assert totals["tracked_sample_count"] == 1450
    assert totals["mapped_sample_count"] == 331
    assert totals["blocked_sample_count"] == 1119
    assert totals["mapped_sample_count"] + totals["blocked_sample_count"] == 1450
    assert totals["unresolved_sample_count"] == 402
    assert totals["country_published_sample_count"] == 0
    assert sum(row["tracked_sample_count"] for row in honesty["rows"]) == 1450
    assert "Tracked sample rows: `1450`" in markdown


def _sample_row(
    stable_id: str,
    *,
    species_name: str = "Ovis aries",
    inclusion_status: str = "sample_context_published",
) -> dict[str, object]:
    return {
        "identity": {"stable_token": stable_id},
        "species_latin_name": species_name,
        "species_common_name": "sheep",
        "inclusion_status": inclusion_status,
    }


def _stub_honesty_inputs(
    monkeypatch: pytest.MonkeyPatch,
    rows: list[dict[str, object]],
    *,
    mapped: set[str] | None = None,
    country_published: set[str] | None = None,
) -> None:
    monkeypatch.setattr(public_outputs, "_species_roots", lambda _root: [Path("sheep")])
    monkeypatch.setattr(public_outputs, "_load_sample_rows", lambda _root: rows)
    monkeypatch.setattr(
        public_outputs,
        "_load_mapped_sample_ids_by_species",
        lambda _root: {"Ovis aries": mapped if mapped is not None else {"sample-1"}},
    )
    monkeypatch.setattr(
        public_outputs,
        "_load_country_sample_ids_by_species",
        lambda _root: {
            "Ovis aries": country_published if country_published is not None else set()
        },
    )


def test_output_honesty_validates_sample_identity_and_membership(
    monkeypatch: pytest.MonkeyPatch,
    report_root: Path,
) -> None:
    rows = [
        _sample_row("sample-1"),
        _sample_row("sample-2", inclusion_status="sample_context_blocked"),
    ]
    _stub_honesty_inputs(monkeypatch, rows, country_published={"sample-1"})

    honesty = build_public_animal_output_honesty(Path("data"), report_root)

    assert honesty["totals"] == {
        "tracked_sample_count": 2,
        "mapped_sample_count": 1,
        "blocked_sample_count": 1,
        "unresolved_sample_count": 1,
        "country_published_sample_count": 1,
    }


@pytest.mark.parametrize(
    ("rows", "mapped", "country_published", "message"),
    [
        ([_sample_row("")], set(), set(), "blank stable IDs"),
        (
            [_sample_row("sample-1"), _sample_row("sample-1")],
            {"sample-1"},
            set(),
            "duplicate stable IDs",
        ),
        (
            [
                _sample_row("sample-1"),
                _sample_row("sample-2", species_name="Capra hircus"),
            ],
            {"sample-1"},
            set(),
            "mixed species identity",
        ),
        ([_sample_row("sample-1")], {"foreign"}, set(), "not tracked"),
        (
            [_sample_row("sample-1")],
            {"sample-1"},
            {"foreign"},
            "not mapped",
        ),
        (
            [_sample_row("sample-1", inclusion_status="sample_context_blocked")],
            {"sample-1"},
            set(),
            "not blocked",
        ),
    ],
)
def test_output_honesty_refuses_identity_and_membership_drift(
    monkeypatch: pytest.MonkeyPatch,
    report_root: Path,
    rows: list[dict[str, object]],
    mapped: set[str],
    country_published: set[str],
    message: str,
) -> None:
    _stub_honesty_inputs(
        monkeypatch,
        rows,
        mapped=mapped,
        country_published=country_published,
    )

    with pytest.raises(ValueError, match=message):
        build_public_animal_output_honesty(Path("data"), report_root)
