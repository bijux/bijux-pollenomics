"""Compare complete original source/count results and actual managed reader bytes."""

import argparse
import json
from pathlib import Path

from comparison import exact, exact_csv
from input_custody import qualify, row

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    load_routes,
    render_route,
    verified_authored_reader,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    a = p.parse_args()
    plan = json.loads(a.plan.read_bytes())
    repository = Path(plan["repository"])
    output = Path(plan["output"])
    private = Path(plan["private_root"])
    for item in plan["input_pins"]:
        assert row(Path(item["path"])) == item
    exact(qualify(repository, private), plan["complete_source_inputs"])
    progress = json.loads((output / "stage-progress.json").read_bytes())
    assert len(progress) == 1 and type(progress[0]["actual_exit"]) is int
    assert progress[0]["actual_exit"] == 0 and progress[0]["timed_out"] is False
    assert progress[0]["argv"] == plan["stages"][0]["argv"]
    product = output / "products"
    original = Path(plan["original_family"])
    expected = {"REPORT.md", "report.json", "scores.csv", "predictions.csv"}
    assert {
        p.relative_to(product).as_posix() for p in product.rglob("*") if p.is_file()
    } == expected
    rows = []
    for name in sorted(expected):
        path = product / name
        retained = original / name
        assert not path.is_symlink()
        actual, old = path.read_bytes(), retained.read_bytes()
        if name.endswith(".csv"):
            exact_csv(actual, old)
            assert actual == old
            comparison = "Family wrapper normalized CSV wire; final bytes exact"
        elif name == "REPORT.md":
            route = load_routes()[plan["reader_path"]]
            # Both directions use the maintained authority; arbitrary suffix
            # stripping cannot authorize generated prose or a stale account.
            verified_authored_reader(old, route)
            verified_authored_reader(actual, route)
            assert actual == old and render_route(actual, route) == old
            comparison = "Maintained verified_authored_reader/render_route and exact full current managed reader bytes"
        else:
            exact(json.loads(actual), json.loads(old))
            assert actual == old
            report = json.loads(actual)
            assert report["count_denominator"] == "31_author_prepared_pollen_taxa"
            assert (
                report["measured_vegetation_accuracy"]
                == report["swedish_cohort"]
                == "not_evaluated"
            )
            assert len(report["grids"]) == 2
            comparison = "Byte and typed JSON exact"
        rows.append(
            {
                "name": name,
                "actual": row(path),
                "current_retained": row(retained),
                "comparison": comparison,
            }
        )
    report = json.loads((product / "report.json").read_bytes())
    result = {
        "schema_version": "independent-author-pollen-family-replay-review.v1",
        "candidate": plan["candidate"],
        "actual_producer": progress[0],
        "products": rows,
        "source_snapshot_members": 193,
        "source_sites": 17,
        "grids": 2,
        "prepared_taxa": 31,
        "attempted_site_bins": report["attempted_site_bins"],
        "scored_site_bins": report["scored_site_bins"],
        "refused_no_training_site_bins": report["refused_no_training_site_bins"],
        "all_scientific_typed_values_exact": True,
        "all_source_inputs_exact": True,
        "R_executed": False,
        "vegetation_accuracy_or_rights_or_human_acceptance": False,
        "scope": plan["scope"],
    }
    path = output / "independent-author-holdout-review.json"
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(row(path)))


if __name__ == "__main__":
    main()
