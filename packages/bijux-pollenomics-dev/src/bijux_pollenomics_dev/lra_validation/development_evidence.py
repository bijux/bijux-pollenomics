"""Read the immutable exposed-English audit packet without running experiments."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

PACKET = Path("data/model-development/english-retained-score-audit")
PACKET_SHA256 = "4a7542e19ba5503ededfa5a8536283e4e23d847418f9962e1b4bc42e9b8b05bb"


def _regular(path: Path, root: Path) -> bytes:
    if (
        not path.resolve().is_relative_to(root.resolve())
        or path.is_symlink()
        or not path.is_file()
    ):
        raise ValueError("development_evidence_not_regular_owned_file")
    if any(
        parent.is_symlink()
        for parent in path.parents
        if parent != root and parent.is_relative_to(root)
    ):
        raise ValueError("development_evidence_symlink_ancestor")
    return path.read_bytes()


def build_development_evidence(repository: Path) -> dict[str, Any]:
    """Retain every fresh audit terminal and every historical bin outcome."""
    root = repository / PACKET
    manifest_bytes = _regular(root / "manifest.json", root)
    if hashlib.sha256(manifest_bytes).hexdigest() != PACKET_SHA256:
        raise ValueError("development_evidence_manifest_changed")
    manifest = json.loads(manifest_bytes)
    inputs: dict[str, bytes] = {}
    for name, identity in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("development_evidence_path_escape")
        raw = _regular(root / relative, root)
        if (
            len(raw) != identity["bytes"]
            or hashlib.sha256(raw).hexdigest() != identity["sha256"]
        ):
            raise ValueError("development_evidence_member_changed")
        inputs[name] = raw
    original_rows = []
    fresh = []
    for identity in manifest["fresh_attempt_ids"]:
        start_envelope = json.loads(inputs[f"ledger/{identity}/start.json"])
        result_envelope = json.loads(inputs[f"ledger/{identity}/result.json"])
        diagnostics = json.loads(inputs[f"audits/{identity}.json"])
        start = start_envelope["payload"]
        result = result_envelope["payload"]
        if start["run_id"] != identity or diagnostics["fresh_attempt_id"] != identity:
            raise ValueError("development_evidence_attempt_identity_changed")
        original_rows.extend(diagnostics["original_attempts"])
        fresh.append(
            {
                "attempt_id": identity,
                "historical_candidate_id": diagnostics["historical_candidate_id"],
                "fold_id": diagnostics["fold_id"],
                "terminal": result,
                "original_attempt_count": diagnostics["original_attempt_count"],
                "original_status_counts": diagnostics["original_status_counts"],
                "original_refusal_reason_counts": diagnostics[
                    "original_refusal_reason_counts"
                ],
                "independent_score_check": diagnostics["independent_score_check"],
                "common_scored_bins": diagnostics["common_scored_bins"],
                "common_scored_sites": diagnostics["common_scored_sites"],
            }
        )
    custody = json.loads(inputs["execution-custody.json"])
    failed = []
    for identity in manifest["failed_runtime_attempt_ids"]:
        start = json.loads(inputs[f"failed-runtime/ledger/{identity}/start.json"])[
            "payload"
        ]
        result = json.loads(inputs[f"failed-runtime/ledger/{identity}/result.json"])[
            "payload"
        ]
        if start["run_id"] != identity or result["status"] != "failed":
            raise ValueError("development_evidence_failed_runtime_attempt_changed")
        failed.append(
            {
                "attempt_id": identity,
                "terminal": result,
                "operation": "declared_audit_failed_before_score_consumption",
            }
        )
    if custody["native_exit"] != 0 or custody["pins_unchanged"] is not True:
        raise ValueError("development_evidence_execution_incomplete")
    return {
        "schema_version": "english-prior-exposed-development-evidence.v1",
        "packet_manifest_sha256": PACKET_SHA256,
        "source_candidate": manifest["source_candidate"],
        "fresh_operation": "retained_score_audit_without_refitting",
        "frozen_development_design": json.loads(inputs["frozen/design.json"]),
        "development_cohort": json.loads(inputs["frozen/development-cohort.json"]),
        "target_support": json.loads(inputs["frozen/scope.json"]),
        "splits": json.loads(inputs["frozen/split-manifest.json"]),
        "selection_policy": json.loads(inputs["frozen/selection-policy.json"]),
        "historical_completed_design": json.loads(
            inputs["frozen/historical-design.json"]
        ),
        "fresh_audit_attempts": fresh,
        "failed_runtime_attempts": failed,
        "all_fresh_execution_counts": {
            "attempted": len(fresh) + len(failed),
            "completed_audit": len(fresh),
            "failed_before_audit": len(failed),
        },
        "fresh_terminal_counts": dict(
            Counter(row["terminal"]["status"] for row in fresh)
        ),
        "original_attempts": sorted(
            original_rows,
            key=lambda row: (
                row["candidate_id"],
                row["fold_id"],
                row["target_site_id"],
                row["bin_id_bp"],
            ),
        ),
        "original_status_counts": dict(Counter(row["status"] for row in original_rows)),
        "original_refusal_reason_counts": dict(
            Counter(
                row["reason"] for row in original_rows if row["status"] == "refused"
            )
        ),
        "execution_custody": custody,
        "claims": {
            "fresh_audit_reserved_before_consumption": True,
            "original_outcomes_previously_exposed": True,
            "historical_search_prospectively_frozen_by_this_packet": False,
            "fresh_model_fit_or_parameter_sweep": False,
            "untouched_test_or_empirical_vegetation_accuracy": False,
            "ecological_or_release_certification": False,
        },
    }


def main() -> int:
    """Write one deterministic retained account to an absent output destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_development_evidence(args.repository)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        stream.write(
            json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
