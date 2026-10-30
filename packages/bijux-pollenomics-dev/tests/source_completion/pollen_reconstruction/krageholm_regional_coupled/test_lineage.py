"""Full family construction and quantitative-ancestry refusal controls."""

from typing import Any

import pytest

from .lineage import allowed_closure, expected_folds, families


def catalogue() -> list[dict[str, Any]]:
    return [
        {
            "record_id": code,
            "site_id": "site:" + code,
            "identity_keys": ["unit:" + code],
        }
        for code in ("BOKE", "BUS", "SOLSOE83", "KRAG")
    ]


def test_fixed_regional_is_never_target_or_local_predictor() -> None:
    folds = expected_folds(catalogue(), ["BOKE", "BUS", "SOLSOE83"], "KRAG")
    assert len(folds) == 3
    assert {fold["test_record_ids"][0] for fold in folds} == {"BOKE", "BUS", "SOLSOE83"}
    for fold in folds:
        assert "KRAG" in fold["train_record_ids"]
        assert len(set(fold["train_record_ids"]) - {"KRAG"}) == 2
        assert not set(fold["train_record_ids"]) & set(fold["test_record_ids"])


def test_fold_group_ids_sort_independently_of_record_ids() -> None:
    folds = expected_folds(catalogue(), ["BOKE", "BUS", "SOLSOE83"], "KRAG")
    boke = "site-group:6c0e75aa0bb10fcb3a6e06ab2417f4246e93cd44b8502110d43b3efbf3b29b54"
    bus = "site-group:3284d35bb1fec648fe98498375da0497b70f9f4681d3b6d4a0795a9ba6490c99"
    solsoe = (
        "site-group:8be91017acc89e21d682f71aabc29cfeb5c12056729dd6ccec30ab3faa82c645"
    )
    krag = "site-group:bfd7ede870346e4a06ceccc1c2b6eb2eb7ccb0b78078c69910526146c5469796"
    assert [fold["fold_id"] for fold in folds] == [bus, boke, solsoe]
    assert [bus, krag, solsoe] != [bus, solsoe, krag]
    assert next(fold for fold in folds if fold["fold_id"] == boke) == {
        "fold_id": boke,
        "train_record_ids": ["BUS", "KRAG", "SOLSOE83"],
        "test_record_ids": ["BOKE"],
        "train_group_ids": [bus, solsoe, krag],
        "test_group_ids": [boke],
    }


def test_transitive_alias_family_is_built_before_role_selection() -> None:
    records = catalogue()
    records[0]["identity_keys"].append("bridge")
    records.append(
        {
            "record_id": "middle",
            "site_id": "site:middle",
            "identity_keys": ["bridge", "unit:KRAG"],
        }
    )
    assert ["BOKE", "KRAG", "middle"] in families(records)
    with pytest.raises(ValueError, match="crosses"):
        expected_folds(records, ["BOKE", "BUS", "SOLSOE83"], "KRAG")


@pytest.mark.parametrize(
    "mutation", ["site", "named_record", "duplicate", "missing", "regional_target"]
)
def test_source_role_corruptions_refuse(mutation: str) -> None:
    records = catalogue()
    targets = ["BOKE", "BUS", "SOLSOE83"]
    if mutation == "site":
        records[-1]["site_id"] = records[0]["site_id"]
    elif mutation == "named_record":
        records[-1]["identity_keys"] = ["BOKE"]
    elif mutation == "duplicate":
        records.append(records[0])
    elif mutation == "missing":
        records.pop(1)
    else:
        targets[-1] = "KRAG"
    with pytest.raises(ValueError):
        expected_folds(records, targets, "KRAG")


def test_closed_lineage_includes_both_local_predictors_and_regional_source() -> None:
    graph = {
        "BOKE": [],
        "BUS": [],
        "KRAG": [],
        "regional": ["BOKE", "BUS", "KRAG"],
        "parameters": [],
        "geometry": [],
        "time": [],
    }
    assert allowed_closure(
        ["BOKE", "BUS", "KRAG", "regional", "parameters", "geometry", "time"],
        graph,
        ["BOKE", "BUS", "KRAG"],
        ["SOLSOE83"],
        ["regional", "parameters", "geometry", "time"],
    ) == sorted(graph)


@pytest.mark.parametrize("mode", ["withheld", "cycle", "missing", "unadmitted"])
def test_transitive_quantitative_lineage_refuses(mode: str) -> None:
    graph = {"regional": ["derived"], "derived": ["KRAG"], "KRAG": []}
    if mode == "withheld":
        graph["derived"] = ["SOLSOE83"]
        graph["SOLSOE83"] = []
    elif mode == "cycle":
        graph["derived"] = ["regional"]
    elif mode == "missing":
        del graph["KRAG"]
    else:
        graph["derived"] = ["foreign"]
        graph["foreign"] = []
    with pytest.raises(ValueError):
        allowed_closure(
            ["regional"],
            graph,
            ["KRAG"],
            ["SOLSOE83"],
            ["regional", "derived", "SOLSOE83"],
        )
