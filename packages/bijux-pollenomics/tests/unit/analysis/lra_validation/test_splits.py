"""Counterexamples for duplicate identities and hidden regional-input leakage."""

import pytest

from bijux_pollenomics.analysis.lra_validation import (
    Fold,
    SiteRecord,
    ValidationRefusal,
    assert_allowed_inputs,
    grouped_block_holdouts,
    grouped_leave_one_out,
    manifest_sha256,
    split_manifest,
)


def test_transitive_duplicate_core_and_source_aliases_are_one_site():
    rows = (
        SiteRecord("neotoma:1", "site:a", ("core:1",), "north"),
        SiteRecord("sead:2", "renamed:a", ("core:1", "raw:9"), "north"),
        SiteRecord("grid:9", "derived:a", ("raw:9",), "north"),
        SiteRecord("sead:3", "site:b", (), "south"),
    )
    folds = grouped_leave_one_out(rows)
    assert len(folds) == 2
    assert {fold.test_record_ids for fold in folds} == {
        ("grid:9", "neotoma:1", "sead:2"),
        ("sead:3",),
    }
    assert manifest_sha256(split_manifest(rows)) == manifest_sha256(
        split_manifest(reversed(rows))
    )
    assert len(grouped_block_holdouts(rows)) == 2


@pytest.mark.parametrize(
    "rows",
    [(), (SiteRecord("r1", "s1"),), (SiteRecord("r1", "s1"), SiteRecord("r1", "s2"))],
)
def test_insufficient_or_duplicate_record_sets_refuse(rows):
    with pytest.raises(ValidationRefusal):
        grouped_leave_one_out(rows)


def test_block_assignment_cannot_split_aliases_or_assume_missing_block():
    with pytest.raises(ValidationRefusal, match="same known block"):
        grouped_block_holdouts(
            [
                SiteRecord("a", "same", block_id="north"),
                SiteRecord("b", "same", block_id="south"),
                SiteRecord("c", "other", block_id="south"),
            ]
        )
    with pytest.raises(ValidationRefusal, match="same known block"):
        grouped_block_holdouts(
            [SiteRecord("a", "a"), SiteRecord("b", "b", block_id="south")]
        )


def test_regional_dependency_closure_refuses_renamed_heldout_product():
    fold = next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )
    graph = {
        "train": (),
        "test": (),
        "renamed-grid": ("upstream",),
        "upstream": ("test",),
    }
    with pytest.raises(ValidationRefusal) as error:
        assert_allowed_inputs(
            fold,
            ["train", "renamed-grid"],
            graph,
            admitted_external_ids=["renamed-grid", "upstream", "test"],
        )
    assert error.value.reason_code == "withheld_input_leakage"


@pytest.mark.parametrize(
    ("graph", "externals", "reason"),
    [
        ({"train": ("unknown",)}, (), "unadmitted_input"),
        ({"train": ("unknown",)}, ("unknown",), "unknown_input_lineage"),
        (
            {"train": ("external",), "external": ("train",)},
            ("external",),
            "cyclic_input_lineage",
        ),
    ],
)
def test_lineage_gaps_and_cycles_fail_closed(graph, externals, reason):
    fold = next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )
    with pytest.raises(ValidationRefusal) as error:
        assert_allowed_inputs(fold, ["train"], graph, admitted_external_ids=externals)
    assert error.value.reason_code == reason


def test_explicit_raw_leaf_and_independent_parameter_library_are_allowed():
    fold = next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )
    assert assert_allowed_inputs(
        fold, ["train"], {"train": ("ppe",), "ppe": ()}, admitted_external_ids=["ppe"]
    ) == ("ppe", "train")


def test_long_lineage_and_diamond_dependencies_do_not_recurse_or_false_cycle():
    fold = next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )
    graph = {f"node:{i}": (f"node:{i + 1}",) for i in range(2000)}
    graph["node:2000"] = ()
    graph["train"] = ("left", "right")
    graph["left"] = ("node:0",)
    graph["right"] = ("node:0",)
    closure = assert_allowed_inputs(fold, ["train"], graph, admitted_external_ids=graph)
    assert len(closure) == 2004


def test_identity_and_partition_strings_are_not_character_collections():
    with pytest.raises(ValidationRefusal, match="bare string"):
        SiteRecord("record", "site", identity_keys="core")
    with pytest.raises(ValidationRefusal, match="bare string"):
        Fold("fold", "train", ("test",), ("train-group",), ("test-group",))


@pytest.mark.parametrize("field", ["input_ids", "admitted_external_ids", "parents"])
def test_lineage_string_collections_are_refused(field):
    fold = Fold("fold", ("train",), ("test",), ("train-group",), ("test-group",))
    inputs = "train" if field == "input_ids" else ["train"]
    externals = "external" if field == "admitted_external_ids" else []
    graph = {"train": "test" if field == "parents" else ()}
    with pytest.raises(ValidationRefusal, match="bare string"):
        assert_allowed_inputs(fold, inputs, graph, admitted_external_ids=externals)
