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


def _object(value: object) -> dict[str, object]:
    """Require a retained JSON object while preserving its mutation identity."""
    assert isinstance(value, dict) and all(isinstance(key, str) for key in value)
    return value


def _array(value: object) -> list[object]:
    """Require a retained JSON array while preserving its mutation identity."""
    assert isinstance(value, list)
    return value


def _records(value: object) -> list[dict[str, object]]:
    """Admit saved records without replacing the objects under mutation."""
    return [_object(row) for row in _array(value)]


def _number(value: object) -> int | float:
    """Require an actual numerical cell before changing a retained count or value."""
    assert isinstance(value, (int, float)) and type(value) in (int, float)
    return value


def _text(value: object) -> str:
    """Require an actual citation or chronology label before reading its text."""
    assert isinstance(value, str)
    return value


@pytest.fixture
def captured_repository(tmp_path: Path) -> Path:
    """Provide captured repository for the retained source contract."""
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
    captured_repository: Path,
) -> None:
    """Verify qualified native citations preserve exact relations and nulls."""
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
    by_id = {row["native_dataset_id"]: row for row in _records(result["datasets"])}
    expected = {
        4445: (3432, 15707, None),
        4446: (3432, 15707, None),
        20034: (13388, 9495, "10.1111/j.1502-3885.2004.tb01142.x"),
        52082: (28072, 16469, None),
    }
    for did, (sid, pid, doi) in expected.items():
        row = _object(by_id[did])
        primary = _object(
            _array(_object(row["returned_native_publication_inventory"])["primary"])[0]
        )
        assert row["native_site_id"] == sid
        assert primary["native_dataset_relation"] == {
            "datasetid": did,
            "siteid": sid,
            "primary": True,
        }
        assert _object(primary["native_publication"])["publicationid"] == pid
        assert _object(primary["native_publication"])["doi"] == doi
        assert _text(_object(primary["native_publication"])["citation"]).strip()
    assert [
        row["citation_key"]
        for row in _records(
            _object(result["existing_policy_citation_account"])["preferred_citations"]
        )
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
    captured_repository: Path, mutation: str
) -> None:
    """Verify native publication refusals use actual source shape."""
    inputs = load_inputs(captured_repository)
    body = _object(copy.deepcopy(inputs[PREFIX + "dataset-52082.json"]))
    publication = _object(_object(_array(body["data"])[0])["publication"])
    relation = _object(_array(publication["datasets"])[0])
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
        _array(body["data"])[0] = {}
    elif mutation == "duplicate_id":
        _array(body["data"]).append(copy.deepcopy(_array(body["data"])[0]))
    elif mutation == "duplicate_relation":
        _array(publication["datasets"]).append(copy.deepcopy(relation))
    result = assess_publications(body, 52082, 28072)
    assert result["attribution_complete"] is False
    if mutation == "only_secondary":
        assert len(_array(result["secondary"])) == 1 and result["refusals"] == []
    elif mutation == "empty":
        assert result["empty_publication_response"] is True and result["refusals"] == []
    else:
        assert result["refusals"]


def test_shared_article_is_valid_across_distinct_native_core_relations(
    captured_repository: Path,
) -> None:
    """Verify shared article is valid across distinct native core relations."""
    inventory = publication_inventory(load_inputs(captured_repository))
    assert (
        _object(
            _object(_array(_object(inventory[4445])["primary"])[0])[
                "native_publication"
            ]
        )["publicationid"]
        == _object(
            _object(_array(_object(inventory[4446])["primary"])[0])[
                "native_publication"
            ]
        )["publicationid"]
        == 15707
    )
    assert (
        _object(
            _object(_array(_object(inventory[4445])["primary"])[0])[
                "native_dataset_relation"
            ]
        )["datasetid"]
        != _object(
            _object(_array(_object(inventory[4446])["primary"])[0])[
                "native_dataset_relation"
            ]
        )["datasetid"]
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
    captured_repository: Path, mutation: str, reason: str
) -> None:
    """Verify changed publication capture authority refuses."""
    inputs = copy.deepcopy(load_inputs(captured_repository))
    acquisition = _object(inputs[PREFIX + "acquisition.json"])
    qualified = _object(inputs[PREFIX + "qualification.json"])
    terminal = _object(inputs[PREFIX + "acquisition-terminal.json"])
    if mutation == "terminal_plan":
        terminal["plan_sha256"] = "0" * 64
    elif mutation == "terminal_exit_bool":
        terminal["native_exit_code"] = False
    elif mutation == "missing_resource_field":
        del terminal["resource_failure"]
    elif mutation == "terminal_output":
        _object(_object(terminal["product_files"])["consumer-result.json"])[
            "sha256"
        ] = "0" * 64
    elif mutation == "raw_terminal_member":
        _object(
            _object(terminal["product_files"])["dataset-52082-publications.response"]
        )["sha256"] = "0" * 64
    elif mutation == "qualification_summary":
        qualified["native_primary_publication_count"] = (
            _number(qualified["native_primary_publication_count"]) + 1
        )
    elif mutation == "dataset_axis_bool":
        _object(_array(acquisition["records"])[0])["native_dataset_id"] = True
    elif mutation == "core_metadata":
        _object(_object(_array(qualified["records"])[0])["source_core"])[
            "native_site_id"
        ] = (
            _number(
                _object(_object(_array(qualified["records"])[0])["source_core"])[
                    "native_site_id"
                ]
            )
            + 1
        )
    elif mutation == "relation_assessment":
        _object(_array(qualified["records"])[0])["primary"] = []
    elif mutation == "policy_identity":
        _object(
            _object(
                _object(acquisition["existing_policy_citation_account"])[
                    "existing_actual_HTTP200_policy_bytes"
                ]
            )["neotoma"]
        )["sha256"] = "0" * 64
        qualified["existing_policy_citation_account"] = copy.deepcopy(
            acquisition["existing_policy_citation_account"]
        )
    elif mutation == "census_scope":
        qualified["original_census_receipt_scope"] = "fully admitted"
    elif mutation == "claimed_fresh_policy":
        _object(acquisition["existing_policy_citation_account"])[
            "policy_retrieval_fresh_in_this_job"
        ] = True
        qualified["existing_policy_citation_account"] = copy.deepcopy(
            acquisition["existing_policy_citation_account"]
        )
    with pytest.raises(ValueError, match=reason):
        publication_inventory(inputs)


@pytest.mark.parametrize("name", [*PUBLICATION_CAPTURE_PINS, DESCRIPTOR])
def test_added_publication_sources_and_descriptor_are_byte_pinned(
    captured_repository: Path, name: str
) -> None:
    """Verify added publication sources and descriptor are byte pinned."""
    path = captured_repository / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        load_inputs(captured_repository)
