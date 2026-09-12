"""Explicit prediction and observation-scoring command interfaces."""

from __future__ import annotations

import argparse
from pathlib import Path


def build_prepare_lra_experiment_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Keep prediction execution and later observation access separate."""
    prepare = subparsers.add_parser(
        "prepare-lra-experiment",
        help="Reconstruct training folds and freeze exploratory site predictions.",
    )
    prepare.add_argument(
        "request", type=Path, help="Declared synthetic lra-experiment.v1 JSON."
    )
    prepare.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root for declared raw and geometry evidence.",
    )
    prepare.add_argument(
        "--cache-root",
        type=Path,
        required=True,
        help="Verified reconstruction cache directory.",
    )
    prepare.add_argument(
        "--output", type=Path, required=True, help="New prediction product directory."
    )
    prepare.add_argument(
        "--max-workers", type=int, default=1, help="Maximum concurrent model calls."
    )
    return prepare


def build_score_lra_experiment_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Require an externally identified prediction product before scoring."""
    score = subparsers.add_parser(
        "score-lra-experiment",
        help="Score separate synthetic observations against frozen predictions.",
    )
    score.add_argument(
        "product", type=Path, help="Previously frozen prediction product."
    )
    score.add_argument(
        "--expected-manifest-sha256",
        required=True,
        help="Independently retained prediction manifest SHA-256.",
    )
    score.add_argument(
        "--outcome-root",
        type=Path,
        required=True,
        help="Root containing separate held-out observations.",
    )
    score.add_argument(
        "--outcome-inventory",
        type=Path,
        required=True,
        help="Declared synthetic outcome references and hashes.",
    )
    score.add_argument(
        "--output", type=Path, required=True, help="New score product directory."
    )
    return score
