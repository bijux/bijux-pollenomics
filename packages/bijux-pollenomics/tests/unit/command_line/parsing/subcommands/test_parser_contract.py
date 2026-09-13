"""Ordered argparse contracts for every CLI subcommand."""

from __future__ import annotations

import argparse
import hashlib

from bijux_pollenomics.command_line.parsing import build_parser

_COMMAND_ACTIONS = {
    "adna-archive-projects": ["help", "species", "json"],
    "adna-artifact-plan": ["help", "species", "json"],
    "adna-curation-manifest": ["help", "species", "json"],
    "adna-domestication-coverage": ["help", "json"],
    "adna-layout": ["help", "species", "json"],
    "adna-release-bar": ["help", "json"],
    "adna-release-readiness": ["help", "species", "json"],
    "adna-normalization-bundle": ["help", "species", "json"],
    "adna-runtime-manifest": ["help", "species", "version", "json"],
    "adna-species": ["help", "json"],
    "adna-species-review": ["help", "species", "json"],
    "refresh-animal-adna-foundation": [
        "help",
        "data_root",
        "aadr_root",
        "output_root",
        "context_root",
        "version",
        "countries",
        "species",
    ],
    "report-country": [
        "help",
        "country",
        "aadr_root",
        "version",
        "output_root",
        "context_root",
        "shared_map_label",
        "shared_map_path",
    ],
    "report-multi-country-map": [
        "help",
        "countries",
        "name",
        "title",
        "aadr_root",
        "version",
        "output_root",
        "context_root",
    ],
    "publish-reports": [
        "help",
        "countries",
        "name",
        "title",
        "aadr_root",
        "version",
        "output_root",
        "published_output_root",
        "context_root",
    ],
    "collect-data": ["help", "sources", "version", "output_root"],
    "validate-lra-input": ["help", "request", "input_root"],
    "run-lra": ["help", "request", "input_root", "output"],
    "run-joint-lra": ["help", "request", "input_root", "output", "cache_root"],
    "run-lra-batch": [
        "help",
        "request",
        "input_root",
        "cache_root",
        "report_root",
        "max_workers",
        "max_items",
    ],
    "render-lra-report": [
        "help",
        "product",
        "expected_manifest_sha256",
        "geometry",
        "expected_geometry_sha256",
        "output",
        "temporal_profile",
    ],
    "prepare-lra-experiment": [
        "help",
        "request",
        "input_root",
        "cache_root",
        "output",
        "max_workers",
    ],
    "score-lra-experiment": [
        "help",
        "product",
        "expected_manifest_sha256",
        "outcome_root",
        "outcome_inventory",
        "output",
    ],
    "prepare-lra-observation-uncertainty": [
        "help",
        "predictions",
        "plan",
        "evidence_root",
        "output",
    ],
    "score-lra-observation-coverage": [
        "help",
        "predictions",
        "uncertainty",
        "scores",
        "expected_uncertainty_sha256",
        "expected_scores_sha256",
        "output",
    ],
    "refresh-aadr-source-accountability": ["help", "data_root", "version"],
    "refresh-data-contract-surfaces": ["help", "data_root", "version"],
    "surface-map": ["help", "json"],
    "product-scope": ["help", "json"],
    "ownership-map": ["help", "json"],
    "source-support": ["help", "json"],
    "validate-collection-summary": ["help", "summary_path"],
}


def _subparsers_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction[argparse.ArgumentParser]:
    return next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )


def test_subcommands_and_actions_retain_exact_order() -> None:
    action = _subparsers_action(build_parser())
    actual = {
        name: [child_action.dest for child_action in parser._actions]
        for name, parser in action.choices.items()
    }
    assert actual == _COMMAND_ACTIONS


def test_root_and_subcommand_help_text_is_frozen() -> None:
    parser = build_parser()
    action = _subparsers_action(parser)
    root_digest = hashlib.sha256(parser.format_help().encode()).hexdigest()
    subcommand_help = "".join(child.format_help() for child in action.choices.values())
    assert (
        root_digest
        == "e89502483371136a0a938ca63679b259f653962209f83f95fa343f0ced4c3522"
    )
    assert hashlib.sha256(subcommand_help.encode()).hexdigest() == (
        "1e6ca36ccc2a97ecaa2ff69f93ce948b9eaf3a24877bec5a297b941eeda0bd57"
    )
