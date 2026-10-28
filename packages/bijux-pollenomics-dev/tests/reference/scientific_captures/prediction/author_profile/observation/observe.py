"""Reconcile complete current author outputs against exact original source and retained science."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).absolute().parent))
from comparison import (  # noqa: E402 - isolated script imports owned helper.
    compare_report,
    sha,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--plan", type=Path, required=True)
    args = p.parse_args()
    plan = json.loads(args.plan.read_bytes())
    out = Path(plan["output"])
    private = Path(plan["private_root"])
    for row in plan["input_pins"]:
        path = Path(row["path"])
        assert (
            path.is_file()
            and not path.is_symlink()
            and sha(path) == row["sha256"]
            and path.stat().st_size == row["bytes"]
        )
    snapshot = json.loads((private / "snapshot-manifest.json").read_bytes())
    assert snapshot["file_count"] == len(snapshot["files"]) == 193
    for name, digest in snapshot["files"].items():
        assert sha(private / name) == digest
    progress = json.loads((out / "stage-progress.json").read_bytes())
    assert len(progress) == 1 and all(
        type(stage["actual_exit"]) is int
        and stage["actual_exit"] == 0
        and stage["timed_out"] is False
        and stage["argv"] == plan["stages"][i]["argv"]
        for i, stage in enumerate(progress)
    )
    products = []
    for name, items in plan["original_products"].items():
        directory = out / name
        expected = set(items)
        actual = {
            p.relative_to(directory).as_posix()
            for p in directory.rglob("*")
            if p.is_file()
        }
        assert actual == expected
        original = json.loads(Path(plan["original_reports"][name]).read_bytes())
        current = json.loads((directory / "report.json").read_bytes())
        compare_report(
            name,
            current,
            original,
            plan["current_code_inputs"][name],
            plan["profile_document_inputs"]
            if name == "author-site-profile-comparison"
            else None,
        )
        assert (
            current["ecological_accuracy_claimed"] is False
            and current["chronology_geometry_transport_fixed"] is True
        )
        for row in plan["private_members"][name]:
            assert (
                sha(private / row["path"]) == row["sha256"]
                and (private / row["path"]).stat().st_size == row["bytes"]
            )
        for filename, old in items.items():
            path = directory / filename
            assert path.is_file() and not path.is_symlink()
            same = path.read_bytes() == Path(old).read_bytes()
            if filename != "report.json":
                assert same
            products.append(
                {
                    "owner": name,
                    "path": str(path),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                    "original_path": old,
                    "original_sha256": sha(Path(old)),
                    "byte_identical": same,
                    "all_scientific_typed_values_exact": True,
                    "allowed_difference": "Exact current code rows and authenticated upstream documentation identities"
                    if filename == "report.json"
                    else "none",
                }
            )
    owner = plan["owner"]
    current = json.loads((out / owner / "report.json").read_bytes())
    if owner == "author-site-uncertainty":
        assert len(current["site_ids"]) == 6
        assert len(current["prepared_targets"]) == 10
        assert current["joint_replicate_count"] == 1024
    else:
        assert current["paired_site_draw_count"] == 1000
        from custody import successful_uncertainty

        prior = plan["successful_uncertainty_prerequisite"]
        successful_uncertainty(
            Path(plan["repository"]),
            Path(prior["plan"]["path"]),
            prior["plan"]["sha256"],
            Path(prior["terminal"]["path"]),
            prior["terminal"]["sha256"],
        )
    assert current["selected_counts_by_site"] == [289, 293, 2223, 2786, 4251, 562]
    result = {
        "schema_version": "independent-current-author-site-source-review.v1",
        "candidate": plan["candidate"],
        "owner": owner,
        "profile_document_inputs": plan["profile_document_inputs"],
        "historical_document_epoch_bridge": plan["historical_document_epoch_bridge"],
        "successful_uncertainty_prerequisite": plan[
            "successful_uncertainty_prerequisite"
        ],
        "source_snapshot_members": 193,
        "private_original_input_counts": {
            name: len(rows) for name, rows in plan["private_members"].items()
        },
        "actual_producer_stages": progress,
        "complete_products": products,
        "scientific_typed_values_exact_to_original": True,
        "source_private_members_exact": True,
        "site_count": 6,
        "selected_taxa": 10,
        "selected_counts_by_site": [289, 293, 2223, 2786, 4251, 562],
        "current_joint_draws": 1024 if owner == "author-site-uncertainty" else None,
        "original_retained_profile_paired_draws": 1000
        if owner == "author-site-profile-comparison"
        else None,
        "R_executed": False,
        "ecological_accuracy_claimed": False,
        "scientific_release_or_rights_admission": False,
        "scope": plan["scope"],
    }
    path = out / "independent-author-review.json"
    assert not path.exists()
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps({"path": str(path), "sha256": sha(path), "products": len(products)})
    )


if __name__ == "__main__":
    main()
