"""Execute one stage of the partitioned reproducible-report build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .contracts import ReportRebuildError
from .workflow import (
    assemble_partition_lane,
    build_partition,
    build_partition_plan,
    verify_partitioned_rebuild,
)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan")
    _common(plan)
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--github-output", type=Path)

    build = commands.add_parser("build")
    _common(build)
    build.add_argument("--plan", type=Path, required=True)
    build.add_argument("--lane", choices=("reference", "replay"), required=True)
    build.add_argument("--partition-id", required=True)
    build.add_argument("--evidence-root", type=Path, required=True)
    build.add_argument("--scope-artifacts-root", type=Path)

    assemble = commands.add_parser("assemble")
    _common(assemble)
    assemble.add_argument("--plan", type=Path, required=True)
    assemble.add_argument("--lane", choices=("reference", "replay"), required=True)
    assemble.add_argument("--partition-artifacts-root", type=Path, required=True)
    assemble.add_argument("--evidence-root", type=Path, required=True)

    verify = commands.add_parser("verify")
    _common(verify)
    verify.add_argument("--plan", type=Path, required=True)
    verify.add_argument("--reference-manifest", type=Path, required=True)
    verify.add_argument("--replay-manifest", type=Path, required=True)
    verify.add_argument("--evidence-root", type=Path, required=True)
    return parser


def _write_github_outputs(path: Path, report: dict[str, object]) -> None:
    scope_ids = report["scope_partition_ids"]
    partition_ids = report["partition_ids"]
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"scope_partitions={json.dumps(scope_ids, separators=(',', ':'))}\n"
        )
        handle.write(f"partitions={json.dumps(partition_ids, separators=(',', ':'))}\n")


def main(argv: list[str] | None = None) -> int:
    """Run the selected rebuild stage."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            report = build_partition_plan(
                repo_root=args.repo_root,
                policy_path=args.policy,
                output_path=args.output,
            )
            if args.github_output is not None:
                _write_github_outputs(args.github_output, report)
        elif args.command == "build":
            build_partition(
                repo_root=args.repo_root,
                policy_path=args.policy,
                plan_path=args.plan,
                lane=args.lane,
                partition_id=args.partition_id,
                evidence_root=args.evidence_root,
                scope_artifacts_root=args.scope_artifacts_root,
            )
        elif args.command == "assemble":
            assemble_partition_lane(
                repo_root=args.repo_root,
                policy_path=args.policy,
                plan_path=args.plan,
                lane=args.lane,
                partition_artifacts_root=args.partition_artifacts_root,
                evidence_root=args.evidence_root,
            )
        else:
            report = verify_partitioned_rebuild(
                repo_root=args.repo_root,
                policy_path=args.policy,
                plan_path=args.plan,
                reference_manifest_path=args.reference_manifest,
                replay_manifest_path=args.replay_manifest,
                evidence_root=args.evidence_root,
            )
            return 0 if report["status"] == "PASS" else 1
    except ReportRebuildError as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
