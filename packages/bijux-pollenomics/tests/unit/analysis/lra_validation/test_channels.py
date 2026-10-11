"""Adversarial channel admission keeps the actual outer holdout immutable."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
    assert_channel_inputs,
)
from bijux_pollenomics.analysis.lra_validation.contracts import Fold, ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.splits import assert_allowed_inputs


def fixture() -> tuple[
    Fold,
    tuple[ObservationChannels, ...],
    dict[str, tuple[str, ...]],
    ObservedPollenAdmission,
]:
    fold = Fold("original", ("p1",), ("p2", "p2-alias", "p3"), ("g1",), ("g2", "g3"))
    channels = tuple(
        ObservationChannels(
            record,
            group,
            (PollenChannel("raw:" + record, "a" * 64),),
            ("veg:" + record,),
        )
        for record, group in (
            ("p1", "g1"),
            ("p2", "g2"),
            ("p2-alias", "g2"),
            ("p3", "g3"),
        )
    )
    graph: dict[str, tuple[str, ...]] = {
        key: ()
        for row in channels
        for key in (
            row.record_id,
            row.pollen_channels[0].input_id,
            row.vegetation_input_ids[0],
        )
    }
    admission = ObservedPollenAdmission(
        "p2", "g2", (PollenChannel("raw:p2", "a" * 64),)
    )
    return fold, channels, graph, admission


def test_observed_pollen_keeps_original_fold_and_quantitative_closure() -> None:
    fold, channels, graph, admission = fixture()
    original = fold.as_dict()
    closure = assert_channel_inputs(
        fold, ("raw:p1", "raw:p2"), graph, channels=channels, observed_pollen=admission
    )
    assert closure == ("raw:p1", "raw:p2") and fold.as_dict() == original
    with pytest.raises(ValidationRefusal):
        assert_allowed_inputs(fold, ("raw:p2",), graph)


@pytest.mark.parametrize(
    "leak",
    [
        "p2",
        "p2-alias",
        "p3",
        "raw:p2-alias",
        "raw:p3",
        "veg:p2",
        "veg:p2-alias",
        "veg:p3",
    ],
)
def test_other_heldout_channels_owners_and_aliases_cannot_be_externalized(
    leak: str,
) -> None:
    fold, channels, graph, admission = fixture()
    graph["estimate"] = ("raw:p2", leak)
    with pytest.raises(ValidationRefusal, match="Withheld record"):
        assert_channel_inputs(
            fold,
            ("estimate",),
            graph,
            channels=channels,
            observed_pollen=admission,
            admitted_external_ids=("estimate", leak),
        )


def test_supplied_target_owner_edge_is_never_deleted() -> None:
    fold, channels, graph, admission = fixture()
    graph["raw:p2"] = ("p2",)
    with pytest.raises(ValidationRefusal, match="Withheld record"):
        assert_channel_inputs(
            fold, ("raw:p2",), graph, channels=channels, observed_pollen=admission
        )


def test_alias_pollen_requires_explicit_same_group_byte_pin_and_named_owner_channel() -> (
    None
):
    fold, channels, graph, admission = fixture()
    extra = PollenChannel("raw:p2-alias", "a" * 64)
    admission = replace(admission, pollen_channels=(*admission.pollen_channels, extra))
    assert assert_channel_inputs(
        fold,
        ("raw:p2", "raw:p2-alias"),
        graph,
        channels=channels,
        observed_pollen=admission,
    ) == ("raw:p2", "raw:p2-alias")
    with pytest.raises(ValidationRefusal, match="named target record"):
        assert_channel_inputs(
            fold,
            ("raw:p2-alias",),
            graph,
            channels=channels,
            observed_pollen=replace(admission, pollen_channels=(extra,)),
        )


@pytest.mark.parametrize(
    "kind",
    [
        "hash",
        "group",
        "record",
        "unused",
        "missing",
        "cycle",
        "incomplete",
        "split_alias",
        "collision",
        "cross_group",
    ],
)
def test_incomplete_or_forged_channel_evidence_refuses(kind: str) -> None:
    fold, channels, graph, admission = fixture()
    inputs = ("raw:p2",)
    if kind == "hash":
        admission = replace(
            admission, pollen_channels=(PollenChannel("raw:p2", "b" * 64),)
        )
    elif kind == "group":
        admission = replace(admission, group_id="g3")
    elif kind == "record":
        admission = replace(admission, record_id="p1")
    elif kind == "unused":
        inputs = ("raw:p1",)
    elif kind == "missing":
        del graph["raw:p2"]
    elif kind == "cycle":
        graph["raw:p2"] = ("raw:p2",)
    elif kind == "incomplete":
        channels = channels[:-1]
    elif kind == "split_alias":
        channels = (*channels[:2], replace(channels[2], group_id="g1"), channels[3])
    elif kind == "collision":
        channels = (
            channels[0],
            replace(channels[1], vegetation_input_ids=("raw:p2",)),
            *channels[2:],
        )
    elif kind == "cross_group":
        channels = (
            channels[0],
            *channels[1:3],
            replace(channels[3], pollen_channels=channels[1].pollen_channels),
        )
    with pytest.raises(ValidationRefusal):
        assert_channel_inputs(
            fold, inputs, graph, channels=channels, observed_pollen=admission
        )


def test_all_withheld_mode_has_no_implicit_pollen_admission() -> None:
    fold, channels, graph, _ = fixture()
    assert assert_channel_inputs(fold, ("raw:p1",), graph, channels=channels) == (
        "raw:p1",
    )
    with pytest.raises(ValidationRefusal, match="Withheld record"):
        assert_channel_inputs(
            fold,
            ("raw:p2",),
            graph,
            channels=channels,
            admitted_external_ids=("raw:p2",),
        )
