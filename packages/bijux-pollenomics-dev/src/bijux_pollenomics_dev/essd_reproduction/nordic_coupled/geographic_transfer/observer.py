"""Independent source, geographic-role and cached-ensemble readback."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.inputs import decode
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    code_state,
    reopen,
    resources,
    write,
)

from .inputs import check_sources
from .verification import (
    audit_admission,
    audit_candidate,
    audit_scoring,
    bind_projection,
)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent geographic transfer readback: " + message)


def observe(
    repository: Path, protocol_path: Path, products: Path, output: Path
) -> dict[str, Any]:
    """Authenticate the new freeze before original observation and numerical audit."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    products = products.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    state = code_state(repository)
    raw_result = (products / "result.json").read_bytes()
    result = decode(raw_result)
    _require(
        result["source_commit"] == state["head"]
        and result["index_sha256"] == state["index_sha256"]
        and result["protocol_sha256"] == hashlib.sha256(raw_protocol).hexdigest()
        and result["source_guards_passed"] is True,
        "new producer epoch",
    )
    frozen = reopen(products, result["prediction_manifest"])
    pins = result["products"]
    _require(
        frozen["schema_version"] == "krageholm-geographic-transfer-freeze.v1"
        and frozen["files"]
        == {
            key: pins[key]
            for key in ("inputs", "admission", "nominal_handoff", "predictions")
        }
        and frozen["scoring_roles_opened"] == 0,
        "authenticated new prediction member bindings",
    )
    closed = {key: reopen(products, pin) for key, pin in pins.items()}
    packet, admission = closed["inputs"], closed["admission"]
    counts, source_facts = bind_projection(repository, protocol, packet)
    geography = audit_admission(packet, admission, protocol["geography"])
    roles = {role["case_id"]: role for role in admission["roles"]}
    candidates = {row["case"]["case_id"]: row for row in packet["candidate_cases"]}
    indexed = {
        (row["case_id"], row["length_scale_km"]): row for row in closed["predictions"]
    }
    scored = {(row["case_id"], row["length_scale_km"]): row for row in closed["scores"]}
    expected = {(case, scale) for case in roles for scale in (20.0, 100.0)}
    _require(
        len(indexed)
        == len(closed["predictions"])
        == len(scored)
        == len(closed["scores"])
        == 6
        and set(indexed) == set(scored) == expected,
        "all six geographic sensitivity roles",
    )
    handoff = {row["case_id"]: row for row in closed["nominal_handoff"]}
    _require(
        set(handoff)
        == {key for key, role in roles.items() if role["status"] == "admitted"}
        and all(
            row["passed"] is True
            and row["methods"]
            == row["cover_comparisons"]
            == row["pollen_comparisons"]
            == 3
            and row["failures"] == []
            for row in handoff.values()
        ),
        "complete successful nominal handoff",
    )
    numerical, scoring = [], []
    for key in sorted(expected):
        row, score, role = indexed[key], scored[key], roles[key[0]]
        _require(
            row["target_id"] == score["target_id"] == role["target_id"]
            and row["admission_status"] == role["status"],
            "forecast target and block role",
        )
        if role["status"] == "refused":
            _require(
                row["prediction"] is None
                and row["refusal"] == role["reason"]
                and score
                == {
                    "case_id": row["case_id"],
                    "target_id": row["target_id"],
                    "length_scale_km": row["length_scale_km"],
                    "status": "not_executed_geographic_refusal",
                    "reason": role["reason"],
                },
                "no reuse of forbidden old forecasts",
            )
            continue
        _require(
            row["refusal"] is None
            and score["status"] == "evaluated_admitted_observation",
            "admitted candidate evaluation disposition",
        )
        candidate = candidates[key[0]]
        numerical.append(audit_candidate(candidate, row["prediction"]))
        scoring.append(
            audit_scoring(
                candidate,
                row["prediction"],
                {name: value for name, value in score.items() if name != "status"},
                counts[role["target_id"]],
            )
        )
    refs = {row["target_id"]: row for row in packet["observation_refs"]}
    access = [
        {
            "target_id": role["target_id"],
            "role": "scoring_after_new_prediction_readback",
            "prediction_freeze_sha256": result["prediction_manifest"]["sha256"],
            "raw_reference": refs[role["target_id"]]["raw"],
            "scope": "previously_exposed_role_specific_access_not_globally_unread",
        }
        for role in admission["roles"]
        if role["status"] == "admitted"
    ]
    _require(
        closed["observation_access"] == access,
        "only admitted target scoring-role reads",
    )
    check_sources(repository, packet)
    for pin in (*pins.values(), result["prediction_manifest"]):
        reopen(products, pin)
    _require(
        protocol_path.read_bytes() == raw_protocol
        and (products / "result.json").read_bytes() == raw_result
        and code_state(repository) == state,
        "source, products, protocol, HEAD or index changed",
    )
    output.mkdir()
    facts = {
        "schema_version": "krageholm-geographic-transfer-verification.v1",
        "status": "verified",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "source_observation": source_facts,
        "geographic_observation": geography,
        "numerical_observation": numerical,
        "scoring_observation": scoring,
        "role_accesses_verified": len(access),
        "resources": resources(started, output, protocol["limits"], observer=True),
    }
    write(output, "verification.json", facts, protocol["limits"]["max_output_bytes"])
    resources(started, output, protocol["limits"], observer=True)
    return facts


def main() -> None:
    """Audit one new geography-admitted retained-draw projection."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "protocol", "products", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.repository, args.protocol, args.products, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
