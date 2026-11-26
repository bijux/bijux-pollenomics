"""Bind animal point inputs to the maintained Atlas layer owner."""

from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.governance.atlas_candidates.point_inputs import (
    AnimalPointInputs,
)

from ....adna.animal_localities import build_tracked_animal_atlas_bundle
from ....adna.animal_localities.assembly import (
    build_tracked_animal_atlas_bundle_from_inputs,
)


def require_animal_capture_owner(
    context_root: Path | None, surface: Any, inputs: AnimalPointInputs | None
) -> None:
    """Refuse a substituted owner or a context different from the held inputs."""
    if inputs is not None and (
        context_root is None
        or Path(context_root).absolute() != inputs.context_root
        or surface.build_tracked_animal_atlas_bundle
        is not build_tracked_animal_atlas_bundle
    ):
        raise ValueError("animal point capture requires the maintained animal owner")


def prepare_animal_layers(
    *,
    context_root: Path | None,
    staging_output_dir: Path,
    slug: str,
    geography_scope: Any,
    point_layers: list[dict[str, object]],
    extra_artifacts: list[tuple[str, str]],
    surface: Any,
    inputs: AnimalPointInputs | None,
) -> tuple[Any, Any, Any]:
    """Build point layers from held inputs when selected; chronology remains separate."""
    localities: Any = ()
    review = surface.AnimalCoordinateVisibilityReview(
        direct_coordinate_feature_count=0,
        named_site_geocoded_feature_count=0,
        weaker_geography_feature_count=0,
    )
    chronology = None
    if context_root is not None:
        if inputs is None:
            bundle = surface.build_tracked_animal_atlas_bundle(
                data_root=context_root,
                output_dir=staging_output_dir,
                atlas_slug=slug,
                geography_scope=geography_scope,
            )
        else:
            bundle = build_tracked_animal_atlas_bundle_from_inputs(
                data_root=context_root,
                output_dir=staging_output_dir,
                atlas_slug=slug,
                geography_scope=geography_scope,
                point_inputs=inputs,
            )
        point_layers.extend(bundle.point_layers)
        extra_artifacts.extend(bundle.extra_artifacts)
        if surface.animal_sample_chronology_context_available(context_root):
            chronology = surface.build_animal_sample_chronology_context(
                data_root=context_root, geography_scope=geography_scope
            )
            point_layers.extend(chronology.point_layers)
        localities = bundle.localities
        review = surface.AnimalCoordinateVisibilityReview(
            direct_coordinate_feature_count=bundle.coordinate_review.direct_coordinate_feature_count,
            named_site_geocoded_feature_count=bundle.coordinate_review.named_site_geocoded_feature_count,
            weaker_geography_feature_count=bundle.coordinate_review.weaker_geography_feature_count,
        )
    return localities, review, chronology
