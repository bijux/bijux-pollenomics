"""Compare complete diagnostic outputs to original governed scalar values."""

import argparse
import hashlib
import json
from pathlib import Path

from contracts import refusal_contract, typed_equal
from storage import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    output = Path(plan["output"])
    original = {}
    observed = {}
    for label, row in plan["original_reports"].items():
        before = Path(row["path"])
        assert hashlib.sha256(before.read_bytes()).hexdigest() == row["sha256"]
        original[label] = json.loads(before.read_bytes())
        observed[label] = json.loads((output / (label + ".json")).read_bytes())
        typed_equal(observed[label], original[label])
    refusal_contract(observed["gradient"], observed["finite"])
    baseline = json.loads(Path(plan["gradient_baseline"]["path"]).read_bytes())
    assert baseline["experiment_sha256"] == observed["gradient"]["experiment_sha256"]
    for item in observed["gradient"]["items"]:
        declared = baseline["items"][item["item_id"]]
        assert item["request_sha256"] == declared["request_sha256"]
        for index, ring in enumerate(item["rings"]):
            typed_equal(ring["baseline"], declared["rings"][index])
    assert (
        observed["finite"]["request_sha256"]
        == "bf99b6d8add47095749b1770a0e62a575c1f90217af2c477f36525ddd0a5d69c"
    )
    for row in plan["input_pins"]:
        path = Path(row["path"])
        assert (
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size == row["bytes"]
        )
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
    receipt = {
        "candidate": plan["candidate"],
        "all_complete_diagnostic_typed_values_exact": True,
        "all_original_baselines_and_refusals_exact": True,
        "retained_input_producer": plan["qualified_input_epoch"],
        "actual_diagnostic_optimizers_run": True,
        "full_experiment_fit_or_new_prediction_executed": False,
        "R_executed": False,
        "held_out_prediction_count": 0,
        "scientific_or_official_release_acceptance": False,
        "scope": "Two unchanged bounded prior-exposed English development diagnostics only. Three declared training items/two rings and one finite-candidate pair; historical negative convergence is preserved. Any numeric or type difference is a hard refusal, never regenerated into a new expectation.",
    }
    write_json(output, output / "independent-diagnostic-review.json", receipt)
    print(
        json.dumps(
            {
                "actual_exit": 0,
                "typed_reports": 2,
                "convergence_refusals_preserved": True,
            }
        )
    )


if __name__ == "__main__":
    main()
