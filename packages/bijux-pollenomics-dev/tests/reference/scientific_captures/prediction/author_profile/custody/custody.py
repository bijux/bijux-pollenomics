"""Authenticate upstream author report epochs without replacing scientific values."""

import copy
import json
from pathlib import Path

from comparison import exact, sha

PREFIX = "docs/report/method-certification/author-site-uncertainty/"
OLD_REPORT = "415185927514de10a71b6a7ba6c26d7bc1fd3ed8cc140760ec2e3e9f58f1c243"
OLD_DRAWS = "84da401dc862452bc329d11df074d2c6d7353b3e34b223892b5fd6702fae4390"


def record(path):
    assert path.is_absolute() and ".." not in path.parts
    assert path.resolve() == path and path.is_file()
    assert not any(p.is_symlink() for p in (path, *path.parents))
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def document_inputs(repository, controls):
    original_path = controls / "retained-original-uncertainty-report.json"
    assert sha(original_path) == OLD_REPORT
    original = json.loads(original_path.read_bytes())
    profile = json.loads(
        (
            repository
            / "docs/report/method-certification/author-site-profile-comparison/report.json"
        ).read_bytes()
    )
    declared = [
        r
        for r in profile["input_identities"]
        if r["path"].startswith("docs/") and not r["path"].endswith(".py")
    ]
    assert len(declared) == 2
    assert {r["path"]: r["sha256"] for r in declared} == {
        PREFIX + "report.json": OLD_REPORT,
        PREFIX + "draws.json": OLD_DRAWS,
    }
    rows = []
    for row in declared:
        path = repository / row["path"]
        actual = record(path)
        rows.append(
            {
                "path": row["path"],
                "sha256": actual["sha256"],
                "bytes": actual["bytes"],
                "absolute_path": str(path),
            }
        )
        if row["path"].endswith("draws.json"):
            assert actual["sha256"] == row["sha256"] and actual["bytes"] == row["bytes"]
    current = json.loads((repository / PREFIX / "report.json").read_bytes())
    before, after = copy.deepcopy(original), copy.deepcopy(current)
    original_code = before.pop("repository_code_inputs")
    current_code = after.pop("repository_code_inputs")
    exact(before, after)
    assert original["draws_sha256"] == current["draws_sha256"] == OLD_DRAWS
    return rows, {
        "original_report": record(original_path),
        "original_git_commit": "44ef3ff84587d4f04cfd71ac860f0774690f1c4a",
        "current_report": record(repository / PREFIX / "report.json"),
        "original_code_rows": original_code,
        "current_code_rows": current_code,
        "all_scientific_typed_values_exact": True,
        "original_draws_sha256": OLD_DRAWS,
    }


def successful_uncertainty(
    repository, plan_path, plan_sha, terminal_path, terminal_sha
):
    plan_record, terminal_record = record(plan_path), record(terminal_path)
    assert (
        plan_record["sha256"] == plan_sha and terminal_record["sha256"] == terminal_sha
    )
    plan, terminal = (
        json.loads(plan_path.read_bytes()),
        json.loads(terminal_path.read_bytes()),
    )
    output = Path(plan["output"])
    assert plan_path == output / "plan.json"
    assert terminal_path == output / "author-site-terminal.json"
    assert plan["owner"] == "author-site-uncertainty" and plan["repository"] == str(
        repository
    )
    assert (
        terminal["candidate"] == plan["candidate"]
        and terminal["plan_sha256"] == plan_sha
    )
    assert type(terminal["actual_exit"]) is int and terminal["actual_exit"] == 0
    assert terminal["common_actual_exit"] == 0
    assert (
        terminal["memory_bound_pass"] is True and terminal["storage_bound_pass"] is True
    )
    common_path = output / "terminal.json"
    assert terminal["common_terminal"] == {
        "path": str(common_path),
        "sha256": sha(common_path),
    }
    common = json.loads(common_path.read_bytes())
    assert (
        common["plan_sha256"] == plan_sha and common["candidate"] == plan["candidate"]
    )
    assert type(common["actual_exit"]) is int and common["actual_exit"] == 0
    assert (
        common["canonical_before"]
        == common["canonical_after"]
        == plan["canonical_identity"]
    )
    assert common["before_pin_mismatches"] == common["after_pin_mismatches"] == []
    assert common["absent_input_paths_unchanged"] is True
    assert len(plan["stages"]) == len(common["stages"]) == 2
    for expected, actual in zip(plan["stages"], common["stages"], strict=True):
        assert type(actual["actual_exit"]) is int and actual["actual_exit"] == 0
        assert actual["timed_out"] is False and actual["argv"] == expected["argv"]
    observer_path = output / "independent-author-review.json"
    observer = json.loads(observer_path.read_bytes())
    assert (
        observer["candidate"] == plan["candidate"]
        and observer["owner"] == plan["owner"]
    )
    assert observer["scientific_typed_values_exact_to_original"] is True
    assert observer["source_private_members_exact"] is True
    expected_files = {"report.json", "draws.json", "cover-draws.csv"}
    products = observer["complete_products"]
    assert (
        len(products) == 3
        and {Path(p["path"]).name for p in products} == expected_files
    )
    pins = {plan_path, terminal_path, common_path, observer_path}
    for row in products:
        name = Path(row["path"]).name
        product = output / "author-site-uncertainty" / name
        assert (
            Path(row["path"]) == product and record(product)["sha256"] == row["sha256"]
        )
        assert product.stat().st_size == row["bytes"]
        assert (repository / PREFIX / name).read_bytes() == product.read_bytes()
        pins.add(product)
    # Adoption can legitimately change the three canonical output pins. The
    # recorded successful epoch remains immutable; scientific implementation
    # and original private inputs must still be identical at profile execution.
    for row in plan["current_code_inputs"]["author-site-uncertainty"]:
        path = repository / row["path"]
        assert (
            record(path)["sha256"] == row["sha256"]
            and path.stat().st_size == row["bytes"]
        )
        pins.add(path)
    return {
        "plan": plan_record,
        "terminal": terminal_record,
        "common_terminal": record(common_path),
        "observer": record(observer_path),
        "source_candidate": plan["candidate"],
        "adopted_product_files": products,
    }, pins
