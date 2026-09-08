from __future__ import annotations

import json
from pathlib import Path

from ....adna.governance.audit_catalogs import build_public_animal_output_honesty
from ...models import CountryReport
from ..comparison_contracts import govern_animal_comparison_payload
from .atlas_readiness import (
    _build_animal_atlas_exclusion_report,
    _build_animal_atlas_readiness,
)
from .chronology_comparisons import (
    _build_animal_human_chronology_overlap,
    _build_animal_pollen_chronology_overlap,
)
from .country_coverage import (
    _build_country_species_coverage,
    _load_country_payloads,
)
from .farming_scenario import _build_farming_history_scenario
from .first_appearance import _build_first_appearance_by_country
from .rendering import (
    _render_animal_atlas_exclusion_report_markdown,
    _render_animal_atlas_readiness_markdown,
    _render_country_species_coverage_markdown,
    _render_first_appearance_markdown,
    _render_human_overlap_markdown,
    _render_output_honesty_markdown,
    _render_pollen_overlap_markdown,
    _render_scenario_markdown,
)

__all__ = ["publish_public_animal_reporting_outputs"]


def publish_public_animal_reporting_outputs(
    output_root: Path,
    *,
    data_root: Path,
    country_reports: tuple[CountryReport, ...],
    country_output_dirs: tuple[Path, ...],
    atlas_output_dir: Path,
) -> dict[str, str]:
    """Write public cross-country animal reporting outputs from generated bundles."""
    country_payloads = _load_country_payloads(country_reports, country_output_dirs)
    coverage_payload = _build_country_species_coverage(country_payloads)
    honesty_payload = build_public_animal_output_honesty(Path(data_root), output_root)
    human_overlap_payload = govern_animal_comparison_payload(
        _build_animal_human_chronology_overlap(country_payloads, country_reports),
        contract_id="animal-human-chronology-overlap",
    )
    pollen_overlap_payload = govern_animal_comparison_payload(
        _build_animal_pollen_chronology_overlap(country_payloads, atlas_output_dir),
        contract_id="animal-pollen-chronology-overlap",
    )
    first_appearance_payload = _build_first_appearance_by_country(country_payloads)
    atlas_readiness_payload = _build_animal_atlas_readiness(
        Path(data_root),
        country_payloads,
    )
    atlas_exclusion_payload = _build_animal_atlas_exclusion_report(Path(data_root))
    scenario_payload = _build_farming_history_scenario(
        coverage_payload=coverage_payload,
        human_overlap_payload=human_overlap_payload,
        pollen_overlap_payload=pollen_overlap_payload,
        first_appearance_payload=first_appearance_payload,
    )

    artifact_payloads = {
        "animal_country_species_coverage": coverage_payload,
        "animal_output_honesty": honesty_payload,
        "animal_human_chronology_overlap": human_overlap_payload,
        "animal_pollen_chronology_overlap": pollen_overlap_payload,
        "animal_first_appearance_by_country": first_appearance_payload,
        "animal_atlas_readiness": atlas_readiness_payload,
        "animal_atlas_exclusion_report": atlas_exclusion_payload,
        "nordic_farming_history_scenario": scenario_payload,
    }
    for stem, payload in artifact_payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
    (output_root / "animal_country_species_coverage.md").write_text(
        _render_country_species_coverage_markdown(coverage_payload),
        encoding="utf-8",
    )
    (output_root / "animal_output_honesty.md").write_text(
        _render_output_honesty_markdown(honesty_payload),
        encoding="utf-8",
    )
    (output_root / "animal_human_chronology_overlap.md").write_text(
        _render_human_overlap_markdown(human_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_pollen_chronology_overlap.md").write_text(
        _render_pollen_overlap_markdown(pollen_overlap_payload),
        encoding="utf-8",
    )
    (output_root / "animal_first_appearance_by_country.md").write_text(
        _render_first_appearance_markdown(first_appearance_payload),
        encoding="utf-8",
    )
    (output_root / "animal_atlas_readiness.md").write_text(
        _render_animal_atlas_readiness_markdown(atlas_readiness_payload),
        encoding="utf-8",
    )
    (output_root / "animal_atlas_exclusion_report.md").write_text(
        _render_animal_atlas_exclusion_report_markdown(atlas_exclusion_payload),
        encoding="utf-8",
    )
    (output_root / "nordic_farming_history_scenario.md").write_text(
        _render_scenario_markdown(scenario_payload),
        encoding="utf-8",
    )
    return {
        "animal_country_species_coverage_json": "animal_country_species_coverage.json",
        "animal_country_species_coverage_markdown": "animal_country_species_coverage.md",
        "animal_output_honesty_json": "animal_output_honesty.json",
        "animal_output_honesty_markdown": "animal_output_honesty.md",
        "animal_human_chronology_overlap_json": "animal_human_chronology_overlap.json",
        "animal_human_chronology_overlap_markdown": "animal_human_chronology_overlap.md",
        "animal_pollen_chronology_overlap_json": "animal_pollen_chronology_overlap.json",
        "animal_pollen_chronology_overlap_markdown": "animal_pollen_chronology_overlap.md",
        "animal_first_appearance_by_country_json": "animal_first_appearance_by_country.json",
        "animal_first_appearance_by_country_markdown": "animal_first_appearance_by_country.md",
        "animal_atlas_readiness_json": "animal_atlas_readiness.json",
        "animal_atlas_readiness_markdown": "animal_atlas_readiness.md",
        "animal_atlas_exclusion_report_json": "animal_atlas_exclusion_report.json",
        "animal_atlas_exclusion_report_markdown": "animal_atlas_exclusion_report.md",
        "nordic_farming_history_scenario_json": "nordic_farming_history_scenario.json",
        "nordic_farming_history_scenario_markdown": "nordic_farming_history_scenario.md",
    }
