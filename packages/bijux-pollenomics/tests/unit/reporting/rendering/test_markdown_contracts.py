"""Rendered README identity and malformed publication-payload refusals."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.summary_builders.atlas import (
    build_multi_country_bundle_manifest,
    build_multi_country_map_summary,
)
from bijux_pollenomics.reporting.models import CountryReport, MultiCountryMapReport
from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    load_routes,
    verified_authored_reader,
)
from bijux_pollenomics.reporting.rendering.markdown import (
    render_multi_country_map_markdown,
    render_sample_markdown,
    render_summary_markdown,
)


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docs/report/world/world_summary.json").is_file():
            return parent
    raise AssertionError("published world summary fixture is unavailable")


def _world_summary() -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (_repository_root() / "docs/report/world/world_summary.json").read_text(
                encoding="utf-8"
            )
        ),
    )


def _render_world(
    *,
    map_contract: dict[str, object] | None = None,
    animal_summary: dict[str, object] | None = None,
    extra_artifacts: list[tuple[str, str]] | None = None,
) -> str:
    summary = _world_summary()
    artifacts = cast(dict[str, object], summary["artifacts"])
    extra_files = cast(list[dict[str, str]], artifacts["extra_files"])
    return render_multi_country_map_markdown(
        title=cast(str, summary["title"]),
        version=cast(str, summary["version"]),
        generated_on=cast(str, summary["generated_on"]),
        countries=tuple(cast(list[str], summary["countries"])),
        country_sample_counts=cast(dict[str, int], summary["country_sample_counts"]),
        map_html_name=cast(str, artifacts["map_html"]),
        geojson_name=cast(str, artifacts["samples_geojson"]),
        summary_json_name=cast(str, artifacts["summary_json"]),
        map_publication_contract_json_name=cast(
            str, artifacts["map_publication_contract_json"]
        ),
        map_publication_contract_markdown_name=cast(
            str, artifacts["map_publication_contract_markdown"]
        ),
        point_traceability_json_name=cast(str, artifacts["point_traceability_json"]),
        point_traceability_markdown_name=cast(
            str, artifacts["point_traceability_markdown"]
        ),
        extra_artifacts=(
            extra_artifacts
            if extra_artifacts is not None
            else [(row["label"], row["filename"]) for row in extra_files]
        ),
        map_publication_contract=(
            map_contract
            if map_contract is not None
            else cast(dict[str, object], summary["map_publication_contract"])
        ),
        animal_atlas_summary=(
            animal_summary
            if animal_summary is not None
            else cast(dict[str, object], summary["animal_atlas"])
        ),
    )


def _country_report(sample: AdnaSampleRecord | None = None) -> CountryReport:
    return CountryReport(
        country="Sweden",
        version="v66",
        generated_on="2026-09-29",
        total_unique_samples=1 if sample is not None else 0,
        total_unique_localities=0,
        dataset_row_counts={"ho": 1} if sample is not None else {},
        samples=(sample,) if sample is not None else (),
        localities=(),
        output_dir=Path("unused"),
    )


def _sample() -> AdnaSampleRecord:
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace="homo_sapiens:aadr_genetic_id",
            stable_token="SE1",
            accession_lineage=("species:Homo sapiens",),
        ),
        locality_identity=AdnaLocalityIdentity(
            namespace="homo_sapiens:locality",
            stable_token="homo_sapiens:aadr:uppsala",
            locality_text="Uppsala",
            political_entity="Sweden",
            source_anchor_tokens=("SE1",),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_release="v66",
        record_modality="metadata_only",
        review_strength="curated_release_metadata",
        provenance_quality="release_manifest_pinned",
        master_id="SE1",
        group_id="Sweden_Group",
        locality="Uppsala",
        political_entity="Sweden",
        coordinates=AdnaCoordinate(
            latitude=59.8586,
            longitude=17.6389,
            latitude_text="59.8586",
            longitude_text="17.6389",
            confidence="exact",
        ),
        publication="PaperA",
        year_first_published="2022",
        full_date="500 BCE",
        chronology=AdnaChronology(
            original_text="500 BCE",
            time_start_bp=2200,
            time_end_bp=2700,
            time_mean_bp=2450,
        ),
        data_type="HO",
        molecular_sex="F",
        datasets=("ho",),
    )


def test_world_readme_matches_tracked_publication_bytes() -> None:
    expected = (_repository_root() / "docs/report/world/README.md").read_bytes()
    route = load_routes()["docs/report/world/README.md"]
    assert _render_world().encode() == verified_authored_reader(expected, route)


def test_map_readme_keeps_reader_links_and_full_machine_inventory(
    tmp_path: Path,
) -> None:
    extra_artifacts = [
        ("Static atlas bootstrap manifest", "atlas_assets.json"),
        ("Source download", "sources.csv"),
        ("Traceability", "traceability.md"),
        ("Static atlas data chunk", "atlas-nodes.js"),
        ("Static atlas runtime", "atlas-runtime.js"),
        ("Static atlas index transport", "atlas-index-transport.js"),
        ("Interactive evidence tools", "atlas-evidence-tools.js"),
    ]
    original_artifacts = list(extra_artifacts)
    report = MultiCountryMapReport(
        title="Reader inventory fixture",
        slug="atlas",
        version="v66",
        generated_on="2026-09-29",
        countries=(),
        country_sample_counts={},
        total_unique_samples=0,
        output_dir=tmp_path,
    )
    paths = build_atlas_bundle_paths(tmp_path, "atlas", "v66")
    before_summary = build_multi_country_map_summary(report, paths, extra_artifacts, {})
    before_manifest = build_multi_country_bundle_manifest(
        report, paths, extra_artifacts, {}
    )

    rendered = _render_world(extra_artifacts=extra_artifacts)

    for filename in ("atlas_assets.json", "sources.csv", "traceability.md"):
        assert f"[`{filename}`](./{filename})" in rendered
    for filename in (
        "atlas-nodes.js",
        "atlas-runtime.js",
        "atlas-index-transport.js",
        "atlas-evidence-tools.js",
    ):
        assert filename not in rendered
    assert "[complete file inventory](./world_summary.json)" in rendered
    assert "JavaScript data chunks, runtime and optional controllers" in rendered
    for filename in (
        "world_map.html",
        "world_samples.geojson",
        "world_summary.json",
        "world_map_publication_contract.json",
        "world_map_publication_contract.md",
        "world_point_traceability.json",
        "world_point_traceability.md",
    ):
        assert f"[`{filename}`](./{filename})" in rendered
    assert extra_artifacts == original_artifacts
    assert (
        build_multi_country_map_summary(report, paths, extra_artifacts, {})
        == before_summary
    )
    assert (
        build_multi_country_bundle_manifest(report, paths, extra_artifacts, {})
        == before_manifest
    )
    for payload in (before_summary, before_manifest):
        artifacts = cast(dict[str, object], payload["artifacts"])
        assert artifacts["extra_files"] == [
            {
                "label": "Static atlas bootstrap manifest",
                "filename": "atlas_assets.json",
            },
            {"label": "Source download", "filename": "sources.csv"},
            {"label": "Traceability", "filename": "traceability.md"},
            {"label": "Static atlas data chunk", "filename": "atlas-nodes.js"},
            {"label": "Static atlas runtime", "filename": "atlas-runtime.js"},
            {
                "label": "Static atlas index transport",
                "filename": "atlas-index-transport.js",
            },
            {
                "label": "Interactive evidence tools",
                "filename": "atlas-evidence-tools.js",
            },
        ]


@pytest.mark.parametrize("extra_artifacts", [[], [("Traceability", "traceability.md")]])
def test_map_readme_without_javascript_retains_ordinary_artifacts(
    extra_artifacts: list[tuple[str, str]],
) -> None:
    rendered = _render_world(extra_artifacts=extra_artifacts)
    assert "complete file inventory" not in rendered
    for _, filename in extra_artifacts:
        assert f"[`{filename}`](./{filename})" in rendered


def test_map_contract_refuses_malformed_layer_and_label_containers() -> None:
    source = cast(dict[str, object], _world_summary()["map_publication_contract"])
    for field, value in (
        ("layer_rows", [object()]),
        ("filter_surfaces", [1]),
        ("visible_caveats", "not a list"),
    ):
        malformed = dict(source)
        malformed[field] = value
        with pytest.raises(ValueError, match=field):
            _render_world(map_contract=malformed)


def test_animal_summary_refuses_invalid_counts_and_nested_containers() -> None:
    source = cast(dict[str, object], _world_summary()["animal_atlas"])
    for field, value in (
        ("total_locality_points", True),
        ("layer_groups", [1]),
        ("coordinate_confidence_counts", {"direct": -1}),
        ("species_layers", [object()]),
    ):
        malformed = dict(source)
        malformed[field] = value
        with pytest.raises(ValueError, match=field):
            _render_world(animal_summary=malformed)


def test_empty_country_summary_retains_absent_coordinate_text() -> None:
    markdown = render_summary_markdown(
        _country_report(),
        "samples.csv",
        "localities.csv",
        "samples.geojson",
        "samples.md",
        "summary.json",
        None,
    )
    assert markdown.count("No latitude values available") == 1
    assert markdown.count("No longitude values available") == 1


def test_country_renderers_refuse_missing_coordinate_and_locality() -> None:
    sample = _sample()
    without_coordinate = replace(
        sample,
        coordinates=replace(sample.coordinates, latitude=None),
    )
    with pytest.raises(ValueError, match="latitude"):
        render_summary_markdown(
            _country_report(without_coordinate),
            "samples.csv",
            "localities.csv",
            "samples.geojson",
            "samples.md",
            "summary.json",
            None,
        )
    with pytest.raises(ValueError, match="locality"):
        render_sample_markdown(_country_report(replace(sample, locality=None)))
