"""Command-line entry point for content-bound atlas media materialization."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasCandidate

from .catalog import (
    DEFAULT_EXACT_TAXA,
    DEFAULT_MODELED_METRICS,
    DEFAULT_SOURCE_LABEL_PRESETS,
)
from .contracts import AtlasMediaError, AtlasMediaPlan, StorySelection
from .runner import materialize_atlas_media


def _binary(name: str, fallback: str | None = None) -> Path:
    resolved = shutil.which(name)
    if resolved is not None:
        return Path(resolved)
    if fallback is not None and Path(fallback).is_file():
        return Path(fallback)
    raise AtlasMediaError(f"required binary is unavailable: {name}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a governed Nordic atlas storyboard as poster, MP4, and GIF."
    )
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--storyboard-manifest", required=True)
    parser.add_argument(
        "--atlas-document",
        default="docs/report/regions/nordic/nordic_map.html",
    )
    parser.add_argument(
        "--atlas-manifest",
        default="docs/report/regions/nordic/nordic_map_assets.json",
    )
    parser.add_argument("--repository-head", required=True)
    parser.add_argument("--repository-tree", required=True)
    parser.add_argument("--atlas-output-commit", required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--browser-binary", type=Path)
    parser.add_argument("--node-binary", type=Path)
    parser.add_argument("--ffmpeg-binary", type=Path)
    parser.add_argument("--ffprobe-binary", type=Path)
    parser.add_argument("--no-core-source-stories", action="store_true")
    parser.add_argument("--exact-taxon", action="append")
    parser.add_argument("--source-label-preset", action="append")
    parser.add_argument("--modeled-metric", action="append")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--frames-per-second", type=int, default=12)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse explicit release identities and run the materializer."""
    arguments = _parser().parse_args(argv)
    try:
        plan = AtlasMediaPlan(
            repository_root=arguments.repository_root,
            artifact_root=arguments.artifact_root,
            browser_binary=arguments.browser_binary
            or _binary(
                "brave",
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            ),
            node_binary=arguments.node_binary or _binary("node"),
            ffmpeg_binary=arguments.ffmpeg_binary or _binary("ffmpeg"),
            ffprobe_binary=arguments.ffprobe_binary or _binary("ffprobe"),
            atlas_document=arguments.atlas_document,
            atlas_manifest=arguments.atlas_manifest,
            storyboard_manifest=arguments.storyboard_manifest,
            candidate=AtlasCandidate(
                repository_head=arguments.repository_head,
                repository_tree=arguments.repository_tree,
                atlas_output_commit=arguments.atlas_output_commit,
                build_id=arguments.build_id,
            ),
            selection=StorySelection(
                include_core_source_stories=not arguments.no_core_source_stories,
                source_label_presets=tuple(
                    arguments.source_label_preset or DEFAULT_SOURCE_LABEL_PRESETS
                ),
                exact_taxa=tuple(arguments.exact_taxon or DEFAULT_EXACT_TAXA),
                modeled_metrics=tuple(
                    arguments.modeled_metric or DEFAULT_MODELED_METRICS
                ),
            ),
            width=arguments.width,
            height=arguments.height,
            frames_per_second=arguments.frames_per_second,
            timeout_seconds=arguments.timeout_seconds,
        )
        result = materialize_atlas_media(plan)
    except (AtlasMediaError, ValueError) as error:
        print(f"atlas media materialization refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
