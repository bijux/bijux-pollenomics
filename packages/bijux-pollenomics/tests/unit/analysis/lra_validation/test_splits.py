"""Counterexamples for duplicate identities and hidden regional-input leakage."""

from typing import Any

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


def test_transitive_duplicate_core_and_source_aliases_are_one_site() -> None:
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


@pytest.mark.parametrize("key", ["p-test", "site:test"])
def test_one_sided_identity_key_holds_alternate_record_out(key: str) -> None:
    records = (
        SiteRecord("p-test", "site:test", block_id="east"),
        SiteRecord("p-alias", "site:alternate", (key,), "east"),
        SiteRecord("v-train", "site:train", block_id="west"),
    )
    fold = next(
        fold
        for fold in grouped_leave_one_out(records)
        if "p-test" in fold.test_record_ids
    )
    assert fold.test_record_ids == ("p-alias", "p-test")
    assert fold.train_record_ids == ("v-train",)
    graph = {
        "p-test": (),
        "p-alias": (),
        "v-train": (),
        "regional": ("p-alias",),
    }
    with pytest.raises(ValidationRefusal) as error:
        assert_allowed_inputs(
            fold,
            ("v-train", "regional"),
            graph,
            admitted_external_ids=("regional",),
        )
    assert error.value.reason_code == "withheld_input_leakage"


def test_one_sided_identity_key_crossing_blocks_refuses() -> None:
    records = (
        SiteRecord("p-test", "site:test", block_id="east"),
        SiteRecord("p-alias", "site:alternate", ("p-test",), "west"),
        SiteRecord("v-train", "site:train", block_id="west"),
    )
    with pytest.raises(ValidationRefusal, match="same known block"):
        grouped_block_holdouts(records)


def test_identity_key_matching_unrelated_record_and_site_refuses() -> None:
    records = (
        SiteRecord("p-test", "site:test"),
        SiteRecord("p-other", "p-test"),
        SiteRecord("p-alias", "site:alias", ("p-test",)),
    )
    with pytest.raises(ValidationRefusal) as error:
        grouped_leave_one_out(records)
    assert error.value.reason_code == "ambiguous_identity_key"


@pytest.mark.parametrize(
    "rows",
    [(), (SiteRecord("r1", "s1"),), (SiteRecord("r1", "s1"), SiteRecord("r1", "s2"))],
)
def test_insufficient_or_duplicate_record_sets_refuse(
    rows: tuple[SiteRecord, ...],
) -> None:
    with pytest.raises(ValidationRefusal):
        grouped_leave_one_out(rows)


def test_block_assignment_cannot_split_aliases_or_assume_missing_block() -> None:
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


def test_regional_dependency_closure_refuses_renamed_heldout_product() -> None:
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
def test_lineage_gaps_and_cycles_fail_closed(
    graph: dict[str, tuple[str, ...]], externals: tuple[str, ...], reason: str
) -> None:
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


def test_explicit_raw_leaf_and_independent_parameter_library_are_allowed() -> None:
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


def test_long_lineage_and_diamond_dependencies_do_not_recurse_or_false_cycle() -> None:
    fold = next(
        fold
        for fold in grouped_leave_one_out(
            [SiteRecord("train", "s1"), SiteRecord("test", "s2")]
        )
        if fold.test_record_ids == ("test",)
    )
    graph: dict[str, tuple[str, ...]] = {
        f"node:{i}": (f"node:{i + 1}",) for i in range(2000)
    }
    graph["node:2000"] = ()
    graph["train"] = ("left", "right")
    graph["left"] = ("node:0",)
    graph["right"] = ("node:0",)
    closure = assert_allowed_inputs(fold, ["train"], graph, admitted_external_ids=graph)
    assert len(closure) == 2004


def test_identity_and_partition_strings_are_not_character_collections() -> None:
    malformed: Any = "core"
    with pytest.raises(ValidationRefusal, match="bare string"):
        SiteRecord("record", "site", identity_keys=malformed)
    with pytest.raises(ValidationRefusal, match="bare string"):
        Fold("fold", malformed, ("test",), ("train-group",), ("test-group",))


@pytest.mark.parametrize("field", ["input_ids", "admitted_external_ids", "parents"])
def test_lineage_string_collections_are_refused(field: str) -> None:
    fold = Fold("fold", ("train",), ("test",), ("train-group",), ("test-group",))
    inputs = "train" if field == "input_ids" else ["train"]
    externals = "external" if field == "admitted_external_ids" else []
    graph = {"train": "test" if field == "parents" else ()}
    with pytest.raises(ValidationRefusal, match="bare string"):
        assert_allowed_inputs(fold, inputs, graph, admitted_external_ids=externals)


def test_training_admission_preserves_original_block_and_whole_alias_groups() -> None:
    from bijux_pollenomics.analysis.lra_validation.splits import (
        admit_training_groups,
        assert_training_inputs,
    )

    records = (
        SiteRecord("a", "lake-a", block_id="train"),
        SiteRecord("a-alias", "lake-a", block_id="train"),
        SiteRecord("b", "lake-b", block_id="train"),
        SiteRecord("t1", "lake-t1", block_id="test"),
        SiteRecord("t2", "lake-t2", block_id="test"),
    )
    fold = next(f for f in grouped_block_holdouts(records) if f.fold_id == "block:test")
    groups = {
        r: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for r in f.test_record_ids
    }
    admission = admit_training_groups(
        fold,
        records,
        (groups["a"],),
        criterion={"profile": "synthetic-buffer", "minimum_buffer_m": 1000},
    )
    assert admission.fold is fold
    assert admission.admitted_record_ids == ("a", "a-alias")
    assert admission.excluded_record_ids == ("b",)
    assert fold.test_record_ids == ("t1", "t2")
    assert admission.as_dict()["original_fold"] == fold.as_dict()
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(
        ("a", "a-alias", "b", "t1", "t2"), ()
    )
    assert assert_training_inputs(
        fold, admission.admitted_record_ids, graph, training_admission=admission
    ) == ("a", "a-alias")
    for forbidden in ("b", "t1", "t2"):
        graph["derived"] = (forbidden,)
        with pytest.raises(ValidationRefusal):
            assert_training_inputs(
                fold,
                ("derived",),
                graph,
                training_admission=admission,
                admitted_external_ids=("derived", forbidden),
            )


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown_group",
        "test_group",
        "duplicate_group",
        "missing_owner",
        "cross_partition_owner",
        "different_fold",
        "noncanonical_criterion",
    ],
)
def test_malformed_training_admission_refused(mutation: str) -> None:
    from dataclasses import replace

    from bijux_pollenomics.analysis.lra_validation.contracts import (
        TrainingAdmission,
        canonical_json,
        site_group_id,
    )

    fold = Fold(
        "block",
        ("a", "b"),
        ("t",),
        (site_group_id(("a",)), site_group_id(("b",))),
        (site_group_id(("t",)),),
    )
    kwargs: dict[str, Any] = {
        "fold": fold,
        "record_groups": (
            ("a", site_group_id(("a",))),
            ("b", site_group_id(("b",))),
            ("t", site_group_id(("t",))),
        ),
        "admitted_group_ids": (site_group_id(("a",)),),
        "criterion_json": canonical_json({"profile": "synthetic"}),
    }
    if mutation == "unknown_group":
        kwargs["admitted_group_ids"] = ("missing",)
    elif mutation == "test_group":
        kwargs["admitted_group_ids"] = (site_group_id(("t",)),)
    elif mutation == "duplicate_group":
        kwargs["admitted_group_ids"] = (site_group_id(("a",)), site_group_id(("a",)))
    elif mutation == "missing_owner":
        kwargs["record_groups"] = (
            ("a", site_group_id(("a",))),
            ("t", site_group_id(("t",))),
        )
    elif mutation == "cross_partition_owner":
        kwargs["record_groups"] = (
            ("a", site_group_id(("t",))),
            ("b", site_group_id(("b",))),
            ("t", site_group_id(("a",))),
        )
    elif mutation == "noncanonical_criterion":
        kwargs["criterion_json"] = '{ "profile": "synthetic" }'
    with pytest.raises(ValidationRefusal):
        admission = TrainingAdmission(**kwargs)
        if mutation == "different_fold":
            admission.validate(replace(fold, fold_id="another"))


def test_training_admission_default_retains_existing_closure_contract() -> None:
    from bijux_pollenomics.analysis.lra_validation.splits import assert_training_inputs

    fold = Fold("outer", ("a", "b"), ("t",), ("ga", "gb"), ("gt",))
    graph = {"a": (), "b": ()}
    assert assert_training_inputs(fold, ("a",), graph) == assert_allowed_inputs(
        fold, ("a",), graph
    )


def test_reassigned_alias_cannot_enter_admitted_group() -> None:
    from dataclasses import replace

    from bijux_pollenomics.analysis.lra_validation.splits import admit_training_groups

    records = (
        SiteRecord("a", "alias-lake", block_id="train"),
        SiteRecord("a2", "alias-lake", block_id="train"),
        SiteRecord("b", "other-lake", block_id="train"),
        SiteRecord("t", "test-lake", block_id="test"),
    )
    fold = next(f for f in grouped_block_holdouts(records) if f.fold_id == "block:test")
    groups = {
        r: f.test_group_ids[0]
        for f in grouped_leave_one_out(records)
        for r in f.test_record_ids
    }
    admission = admit_training_groups(
        fold, records, (groups["b"],), criterion={"profile": "synthetic-buffer"}
    )
    assert admission.excluded_record_ids == ("a", "a2")
    changed = tuple(
        (record, groups["b"] if record == "a2" else group)
        for record, group in admission.record_groups
    )
    with pytest.raises(ValidationRefusal, match="complete record membership"):
        replace(admission, record_groups=changed)
