"""Publish the maintained Python account of the original retained R reference."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, load_policy
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.original_r_reference import (
    validated_original_r_reference,
)
from bijux_pollenomics_dev.lra_validation import reference_replay
from bijux_pollenomics_dev.source_completion.publication.json_outputs import (
    publish_json_outputs,
)

BUNDLE = Path("docs/report/method-certification/original-r-reference/reference-bundle")
SOURCE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/"
    "method_certification/original_r_account.py"
)
POLICY = Path("configs/ci/reproducible-report-build.json")
ORIGINAL_SOURCE = "56997bbcfb5fcf7088035a16080b6a9416acc6e5"
Snapshot = tuple[tuple[InventoryEntry, ...], dict[str, str], str]
PROSPECTIVE = Path(
    "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/optimized_prospective.json"
)
PROSPECTIVE_VARIANTS = (
    ("intermediates", "LOVEoptim"),
    ("taxon_axis", "LOVEoptim"),
    ("ring_axis", "LOVEoptim"),
    ("wrapper_replay", "LOVEoptim"),
    ("nonfinite_objective", "tf"),
    ("all_nonfinite_refusal", "LOVEoptim"),
)


def _populations(
    repository: Path, hashes: dict[str, str]
) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    """Read returned identities and the maintained prospective case declaration."""
    core = json.loads((repository / BUNDLE / "oracle/case_manifest.json").read_bytes())
    domains = json.loads(
        (repository / BUNDLE / "source-domains/case_manifest.json").read_bytes()
    )
    prospective = repository / PROSPECTIVE
    if prospective.resolve(strict=True) != prospective or hashlib.sha256(
        prospective.read_bytes()
    ).hexdigest() != hashes.get(str(PROSPECTIVE)):
        raise ValueError("Original R prospective declaration source differs")
    declaration = json.loads(prospective.read_bytes())
    identities = [row["id"] for row in declaration["cases"]]
    if (
        len(identities) != 3
        or any(type(name) is not str or not name for name in identities)
        or len(set(identities)) != 3
    ):
        raise ValueError("Original R prospective declaration identities differ")
    returned: list[tuple[str, ...]] = [
        ("source-compatible-core", row["id"], row["name"], row["api"], row["mode"])
        for row in core
    ] + [
        ("source-domains-and-corrected-forward", row["id"], row["semantics"])
        for row in domains
    ]
    # These six views are the unchanged add(...) variants in lra_oracle.cases.
    # Native case IDs come from the authenticated declaration, never report rows.
    unavailable: list[tuple[str, ...]] = [
        (f"{name}_{suffix}", api, "no_result_in_original_R_bundle")
        for name in identities
        for suffix, api in PROSPECTIVE_VARIANTS
    ]
    if len(core) != 25 or len(domains) != 23 or len(set(returned)) != 48:
        raise ValueError("Original R returned manifest identities differ")
    return returned, unavailable


def _snapshot(repository: Path) -> Snapshot:
    """Authenticate the complete retained reference and actual source origins."""
    source = repository / SOURCE
    if source.resolve(strict=True) != source or Path(__file__).resolve() != source:
        raise ValueError("Original R account must use the selected repository source")
    # Load LRA before the oracle's source-path insertion, then verify every loaded
    # LRA module against the source closure. Configured owners use repository code.
    importlib.import_module("bijux_pollenomics_lra.api")
    hashes = reference_replay._replay_source_hashes(repository)
    prefix = Path("packages/bijux-pollenomics-lra/src")
    for name, module in tuple(sys.modules.items()):
        if name.split(".")[0] != "bijux_pollenomics_lra":
            continue
        expected = repository / prefix / (name.replace(".", "/") + ".py")
        if name == "bijux_pollenomics_lra" or hasattr(module, "__path__"):
            expected = expected.with_suffix("") / "__init__.py"
        actual = Path(getattr(module, "__file__", "")).absolute()
        if actual != expected or actual.resolve(strict=True) != expected:
            raise ValueError("Original R account LRA source origin differs: " + name)
        relative = expected.relative_to(repository).as_posix()
        if hashlib.sha256(actual.read_bytes()).hexdigest() != hashes.get(relative):
            raise ValueError("Original R account LRA source bytes differ: " + name)
    retained = validated_original_r_reference(
        repository, load_policy(repository / POLICY)
    )
    return retained, hashes, hashlib.sha256(source.read_bytes()).hexdigest()


def _require_account(
    report: dict[str, Any], hashes: dict[str, str], repository: Path
) -> None:
    """Keep the original 48 returned vectors and 18 unavailable cases explicit."""
    cases = report.get("cases")
    missing = report.get("current_core_cases_without_retained_R")
    counts = {
        "attempted_cases": 66,
        "evaluated_cases": 48,
        "passed_cases": 48,
        "failed_cases": 0,
        "refused_cases": 18,
    }
    if (
        report.get("schema_version") != "retained-r-python-replay.1"
        or report.get("status") != "passed"
        or report.get("fresh_R_executed") is not False
        or report.get("original_R_executed") is not True
        or report.get("release_certificate") is not False
        or report.get("original_source_commit") != ORIGINAL_SOURCE
        or report.get("original_certificate_sha256")
        != reference_replay.CERTIFICATE_SHA256
        or report.get("current_inputs_sha256") != hashes
        or any(
            type(report.get(key)) is not int or report[key] != n
            for key, n in counts.items()
        )
        or not isinstance(cases, list)
        or len(cases) != 48
        or any(
            not isinstance(row, dict) or row.get("status") != "passed" for row in cases
        )
        or Counter(row.get("profile") for row in cases)
        != {"source-compatible-core": 25, "source-domains-and-corrected-forward": 23}
        or len({(row.get("profile"), row.get("id")) for row in cases}) != 48
        or not isinstance(missing, list)
        or len(missing) != 18
        or any(
            not isinstance(row, dict)
            or row.get("reason") != "no_result_in_original_R_bundle"
            for row in missing
        )
    ):
        raise ValueError("Original R account scope or actual comparison differs")
    expected_cases, expected_missing = _populations(repository, hashes)
    actual_cases = []
    for row in cases:
        keys = (
            ("profile", "id", "name", "api", "mode")
            if row["profile"] == "source-compatible-core"
            else ("profile", "id", "semantics")
        )
        if any(type(row.get(key)) is not str for key in keys):
            raise ValueError("Original R returned identity fields differ")
        actual_cases.append(tuple(row[key] for key in keys))
    actual_missing = []
    for row in missing:
        keys = ("name", "api", "reason")
        if any(type(row.get(key)) is not str for key in keys):
            raise ValueError("Original R unavailable identity fields differ")
        actual_missing.append(tuple(row[key] for key in keys))
    if Counter(actual_cases) != Counter(expected_cases) or Counter(
        actual_missing
    ) != Counter(expected_missing):
        raise ValueError("Original R exact returned or unavailable population differs")


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Retain the complete replay stage and expose only a reauthenticated report."""
    repository = repository.absolute()
    if repository.resolve(strict=True) != repository:
        raise ValueError("Original R account repository must be a real directory")
    output = require_absent_artifact_output(repository, output)
    stage_parent = output.parent.parent
    if not stage_parent.is_relative_to(repository / "artifacts"):
        raise ValueError("Original R account needs an artifact evidence directory")
    inputs = _snapshot(repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.original-r-account-", dir=stage_parent)
    )
    # Keep generated CSV fixtures and the genuine producer report outside the
    # mapped owner output. Failure evidence remains available for inspection.
    comparison = stage / "comparison"
    report = reference_replay.replay(repository, repository / BUNDLE, comparison)
    _require_account(report, inputs[1], repository)
    actual = comparison / "report.json"
    if (
        actual.resolve(strict=True) != actual
        or json.loads(actual.read_bytes()) != report
    ):
        raise ValueError(
            "Original R account producer report differs from returned result"
        )
    if _snapshot(repository) != inputs:
        raise ValueError("Original R account source or retained reference changed")
    publish_json_outputs([(output / "report.json", report)])
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the original retained-reference account at an absent artifact output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    publish(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
