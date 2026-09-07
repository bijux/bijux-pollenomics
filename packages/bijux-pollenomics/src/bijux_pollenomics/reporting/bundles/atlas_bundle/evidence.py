"""Scientific evidence, review, and candidate-ranking outputs."""

from __future__ import annotations

from typing import Any

from .ranking_context import candidate_ranking_context_points


def publish_evidence_and_rankings(
    *,
    title: str,
    countries: tuple[str, ...],
    all_samples: Any,
    context_root: Any,
    bundle_paths: Any,
    point_layers: list[dict[str, object]],
    animal_localities: Any,
    animal_coordinate_review: Any,
    extra_artifacts: list[tuple[str, str]],
    surface: Any,
) -> None:
    summarized_localities = tuple(surface.summarize_localities(all_samples))
    context_points = surface._extract_context_points(point_layers)
    evidence_surface = surface.build_atlas_evidence_surface(
        countries=countries,
        human_localities=summarized_localities,
        animal_localities=animal_localities,
        context_points=context_points,
        include_tracked_nonhuman_review=context_root is not None,
    )
    surface.write_atlas_evidence_surface_json(
        bundle_paths.evidence_surface_json_path,
        evidence_surface,
    )
    bundle_paths.evidence_surface_markdown_path.write_text(
        surface.render_atlas_evidence_surface_markdown(evidence_surface),
        encoding="utf-8",
    )
    scientific_review = surface.build_scientific_review_surface(
        countries=countries,
        human_localities=summarized_localities,
        animal_localities=animal_localities,
        context_points=context_points,
        animal_coordinate_review=animal_coordinate_review,
        include_tracked_nonhuman_review=context_root is not None,
    )
    surface.write_scientific_review_surface_json(
        bundle_paths.scientific_review_json_path,
        scientific_review,
    )
    bundle_paths.scientific_review_markdown_path.write_text(
        surface.render_scientific_review_surface_markdown(scientific_review),
        encoding="utf-8",
    )
    ranking_context_points = candidate_ranking_context_points(
        point_layers, context_points
    )
    ranked_sites = surface.rank_localities(
        summarized_localities,
        ranking_context_points,
        profile_name="atlas_exploration",
    )
    sensitivity_report = surface.build_ranking_sensitivity_report(
        summarized_localities,
        ranking_context_points,
    )
    ranking_engine_manifest = surface.build_ranking_engine_manifest()
    surface.write_candidate_sites_csv(
        bundle_paths.candidate_sites_csv_path, ranked_sites
    )
    surface.write_candidate_sites_json(
        bundle_paths.candidate_sites_json_path, ranked_sites
    )
    bundle_paths.candidate_sites_markdown_path.write_text(
        surface.render_candidate_site_markdown(ranked_sites, title=title),
        encoding="utf-8",
    )
    surface.write_candidate_site_sensitivity_json(
        bundle_paths.candidate_site_sensitivity_json_path,
        sensitivity_report,
    )
    bundle_paths.candidate_site_sensitivity_markdown_path.write_text(
        surface.render_candidate_site_sensitivity_markdown(
            sensitivity_report, title=title
        ),
        encoding="utf-8",
    )
    bundle_paths.candidate_ranking_engine_manifest_path.write_text(
        surface.json.dumps(ranking_engine_manifest.as_dict(), indent=2),
        encoding="utf-8",
    )
    extra_artifacts.extend(
        [
            ("Candidate site ranking CSV", bundle_paths.candidate_sites_csv_path.name),
            (
                "Candidate site ranking JSON",
                bundle_paths.candidate_sites_json_path.name,
            ),
            (
                "Candidate site ranking markdown",
                bundle_paths.candidate_sites_markdown_path.name,
            ),
            (
                "Candidate site sensitivity JSON",
                bundle_paths.candidate_site_sensitivity_json_path.name,
            ),
            (
                "Candidate site sensitivity markdown",
                bundle_paths.candidate_site_sensitivity_markdown_path.name,
            ),
            (
                "Candidate ranking engine manifest",
                bundle_paths.candidate_ranking_engine_manifest_path.name,
            ),
            (
                "Atlas evidence surface JSON",
                bundle_paths.evidence_surface_json_path.name,
            ),
            (
                "Atlas evidence surface markdown",
                bundle_paths.evidence_surface_markdown_path.name,
            ),
            (
                "Atlas scientific review JSON",
                bundle_paths.scientific_review_json_path.name,
            ),
            (
                "Atlas scientific review markdown",
                bundle_paths.scientific_review_markdown_path.name,
            ),
        ]
    )
