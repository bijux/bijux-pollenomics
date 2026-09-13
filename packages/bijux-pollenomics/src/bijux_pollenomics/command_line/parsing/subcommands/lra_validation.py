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


def build_prepare_lra_observation_uncertainty_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Declare counting effort separately from held-out observations."""
    parser = subparsers.add_parser(
        "prepare-lra-observation-uncertainty",
        help="Attach conditional pollen draws to frozen withheld-site predictions.",
    )
    parser.add_argument(
        "predictions", type=Path, help="Saved withheld-site prediction product."
    )
    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="Frozen counting plan with prediction and evidence hashes.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        required=True,
        help="Root containing declared counting-design evidence.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New conditional uncertainty product directory.",
    )
    return parser


def build_score_lra_observation_coverage_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Pin saved uncertainty and scores before marginal coverage evaluation."""
    parser = subparsers.add_parser(
        "score-lra-observation-coverage",
        help="Score separate per-taxon conditional pollen coverage.",
    )
    parser.add_argument(
        "predictions", type=Path, help="Saved withheld-site prediction product."
    )
    parser.add_argument(
        "--uncertainty",
        type=Path,
        required=True,
        help="Saved conditional uncertainty product.",
    )
    parser.add_argument(
        "--scores",
        type=Path,
        required=True,
        help="Saved held-out observation score product.",
    )
    parser.add_argument(
        "--expected-uncertainty-sha256",
        required=True,
        help="Retained uncertainty manifest SHA-256.",
    )
    parser.add_argument(
        "--expected-scores-sha256",
        required=True,
        help="Retained score manifest SHA-256.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New marginal coverage product directory.",
    )
    return parser
