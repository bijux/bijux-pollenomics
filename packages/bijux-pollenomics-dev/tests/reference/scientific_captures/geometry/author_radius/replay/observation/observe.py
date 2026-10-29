"""Independently join the radius comparison to the genuine complete source run."""

import argparse
import hashlib
import json
from pathlib import Path

from contracts import qualify_outputs, validate_pin_population
from custody import authenticate, regular, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    original = authenticate()
    assert (
        original["current_scientific_source_projection"]
        == plan["qualified_original_source_projection"]
    )
    validate_pin_population(original["pins"], plan["qualified_original_current_pins"])
    out = Path(plan["output"])
    frozen_path = out / "frozen/predictions.json"
    score_path = out / "scored/report.json"
    csv_path = out / "scored/scores.csv"
    assert {
        p.relative_to(out).as_posix()
        for d in [out / "frozen", out / "scored"]
        for p in d.rglob("*")
        if p.is_file()
    } == {"frozen/predictions.json", "scored/report.json", "scored/scores.csv"}
    for root in [out / "frozen", out / "scored"]:
        assert not any(p.is_symlink() for p in (root, *root.rglob("*")))
    historical = plan["historical_outputs"]
    for row in historical.values():
        assert regular(Path(row["path"])) == row
    expected_source = {
        "producer_sha256": sha(Path(plan["producer"])),
        "experiment_sha256": sha(Path(plan["inputs"]) / "experiment.json"),
        "source_report_sha256": sha(Path(plan["inputs"]) / "source-report.json"),
        "prediction_manifest_sha256": sha(Path(plan["predictions"]) / "manifest.json"),
        "predictions_sha256": sha(Path(plan["predictions"]) / "predictions.json"),
        "preparations_sha256": sha(Path(plan["predictions"]) / "preparations.json"),
    }
    assert expected_source == plan["expected_source"]
    review = qualify_outputs(
        json.loads(frozen_path.read_bytes()),
        json.loads(score_path.read_bytes()),
        csv_path.read_bytes(),
        json.loads(Path(historical["frozen"]["path"]).read_bytes()),
        json.loads(Path(historical["report"]["path"]).read_bytes()),
        Path(historical["scores"]["path"]).read_bytes(),
        expected_source,
        json.loads((Path(plan["predictions"]) / "predictions.json").read_bytes()),
        sha(frozen_path),
    )
    review.update(
        candidate=plan["candidate"],
        source_execution_candidate="22c6e480ba4690cc508202925a8773afe95ab36e",
        original_plan_sha256="7a75256e79a577280d8bd828380ebb8438b80914e3aa8c5ddc390fa428e6428c",
        original_outer_terminal_sha256="c4ab7b6a50c989cd646454ae2b52020df2bbdc749a4806077a45917117fc1539",
        products=[regular(p) for p in [frozen_path, score_path, csv_path]],
        original_33336_inputs_reauthenticated=True,
        complete_900_file_work_reauthenticated=True,
        source_reports_all_eleven_current=True,
    )
    target = out / "independent-radius-comparison-review.json"
    assert not target.exists()
    with target.open("x") as stream:
        stream.write(json.dumps(review, indent=2) + "\n")
    print(
        json.dumps(
            {
                "review": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
