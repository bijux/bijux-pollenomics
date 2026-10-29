"""Join actual paired outputs to complete raw ledgers and retained scientific values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts import EXPECTED, PRODUCER_SHA, qualify_pairs
from custody import authenticate, regular, sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    original = authenticate()
    assert plan["radius_execution"] == {
        k: original[k] for k in plan["radius_execution"]
    }
    out = Path(plan["output"])
    assert regular(Path(plan["producer"]["path"])) == plan["producer"]
    assert plan["producer"]["sha256"] == PRODUCER_SHA
    sources = {}
    for label, row in plan["sources"].items():
        assert sha(Path(row["path"])) == EXPECTED[label]
        p = out / "study" / row["target"]
        assert sha(p) == row["sha256"] and p.stat().st_size == row["bytes"]
        sources[label] = p
    assert {
        p.relative_to(out / "study").as_posix()
        for p in (out / "study").rglob("*")
        if p.is_file()
    } == {r["target"] for r in plan["sources"].values()}
    paired = out / "paired"
    assert not any(p.is_symlink() for p in [paired, *paired.rglob("*")])
    assert {
        p.relative_to(paired).as_posix() for p in paired.rglob("*") if p.is_file()
    } == {"report.json", "paired-scores.csv"}
    for row in plan["historical_paired"].values():
        assert regular(Path(row["path"])) == row
    report = qualify_pairs(
        json.loads((paired / "report.json").read_bytes()),
        json.loads(Path(plan["historical_paired"]["report"]["path"]).read_bytes()),
        (paired / "paired-scores.csv").read_bytes(),
        Path(plan["historical_paired"]["scores"]["path"]).read_bytes(),
        sources["radius_scores"].read_bytes(),
        sources["direct_mae"].read_bytes(),
        json.loads(sources["direct_hellinger"].read_bytes()),
    )
    radius = json.loads(sources["radius_report"].read_bytes())
    hellinger = json.loads(sources["direct_hellinger"].read_bytes())
    assert (
        radius["source"]["prediction_manifest_sha256"]
        == hellinger["lra_prediction_manifest_sha256"]
    )
    assert radius["refused_site"] == "author:BECKHAM"
    report.update(
        candidate=plan["candidate"],
        radius_execution=plan["radius_execution"],
        products=[regular(paired / n) for n in ["report.json", "paired-scores.csv"]],
        source_sha256=EXPECTED,
    )
    target = out / "independent-paired-review.json"
    with target.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"review": str(target), "sha256": sha(target)}))


if __name__ == "__main__":
    main()
