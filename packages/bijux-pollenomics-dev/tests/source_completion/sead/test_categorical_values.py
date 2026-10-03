"""Category relations retain item identity, display text and source refusals."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead.categorical_values import (
    _item_relation,
    _reconcile_parent,
    _reconcile_support,
    run,
)


def source() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    parent = {
        "analysis_value_id": 2,
        "analysis_entity_id": 13,
        "value_class_id": 8,
        "analysis_value": "source display",
    }
    component = {
        "analysis_categorical_value_id": 3,
        "analysis_value_id": 2,
        "value_type_item_id": 6,
        "value": None,
        "is_variant": None,
    }
    observation = {
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": "source display",
        "source_value_state": "reported",
        "entity_relation_id": "sead-analysis-entity:13",
        "source_components": {"tbl_analysis_categorical_values": [component.copy()]},
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
        "source_semantics": {
            "value_semantics_id": "sead-value-class:8",
            "source_unit_id": None,
            "unit_status": "not_exposed_by_relation",
        },
        "chronology_link": {
            "eligible_claim_count": 0,
            "claim_count": 1,
            "status": "direct_analysis_entity_context_only",
            "selection_rule": "same_analysis_entity_only",
            "entity_relation_id": "sead-analysis-entity:13",
        },
    }
    return parent, component, observation


def test_null_component_preserves_linked_item_and_different_parent_display() -> None:
    parent, component, observation = source()
    item, value_class, value_type = _item_relation(
        component,
        parent,
        {6: {"value_type_id": 13, "name": "W"}},
        {8: {"value_type_id": 13}},
        {13: {"base_type": "category"}},
    )
    assert item["name"] == "W" and parent["analysis_value"] == "source display"
    assert value_class["value_type_id"] == 13 and value_type["base_type"] == "category"
    _reconcile_parent(observation, parent, [component], "parent-digest")
    assert component["value"] is None and component["is_variant"] is None


@pytest.mark.parametrize("item_id", [True, "6", 6.0, 99])
def test_item_identity_cannot_be_coerced(item_id: object) -> None:
    parent, component, _ = source()
    component["value_type_item_id"] = item_id
    with pytest.raises(ValueError, match="item key"):
        _item_relation(component, parent, {6: {}}, {8: {}}, {})


@pytest.mark.parametrize(
    "item_type,base_type", [(17, "category"), (13, "text"), (True, "category")]
)
def test_category_class_and_item_must_share_a_category_type(
    item_type: object, base_type: str
) -> None:
    parent, component, _ = source()
    with pytest.raises(ValueError, match="types differ"):
        _item_relation(
            component,
            parent,
            {6: {"value_type_id": item_type}},
            {8: {"value_type_id": 13}},
            {13: {"base_type": base_type}},
        )


@pytest.mark.parametrize(
    "field,replacement",
    [("value", False), ("is_variant", False), ("value_type_item_id", 7)],
)
def test_null_and_identity_replacements_are_refused(
    field: str, replacement: object
) -> None:
    parent, component, observation = source()
    changed = copy.deepcopy(observation)
    changed["source_components"]["tbl_analysis_categorical_values"][0][field] = (
        replacement
    )
    with pytest.raises(ValueError, match="parent or components differ"):
        _reconcile_parent(changed, parent, [component], "parent-digest")


def test_parent_display_cannot_be_replaced_by_item_name_or_promoted() -> None:
    parent, component, observation = source()
    with pytest.raises(ValueError, match="parent or components differ"):
        _reconcile_parent(
            {**observation, "source_value": "W"}, parent, [component], "parent-digest"
        )
    with pytest.raises(ValueError, match="source refusal changed"):
        _reconcile_parent(
            {**observation, "event_eligibility": "eligible"},
            parent,
            [component],
            "parent-digest",
        )


def test_chronology_context_and_missing_unit_remain_separate() -> None:
    parent, _, observation = source()
    assert _reconcile_support(observation, parent, {"unit_id": None}, {}) == (
        "not_exposed_by_relation",
        "direct_analysis_entity_context_only",
    )
    changed = copy.deepcopy(observation)
    changed["chronology_link"]["selection_rule"] = "same_site"
    with pytest.raises(ValueError, match="chronology support differs"):
        _reconcile_support(changed, parent, {"unit_id": None}, {})
    changed = copy.deepcopy(observation)
    changed["source_semantics"]["source_unit_id"] = 8
    with pytest.raises(ValueError, match="unit semantics differ"):
        _reconcile_support(changed, parent, {"unit_id": None}, {})


def test_categorical_chronology_must_share_raw_parent_entity_identity() -> None:
    parent, component, observation = source()
    wrong_observation = copy.deepcopy(observation)
    wrong_observation["entity_relation_id"] = "sead-analysis-entity:14"
    with pytest.raises(ValueError, match="parent entity relation differs"):
        _reconcile_parent(wrong_observation, parent, [component], "parent-digest")


def test_categorical_chronology_link_must_share_observation_entity() -> None:
    parent, _, observation = source()
    wrong_link = copy.deepcopy(observation)
    wrong_link["chronology_link"]["entity_relation_id"] = "sead-analysis-entity:14"
    with pytest.raises(ValueError, match="chronology entity relation differs"):
        _reconcile_support(wrong_link, parent, {"unit_id": None}, {})


def test_categorical_parent_entity_key_cannot_be_boolean() -> None:
    parent, component, observation = source()
    parent["analysis_entity_id"] = True
    observation["source_row"] = parent.copy()
    with pytest.raises(ValueError, match="parent entity relation differs"):
        _reconcile_parent(observation, parent, [component], "parent-digest")


@pytest.mark.parametrize("eligible,claims", [(True, 1), (1, 0), (0, -1), (0, 1.0)])
def test_chronology_counts_are_exact_nonnegative_integers(
    eligible: object, claims: object
) -> None:
    parent, _, observation = source()
    observation["chronology_link"].update(
        eligible_claim_count=eligible, claim_count=claims
    )
    with pytest.raises(ValueError, match="counts are invalid"):
        _reconcile_support(observation, parent, {"unit_id": None}, {})


def test_destination_preserves_existing_bytes_and_refuses_symlinks(
    tmp_path: Path,
) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    existing = artifacts / "report.json"
    existing.write_bytes(b"user bytes")
    with pytest.raises(ValueError, match="already exists"):
        run(tmp_path, existing)
    assert existing.read_bytes() == b"user bytes"
    with pytest.raises(ValueError, match="artifact file"):
        run(tmp_path, tmp_path / "report.json")
    link = artifacts / "linked"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="artifact file"):
        run(tmp_path, link / "report.json")


def test_changed_source_is_refused_before_output_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.sead import categorical_values

    data = tmp_path / "data"
    data.mkdir()
    (data / "source.json").write_bytes(b"changed source")
    monkeypatch.setattr(
        categorical_values,
        "build_report",
        lambda _: {"source_readset_sha256": {"source.json": "0" * 64}},
    )
    output = tmp_path / "artifacts" / "report.json"
    with pytest.raises(ValueError, match="changed before publication"):
        run(tmp_path, output)
    assert not output.exists()


def test_eligible_chronology_claim_does_not_promote_source_event() -> None:
    parent, component, observation = source()
    observation["chronology_link"].update(
        eligible_claim_count=1, status="direct_analysis_entity_eligible_claim"
    )
    assert _reconcile_support(observation, parent, {"unit_id": None}, {})[1] == (
        "direct_analysis_entity_eligible_claim"
    )
    _reconcile_parent(observation, parent, [component], "parent-digest")
    assert observation["event_eligibility"] == "refused"
