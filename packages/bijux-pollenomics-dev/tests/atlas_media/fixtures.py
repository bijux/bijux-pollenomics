"""Synthetic content-bound atlas media fixtures."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SourceChronologyNode,
)
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
from bijux_pollenomics.reporting.source_chronology.facets import build_facet_metadata
from bijux_pollenomics.reporting.source_chronology.features import build_atlas_feature
from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    NEOTOMA_SOURCE_LABEL_TAXA,
    build_neotoma_source_label_preset_catalog,
)
from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasCandidate
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaPlan, StorySelection
from bijux_pollenomics_dev.ci.atlas_media.source_authority import (
    SourceChronologyAuthority,
    SourceFacetAuthority,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
BUILD_ID = "atlas-" + ("d" * 64)
SOURCE_SNAPSHOT_ID = "sha256:" + ("e" * 64)
SOURCE_BUILD_ID = "sha256:" + ("f" * 64)
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


def source_preset_catalog() -> dict[str, object]:
    """Return the exact governed literal source-label catalog fixture."""
    return build_neotoma_source_label_preset_catalog(
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        build_id=SOURCE_BUILD_ID,
    )


def _source_node(
    *,
    node_level: str,
    ordinal: int,
    younger_bp: float,
    older_bp: float,
    observation_count: int = 1,
    source_taxon_id: int | str | None = None,
    source_reported_name: str | None = None,
    source_ecological_group: str | None = None,
    site_id: str | None = None,
) -> SourceChronologyNode:
    token = f"{node_level}-{ordinal}"
    return SourceChronologyNode(
        node_id=f"node-{token}",
        source_family="neotoma",
        source_snapshot_id=SOURCE_SNAPSHOT_ID,
        source_record_id=f"sample-{token}",
        site_id=site_id or f"site-{token}",
        observation_ids=tuple(
            f"observation-{token}-{index}" for index in range(observation_count)
        ),
        node_level=node_level,
        feature_key=(
            f"source:neotoma:taxon:{source_taxon_id}"
            if source_taxon_id is not None
            else f"source:neotoma:ecological-code:{source_ecological_group}"
            if source_ecological_group is not None
            else "source:neotoma:sample-presence"
        ),
        source_variable_ids=(
            (f"variable-{source_taxon_id}",) if source_taxon_id is not None else ()
        ),
        source_taxon_id=source_taxon_id,
        source_reported_name=source_reported_name,
        source_ecological_group=source_ecological_group,
        source_unit="count",
        country_code="SE",
        latitude=56.0 + (ordinal / 10_000),
        longitude=13.0 + (ordinal / 10_000),
        coordinate_quality="source_coordinate",
        chronology_claim_id=f"chronology-claim-{token}",
        chronology_id=f"chronology-{token}",
        chronology_name="Synthetic selected chronology",
        is_default_chronology=True,
        chronology_selection_posture="selected_source_default",
        younger_bp=younger_bp,
        older_bp=older_bp,
        provenance_record_id=f"provenance-{token}",
        input_digest="sha256:" + ("1" * 64),
        config_digest="sha256:" + ("2" * 64),
        producer_version="atlas-media-fixture",
        build_id=SOURCE_BUILD_ID,
        candidate_refusal_reason={
            "source_sample_presence": "reviewed_pollen_sum_not_available",
            "source_ecological_code": "source_ecological_equivalence_not_reviewed",
            "source_taxon": "source_taxon_equivalence_not_reviewed",
        }[node_level],
    )


def _source_nodes() -> tuple[SourceChronologyNode, ...]:
    nodes = [
        _source_node(
            node_level="source_sample_presence",
            ordinal=index,
            younger_bp=0,
            older_bp=22_911,
            observation_count=2,
        )
        for index in range(10)
    ]
    for code, maximum, offset in (
        ("TRSH", 22_911, 100),
        ("UPHE", 22_911, 200),
        ("AQVP", 19_190, 300),
    ):
        nodes.extend(
            _source_node(
                node_level="source_ecological_code",
                ordinal=offset + index,
                younger_bp=0,
                older_bp=maximum,
                observation_count=2 if index < 3 else 1,
                source_ecological_group=code,
            )
            for index in range(5)
        )
    for index, taxon in enumerate(NEOTOMA_SOURCE_LABEL_TAXA, start=1):
        count = 3 if taxon.source_taxon_id == 967 else 1
        exact_intervals = {
            414: (6.3, 13_907),
            415: (24, 9_138),
            416: (0, 2_337),
            427: (0, 11_891),
            497: (2.780076, 10_646),
            967: (2, 4_461),
            969: (11, 7_197.5),
            3705: (2.780076, 12_318),
            3915: (6.3, 1_725),
            3923: (11, 6_645),
            3924: (376, 1_751),
            3926: (0, 3_067),
        }
        for member_index in range(count):
            younger, older = exact_intervals.get(
                taxon.source_taxon_id,
                (float(index), float(index + 200)),
            )
            nodes.append(
                _source_node(
                    node_level="source_taxon",
                    ordinal=1_000 + (index * 10) + member_index,
                    younger_bp=younger,
                    older_bp=older,
                    observation_count=(
                        2
                        if taxon.source_taxon_id == 967 and member_index == 0
                        else 1
                    ),
                    source_taxon_id=taxon.source_taxon_id,
                    source_reported_name=taxon.source_reported_name,
                    site_id=(
                        f"site-source-taxon-secale-{min(member_index, 1)}"
                        if taxon.source_taxon_id == 967
                        else None
                    ),
                )
            )
    nodes.append(
        _source_node(
            node_level="source_taxon",
            ordinal=9_999,
            younger_bp=100.5,
            older_bp=100.5,
            source_taxon_id="instant",
            source_reported_name="Exact instant",
        )
    )
    return tuple(nodes)


def _source_layers() -> list[dict[str, object]]:
    nodes = _source_nodes()
    common = {
        "semantic_role": "source_chronology_context",
        "propagation_status": "refused",
        "edge_count": 0,
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "source_snapshot_id": SOURCE_SNAPSHOT_ID,
        "build_id": SOURCE_BUILD_ID,
    }
    layers = []
    for level in (
        "source_sample_presence",
        "source_ecological_code",
        "source_taxon",
    ):
        selected = [node for node in nodes if node.node_level == level]
        layers.append(
            {
                **common,
                "node_level": level,
                "count": len(selected),
                "facet_metadata": build_facet_metadata(
                    nodes,
                    node_level=level,
                    source_snapshot_id=SOURCE_SNAPSHOT_ID,
                    build_id=SOURCE_BUILD_ID,
                ),
                "features": [build_atlas_feature(node) for node in selected],
            }
        )
    return layers


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
                "no_pollen_data_count": 4,
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
    source_chronology = build_source_chronology_storyboards(
        _source_layers(), countries=COUNTRIES
    )
    modeled_stories = build_modeled_context_storyboards(
        _modeled_manifest(), countries=COUNTRIES
    )
    storyboard = build_playback_manifest(
        source_chronology=source_chronology,
        modeled_stories=modeled_stories,
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
        selection=StorySelection(
            source_label_presets=(
                "avena",
                "hordeum",
                "triticum",
                "secale",
                "cerealia",
            )
        ),
    )


def source_authority() -> SourceChronologyAuthority:
    """Return source facts matching the synthetic storyboard fixture."""
    facets: dict[tuple[str, str], SourceFacetAuthority] = {}
    buckets: dict[tuple[str, str], list[SourceChronologyNode]] = {}
    for node in _source_nodes():
        selector = (
            "all"
            if node.node_level == "source_sample_presence"
            else str(node.source_ecological_group)
            if node.node_level == "source_ecological_code"
            else node.feature_key
        )
        buckets.setdefault((node.node_level, selector), []).append(node)
    for (kind, value), nodes in buckets.items():
        facets[(kind, value)] = SourceFacetAuthority(
            selector_kind=kind,
            selector_value=value,
            label=nodes[0].source_reported_name,
            site_count=len({node.site_id for node in nodes}),
            node_count=len(nodes),
            observation_denominator=sum(len(node.observation_ids) for node in nodes),
            time_min_bp=min(node.younger_bp for node in nodes),
            time_max_bp=max(node.older_bp for node in nodes),
            intervals=tuple((node.younger_bp, node.older_bp) for node in nodes),
            site_intervals=tuple(
                (node.site_id, node.younger_bp, node.older_bp) for node in nodes
            ),
            observation_intervals=tuple(
                (len(node.observation_ids), node.younger_bp, node.older_bp)
                for node in nodes
            ),
        )
    return SourceChronologyAuthority(
        build_id=BUILD_ID,
        digest="1" * 64,
        asset_sha256=("2" * 64,),
        facets=facets,
    )
