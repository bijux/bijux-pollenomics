"""Synthetic content-bound atlas media fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from bijux_pollenomics.reporting.map_playback import (
    build_modeled_context_storyboards,
    build_playback_manifest,
    build_source_chronology_storyboards,
    canonical_json_bytes,
    refuse_candidate_succession_storyboard,
)
from bijux_pollenomics.reporting.modeled_context.contracts import (
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import METRIC_FAMILIES
from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasCandidate
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaPlan
from bijux_pollenomics_dev.ci.atlas_media.source_authority import (
    SourceChronologyAuthority,
    SourceFacetAuthority,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
BUILD_ID = "atlas-" + ("d" * 64)
COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
SUCCESSION = {
    "product_key": "candidate_succession",
    "status": "refused",
    "reason_code": "accepted_scientific_classifications_not_available",
    "detail": (
        "No candidate-succession story is published. Dated observations and modeled "
        "context do not establish movement, migration, or causation."
    ),
    "story_count": 0,
    "edge_count": 0,
}


def candidate() -> AtlasCandidate:
    """Return a stable synthetic repository and atlas identity."""
    return AtlasCandidate(SHA_A, SHA_B, SHA_C, BUILD_ID)


def _time_density(
    node_count: int,
    observation_denominator: int,
    time_min_bp: float,
    time_max_bp: float,
) -> dict[str, object]:
    span = time_max_bp - time_min_bp
    bins = (
        [
            {
                "ordinal": 0,
                "younger_bp": time_min_bp,
                "older_bp": time_max_bp,
                "node_count": node_count,
                "observation_denominator": observation_denominator,
            }
        ]
        if span == 0
        else [
            {
                "ordinal": ordinal,
                "younger_bp": time_min_bp + ((11 - ordinal) * span / 12),
                "older_bp": time_min_bp + ((12 - ordinal) * span / 12),
                "node_count": node_count,
                "observation_denominator": observation_denominator,
            }
            for ordinal in range(12)
        ]
    )
    return {
        "schema_version": "source-chronology-time-density.v1",
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "bin_admission": "closed_interval_overlap",
        "bins_are_additive": False,
        "node_count": node_count,
        "observation_denominator": observation_denominator,
        "time_min_bp": time_min_bp,
        "time_max_bp": time_max_bp,
        "bins": bins,
    }


def _source_layers() -> list[dict[str, object]]:
    common = {
        "semantic_role": "source_chronology_context",
        "propagation_status": "refused",
        "edge_count": 0,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
    }
    return [
        {
            **common,
            "node_level": "source_sample_presence",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_sample_presence",
                "node_count": 10,
                "observation_denominator": 20,
                "time_min_bp": 0,
                "time_max_bp": 250,
                "time_density": _time_density(10, 20, 0, 250),
            },
        },
        {
            **common,
            "node_level": "source_ecological_code",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_ecological_code",
                "source_ecological_codes": [
                    {
                        "value": code,
                        "label": label,
                        "node_count": 5,
                        "observation_denominator": 8,
                        "time_min_bp": 0,
                        "time_max_bp": maximum,
                        "time_density": _time_density(5, 8, 0, maximum),
                    }
                    for code, label, maximum in (
                        ("TRSH", "Trees and Shrubs", 250),
                        ("UPHE", "Upland Herbs", 240),
                        ("AQVP", "Aquatic Vascular Plants", 190),
                    )
                ],
                "node_count": 15,
                "observation_denominator": 24,
                "time_min_bp": 0,
                "time_max_bp": 250,
                "time_density": _time_density(15, 24, 0, 250),
            },
        },
        {
            **common,
            "node_level": "source_taxon",
            "facet_metadata": {
                "schema_version": "neotoma-source-chronology-facets.v3",
                "node_level": "source_taxon",
                "source_taxa": [
                    {
                        "value": "source:neotoma:taxon:967",
                        "source_taxon_id": "secale",
                        "label": "Secale",
                        "node_count": 3,
                        "observation_denominator": 4,
                        "time_min_bp": 36.16162,
                        "time_max_bp": 236.75,
                        "time_density": _time_density(3, 4, 36.16162, 236.75),
                    },
                    {
                        "value": "source:neotoma:taxon:instant",
                        "source_taxon_id": "instant",
                        "label": "Exact instant",
                        "node_count": 1,
                        "observation_denominator": 1,
                        "time_min_bp": 100.5,
                        "time_max_bp": 100.5,
                        "time_density": _time_density(1, 1, 100.5, 100.5),
                    },
                ],
                "node_count": 4,
                "observation_denominator": 5,
                "time_min_bp": 36.16162,
                "time_max_bp": 236.75,
                "time_density": _time_density(4, 5, 36.16162, 236.75),
            },
        },
    ]


def _modeled_manifest() -> dict[str, object]:
    return {
        "schema_version": "modeled-context-manifest.v3",
        "status": "available",
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "interpolation_allowed": False,
        "dataset_id": "937075",
        "metric_count": 47,
        "metric_families": [family.as_dict() for family in METRIC_FAMILIES],
        "windows_oldest_to_present": [
            {
                "label": label,
                "time_start_bp": younger,
                "time_end_bp": older,
                "feature_count": 75,
            }
            for label, younger, older in reversed(PANGAEA_WINDOWS_PRESENT_TO_OLDEST)
        ],
    }


def write_inputs(root: Path) -> tuple[Path, Path, Path]:
    """Write a static identity, document, and canonical storyboard manifest."""
    atlas_root = root / "docs/report/regions/nordic"
    atlas_root.mkdir(parents=True)
    document = atlas_root / "nordic_map.html"
    document.write_text("<!doctype html><title>atlas</title>\n", encoding="utf-8")
    atlas_manifest = atlas_root / "nordic_map_assets.json"
    atlas_manifest.write_text(
        json.dumps(
            {
                "schema_version": "atlas-static-bootstrap.v2",
                "scope_slug": "nordic",
                "build_id": BUILD_ID,
                "version": "v66",
                "assets": {"fields": [], "records": []},
            }
        ),
        encoding="utf-8",
    )
    source_stories, taxa = build_source_chronology_storyboards(
        _source_layers(), countries=COUNTRIES
    )
    modeled_stories = build_modeled_context_storyboards(
        _modeled_manifest(), countries=COUNTRIES
    )
    storyboard = build_playback_manifest(
        source_stories=source_stories,
        modeled_stories=modeled_stories,
        exact_taxa=taxa,
        candidate_succession=refuse_candidate_succession_storyboard(
            {
                "propagation_status": "refused",
                "edge_count": 0,
                "reason_code": "accepted_scientific_classifications_not_available",
            }
        ),
        atlas_build_id=BUILD_ID,
        scope_slug="nordic",
        version="v66",
        countries=COUNTRIES,
    )
    storyboard_path = root / "artifacts/input/playback.json"
    storyboard_path.parent.mkdir(parents=True)
    storyboard_path.write_bytes(canonical_json_bytes(storyboard) + b"\n")
    return document, atlas_manifest, storyboard_path


def plan(root: Path) -> AtlasMediaPlan:
    """Return a plan backed by synthetic inputs and executable placeholders."""
    document, atlas_manifest, storyboard = write_inputs(root)
    binaries = root / "artifacts/bin"
    binaries.mkdir(parents=True)
    paths = []
    for name in ("brave", "node", "ffmpeg", "ffprobe"):
        path = binaries / name
        path.write_text("binary", encoding="utf-8")
        paths.append(path)
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required for candidate-backed media fixtures")
    subprocess.run(  # nosec B603
        (git, "init", "--quiet", "--initial-branch=main"), cwd=root, check=True
    )
    subprocess.run(  # nosec B603
        (
            git,
            "add",
            "--",
            document.relative_to(root).as_posix(),
            atlas_manifest.relative_to(root).as_posix(),
            storyboard.relative_to(root).as_posix(),
        ),
        cwd=root,
        check=True,
    )
    subprocess.run(  # nosec B603
        (
            git,
            "-c",
            "user.name=Bijux Tests",
            "-c",
            "user.email=tests@bijux.invalid",
            "commit",
            "--quiet",
            "-m",
            "test: establish atlas fixture",
        ),
        cwd=root,
        check=True,
    )
    head = subprocess.run(  # nosec B603
        (git, "rev-parse", "HEAD"),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(  # nosec B603
        (git, "rev-parse", "HEAD^{tree}"),
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return AtlasMediaPlan(
        repository_root=root,
        artifact_root=root / "artifacts/media",
        browser_binary=paths[0],
        node_binary=paths[1],
        ffmpeg_binary=paths[2],
        ffprobe_binary=paths[3],
        atlas_document=document.relative_to(root).as_posix(),
        atlas_manifest=atlas_manifest.relative_to(root).as_posix(),
        storyboard_manifest=storyboard.relative_to(root).as_posix(),
        candidate=AtlasCandidate(head, tree, head, BUILD_ID),
    )


def source_authority() -> SourceChronologyAuthority:
    """Return source facts matching the synthetic storyboard fixture."""
    facets: dict[tuple[str, str], SourceFacetAuthority] = {}
    for kind, value, count, denominator, younger, older in (
        ("source_sample_presence", "all", 10, 20, 0, 250),
        ("source_ecological_code", "TRSH", 5, 8, 0, 250),
        ("source_ecological_code", "UPHE", 5, 8, 0, 240),
        ("source_ecological_code", "AQVP", 5, 8, 0, 190),
        ("source_taxon", "source:neotoma:taxon:967", 3, 4, 36.16162, 236.75),
        ("source_taxon", "source:neotoma:taxon:instant", 1, 1, 100.5, 100.5),
    ):
        facets[(kind, value)] = SourceFacetAuthority(
            selector_kind=kind,
            selector_value=value,
            node_count=count,
            observation_denominator=denominator,
            intervals=tuple((younger, older) for _ in range(count)),
        )
    return SourceChronologyAuthority(
        build_id=BUILD_ID,
        digest="1" * 64,
        asset_sha256=("2" * 64,),
        facets=facets,
    )
