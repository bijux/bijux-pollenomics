"""Verify native dataset publication identity without upgrading scientific scope."""

from __future__ import annotations

import copy
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.attribution import (
    attribution,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.authority import (
    CAPTURE_PINS,
    DESCRIPTOR,
    PUBLICATION_CAPTURE_PINS,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.publications import (
    PREFIX,
    assess_publications,
    publication_inventory,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.sources import (
    load_inputs,
)


@pytest.fixture
def captured_repository(tmp_path):
    source = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    for name in (*CAPTURE_PINS, DESCRIPTOR):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    return tmp_path


def test_qualified_native_citations_preserve_exact_relations_and_nulls(
    captured_repository,
):
    inputs = load_inputs(captured_repository)
    result = attribution(inputs)
    assert result["attribution_complete"] is True
    assert result["pending_primary_publication_dataset_ids"] == []
    assert result["native_primary_dataset_relation_count"] == 4
    assert result["distinct_primary_publication_ids"] == [9495, 15707, 16469]
    assert result["native_secondary_dataset_relation_count"] == 3
    assert result["empty_native_publication_response_count"] == 0
    assert result["refused_native_publication_relation_count"] == 0
    assert (
        result["original_source_census_receipt_status"]
        == "PASS_PENDING_SOURCE_CAPTURE_ADMISSION"
    )
    assert result["original_articles_acquired_or_authenticated"] is False
    assert result["rights_and_raw_redistribution_admitted"] is False
    by_id = {row["native_dataset_id"]: row for row in result["datasets"]}
    expected = {
        4445: (3432, 15707, None),
        4446: (3432, 15707, None),
        20034: (13388, 9495, "10.1111/j.1502-3885.2004.tb01142.x"),
        52082: (28072, 16469, None),
    }
    for did, (sid, pid, doi) in expected.items():
        row = by_id[did]
        primary = row["returned_native_publication_inventory"]["primary"][0]
        assert row["native_site_id"] == sid
        assert primary["native_dataset_relation"] == {
            "datasetid": did,
            "siteid": sid,
            "primary": True,
        }
        assert primary["native_publication"]["publicationid"] == pid
        assert primary["native_publication"]["doi"] == doi
        assert primary["native_publication"]["citation"].strip()
    assert [
        row["citation_key"]
        for row in result["existing_policy_citation_account"]["preferred_citations"]
    ] == ["Williams_Grimm_2018", "Fyfe_2009", "Giesecke_2014"]


@pytest.mark.parametrize(
    "mutation",
    [
        "bool_id",
        "zero_id",
        "negative_id",
        "string_id",
        "string_primary",
        "integer_primary",
        "null_primary",
        "blank_citation",
        "null_citation",
        "wrong_dataset",
        "wrong_site",
        "only_secondary",
        "empty",
        "failed_wrapper",
        "missing_wrapper",
        "duplicate_id",
        "duplicate_relation",
    ],
)
def test_native_publication_refusals_use_actual_source_shape(
    captured_repository, mutation
):
    inputs = load_inputs(captured_repository)
    body = copy.deepcopy(inputs[PREFIX + "dataset-52082.json"])
    publication = body["data"][0]["publication"]
    relation = publication["datasets"][0]
    if mutation.endswith("_id") and mutation not in ("duplicate_id",):
        publication["publicationid"] = {
            "bool_id": True,
            "zero_id": 0,
            "negative_id": -1,
            "string_id": "16469",
        }[mutation]
    elif mutation.endswith("_primary"):
        relation["primary"] = {
            "string_primary": "true",
            "integer_primary": 1,
            "null_primary": None,
        }[mutation]
    elif mutation == "blank_citation":
        publication["citation"] = "  "
    elif mutation == "null_citation":
        publication["citation"] = None
    elif mutation == "wrong_dataset":
        relation["datasetid"] = 4445
    elif mutation == "wrong_site":
        relation["siteid"] = 37925
    elif mutation == "only_secondary":
        relation["primary"] = False
    elif mutation == "empty":
        body["data"] = []
    elif mutation == "failed_wrapper":
        body["status"] = "failure"
    elif mutation == "missing_wrapper":
        body["data"][0] = {}
    elif mutation == "duplicate_id":
        body["data"].append(copy.deepcopy(body["data"][0]))
    elif mutation == "duplicate_relation":
        publication["datasets"].append(copy.deepcopy(relation))
    result = assess_publications(body, 52082, 28072)
    assert result["attribution_complete"] is False
    if mutation == "only_secondary":
        assert len(result["secondary"]) == 1 and result["refusals"] == []
    elif mutation == "empty":
        assert result["empty_publication_response"] is True and result["refusals"] == []
    else:
        assert result["refusals"]


def test_shared_article_is_valid_across_distinct_native_core_relations(
    captured_repository,
):
    inventory = publication_inventory(load_inputs(captured_repository))
    assert (
        inventory[4445]["primary"][0]["native_publication"]["publicationid"]
        == inventory[4446]["primary"][0]["native_publication"]["publicationid"]
        == 15707
    )
    assert (
        inventory[4445]["primary"][0]["native_dataset_relation"]["datasetid"]
        != inventory[4446]["primary"][0]["native_dataset_relation"]["datasetid"]
    )


@pytest.mark.parametrize(
    "mutation,reason",
    [
        ("terminal_plan", "terminal authority"),
        ("terminal_exit_bool", "terminal authority"),
        ("missing_resource_field", "terminal authority"),
        ("terminal_output", "output identity"),
        ("raw_terminal_member", "returned-source identity"),
        ("qualification_summary", "summary population"),
        ("dataset_axis_bool", "dataset axis"),
        ("core_metadata", "core metadata"),
        ("relation_assessment", "relation assessment"),
        ("policy_identity", "public-policy identity"),
        ("census_scope", "census scope"),
        ("claimed_fresh_policy", "new retrieval"),
    ],
)
def test_changed_publication_capture_authority_refuses(
    captured_repository, mutation, reason
):
    inputs = copy.deepcopy(load_inputs(captured_repository))
    acquisition = inputs[PREFIX + "acquisition.json"]
    qualified = inputs[PREFIX + "qualification.json"]
    terminal = inputs[PREFIX + "acquisition-terminal.json"]
    if mutation == "terminal_plan":
        terminal["plan_sha256"] = "0" * 64
    elif mutation == "terminal_exit_bool":
        terminal["native_exit_code"] = False
    elif mutation == "missing_resource_field":
        del terminal["resource_failure"]
    elif mutation == "terminal_output":
        terminal["product_files"]["consumer-result.json"]["sha256"] = "0" * 64
    elif mutation == "raw_terminal_member":
        terminal["product_files"]["dataset-52082-publications.response"]["sha256"] = (
            "0" * 64
        )
    elif mutation == "qualification_summary":
        qualified["native_primary_publication_count"] += 1
    elif mutation == "dataset_axis_bool":
        acquisition["records"][0]["native_dataset_id"] = True
    elif mutation == "core_metadata":
        qualified["records"][0]["source_core"]["native_site_id"] += 1
    elif mutation == "relation_assessment":
        qualified["records"][0]["primary"] = []
    elif mutation == "policy_identity":
        acquisition["existing_policy_citation_account"][
            "existing_actual_HTTP200_policy_bytes"
        ]["neotoma"]["sha256"] = "0" * 64
        qualified["existing_policy_citation_account"] = copy.deepcopy(
            acquisition["existing_policy_citation_account"]
        )
    elif mutation == "census_scope":
        qualified["original_census_receipt_scope"] = "fully admitted"
    elif mutation == "claimed_fresh_policy":
        acquisition["existing_policy_citation_account"][
            "policy_retrieval_fresh_in_this_job"
        ] = True
        qualified["existing_policy_citation_account"] = copy.deepcopy(
            acquisition["existing_policy_citation_account"]
        )
    with pytest.raises(ValueError, match=reason):
        publication_inventory(inputs)


@pytest.mark.parametrize("name", [*PUBLICATION_CAPTURE_PINS, DESCRIPTOR])
def test_added_publication_sources_and_descriptor_are_byte_pinned(
    captured_repository, name
):
    path = captured_repository / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        load_inputs(captured_repository)
