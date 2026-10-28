"""Qualify an affine identifiability family against unchanged conditional LOVE captures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from ..authority import DESCRIPTOR
from ..sources import load_inputs
from ..summary import summarize
from .algebra import affine_family, forward_and_jacobian, require
from .independent import review

PROTOCOL = Path(
    "reports/science/swedish-conditional-love-identifiability/protocol.json"
)
BASE = Path("docs/report/pollen-reconstruction/swedish-conditional-love")


def pin(path: Path) -> dict[str, Any]:
    """Describe the bytes and digest of a declared source input."""
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def require_writer_correspondence(
    historical: dict[str, str], current: dict[str, str], contract: dict[str, Any]
) -> None:
    """Bind retained historical writers and separately reviewed current helper bytes."""
    require(
        historical == contract["historical_writer_module_sha256"],
        "Historical writer source identity changed",
    )
    require(
        current == contract["qualified_current_writer_module_sha256"],
        "Qualified current writer source identity changed",
    )
    changes = {name for name in historical if historical[name] != current.get(name)}
    require(
        set(historical)
        == set(current)
        == {
            "__init__.py",
            "__main__.py",
            "authority.py",
            "producer.py",
            "sources.py",
            "summary.py",
        }
        and changes == {"producer.py", "sources.py", "summary.py"},
        "Reviewed writer source correspondence differs",
    )
    rows = contract["reviewed_deltas"]
    require(
        len(rows) == 3
        and {Path(row["path"]).name for row in rows} == changes
        and all(
            row["original_sha256"] == historical[Path(row["path"]).name]
            and row["reviewed_sha256"] == current[Path(row["path"]).name]
            for row in rows
        ),
        "Specific reviewed writer source identities differ",
    )


def qualify(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Keep one input inside its declared conditional identifiability scope."""
    repository = repository.resolve(strict=True)
    # Check the lexical route before normalization can hide a symlink before '..'.
    lexical = output if output.is_absolute() else Path.cwd() / output
    require(
        not any(parent.is_symlink() for parent in (lexical, *lexical.parents)),
        "Artifact output symlink ancestors are refused",
    )
    output = Path(os.path.abspath(lexical))
    require(
        not output.exists()
        and output != repository / "artifacts"
        and output.is_relative_to(repository / "artifacts"),
        "An absent repository artifact output is required",
    )
    protocol = json.loads((repository / PROTOCOL).read_text())
    values, before = load_inputs(repository, source_root, Path(DESCRIPTOR))
    original = summarize(values)
    require(
        json.loads((repository / BASE / "report.json").read_text()) == original,
        "Original scientific report changed",
    )
    proof = json.loads((repository / BASE / "source-proof.json").read_text())
    parent = Path(__file__).resolve().parents[1]
    require_writer_correspondence(
        proof["actual_writer_module_sha256"],
        {p.name: pin(p)["sha256"] for p in sorted(parent.glob("*.py"))},
        protocol["writer_source_correspondence"],
    )
    captured = values["three-conditional-love-cases.json"]
    ppe = captured["ppe"]
    local = captured["raw_local_panel_counts"]
    training = captured["regional_training_counts"]
    factors = captured["training_whole_factors"]
    require(
        local == protocol["support"]["local_panel_counts"]
        and training == protocol["support"]["regional_panel_counts"],
        "Fixed native counts changed",
    )
    U = [
        sum(n[i] / (k[i] * ppe[i]) for n, k in zip(training, factors, strict=True))
        for i in range(2)
    ]
    regional = [x / sum(U) for x in U]
    q = (local[0] / sum(local), local[1] / sum(local))
    a = tuple(captured["local_factors"][i] * ppe[i] for i in range(2))
    c = tuple(captured["regional_factors"][i] * ppe[i] * regional[i] for i in range(2))
    family = affine_family(q, (a[0], a[1]), (c[0], c[1]))
    if family.upper_ratio is None:
        raise ValueError("Native source unexpectedly has an unbounded ratio domain")
    require(
        0.5 < family.upper_ratio < 1,
        "Native ratio feasibility orientation changed",
    )
    upper = family.upper_ratio
    points = []
    named = [
        ("zero_background_limit", 0.0),
        ("quarter_feasible_upper", upper / 4),
        ("half_feasible_upper", upper / 2),
        ("three_quarter_feasible_upper", upper * 3 / 4),
        ("feasible_upper_binary64", upper),
        ("original_half_ratio", 0.5),
        ("original_equal_ratio", 1.0),
        ("original_double_ratio", 2.0),
    ]
    for name, ratio in named:
        cover = family.evaluate(ratio)
        forward, J = forward_and_jacobian(family, ratio)
        points.append(
            {
                "id": name,
                "ratio": ratio,
                "signed_cover": list(cover),
                "binary64_simplex_feasible": all(0 <= x <= 1 for x in cover),
                "closed_forward_pollen": list(forward),
                "response_jacobian": [list(x) for x in J],
                "null_direction": [family.slope[0], 1.0],
                "null_direction_residual": J[0][0] * family.slope[0] + J[0][1],
                "determinant": J[0][0] * J[1][1] - J[0][1] * J[1][0],
            }
        )
    cases = []
    for old in captured["cases"]:
        ratio = old["scenario"]["lambda"]
        new = family.evaluate(ratio)
        require(
            max(abs(x - y) for x, y in zip(new, old["cover"], strict=True)) <= 2e-13,
            "Saved signed case orientation or value differs",
        )
        cases.append(
            {
                "ratio": ratio,
                "original_cover": old["cover"],
                "recomputed_cover": list(new),
                "original_simplex_feasible": old["simplex_feasible"],
                "original_maintained_forward_status": old["maintained_forward"][
                    "status"
                ],
            }
        )
    actual = {
        "pollen": list(q),
        "regional_cover": regional,
        "local_response": list(a),
        "unit_background": list(c),
        "intercept": list(family.intercept),
        "slope": list(family.slope),
        "nonnegative_ratio_domain": {
            "lower": 0.0,
            "lower_closed": True,
            "upper": upper,
            "upper_closed": True,
            "unbounded": False,
        },
        "positive_ratio_domain": {
            "lower": 0.0,
            "lower_closed": False,
            "upper": upper,
            "upper_closed": True,
            "empty": False,
        },
        "points": points,
        "original_case_comparisons": cases,
    }
    oracle = review(values, actual)
    result = {
        "schema_version": "swedish-conditional-love-identifiability.v1",
        "protocol_sha256": pin(repository / PROTOCOL)["sha256"],
        "source_capture_sha256": proof["original_capture_sha256"],
        "writer_source_correspondence": protocol["writer_source_correspondence"],
        "original_report": pin(repository / BASE / "report.json"),
        "original_source_proof": pin(repository / BASE / "source-proof.json"),
        "support": protocol["support"],
        "physical_inputs": protocol["physical_inputs"],
        "original_execution_scope": {
            "overall_model_status": original["original_model_job_status"],
            "model_stage_native_exit": original["original_model_stage_native_exit"],
            "oracle_only_plan_sha256": original["oracle_only_plan_sha256"],
        },
        "conditional_family": actual,
        "independent_oracle": oracle,
        "inference": "The abundance ratio and local composition are not jointly identifiable from this fixed closed two-taxon observation. Every member of the feasible family has the same pollen response; no ratio is selected, fitted or assigned a probability.",
        "scientific_limits": protocol["publication_limits"],
        "new_engine_model_calls": 0,
        "new_quadrature_calls": 0,
        "new_source_acquisition_calls": 0,
        "original_covariance_products_unchanged": True,
    }
    _, after = load_inputs(repository, source_root, Path(DESCRIPTOR))
    require(before == after, "Source custody changed")
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    (output / "independent-audit.json").write_text(
        json.dumps(oracle, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result


def main() -> int:
    """Write the conditional identifiability comparison and its source context."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.repository, args.source_root, args.output)
    print(
        json.dumps(
            {
                "status": "passed",
                "points": len(result["conditional_family"]["points"]),
                "scalar_checks": result["independent_oracle"]["scalar_checks"],
                "new_model_calls": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
