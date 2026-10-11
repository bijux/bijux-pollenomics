"""Source publication links remain typed, complete and non-admitting."""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake import (
    build_candidate_publication_report,
    parse_dataset_publications,
)


def _bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _response(dataset_id: int, *, primary: bool | None = True) -> bytes:
    return _bytes(
        {
            "status": "success",
            "data": [
                {
                    "publication": {
                        "publicationid": 9,
                        "citation": "Source citation",
                        "doi": None,
                        "year": "2005",
                        "pubtype": "Journal Article",
                        "author": [{"familyname": "Source author"}],
                        "datasets": [{"datasetid": dataset_id, "primary": primary}],
                    }
                }
            ],
        }
    )


def _attribution() -> dict[str, object]:
    return {
        "schema_version": "neotoma-candidate-taxon-attribution.v1",
        "publication_allowed": False,
        "lra_accepted_samples": 0,
        "source_snapshot_id": "snapshot",
        "candidate_dataset_count": 2,
        "candidate_sample_count": 3,
        "candidate_pollen_observation_count": 8,
        "dataset_rows": [
            {
                "dataset_id": "neotoma:dataset:1",
                "source_dataset_id": 1,
                "source_country_code": "SE",
                "source_constituent_database": "EPD",
                "source_doi_values": ["10.1/dataset"],
                "source_dataset_pi": [{"contactname": "Contributor"}],
                "candidate_sample_count": 2,
                "candidate_pollen_observation_count": 5,
            },
            {
                "dataset_id": "neotoma:dataset:2",
                "source_dataset_id": 2,
                "source_country_code": "NO",
                "source_constituent_database": "EPD",
                "source_doi_values": ["10.2/dataset"],
                "source_dataset_pi": [{"contactname": "Contributor"}],
                "candidate_sample_count": 1,
                "candidate_pollen_observation_count": 3,
            },
        ],
    }


def test_preserves_primary_publication_and_explicit_empty_response() -> None:
    report = build_candidate_publication_report(
        _attribution(),
        {1: _response(1), 2: _bytes({"status": "success", "data": []})},
    )
    assert report["candidate_dataset_count"] == 2
    assert report["publication_record_count"] == 1
    assert report["publication_link_status_counts"] == {
        "no_publication_link": 1,
        "one_source_primary_publication": 1,
    }
    assert report["country_dataset_denominators"]["NO"]["no_publication_link"] == 1
    assert report["country_dataset_denominators"]["DK"] == {"datasets": 0}
    assert report["rows"][0]["source_publications"][0]["source_doi"] is None
    assert report["rows"][0]["source_dataset_doi_values"] == ["10.1/dataset"]
    assert report["rights_review_status"] == "not_evaluated"
    assert report["lra_accepted_samples"] == 0
    assert report["publication_allowed"] is False


def test_refuses_mismatched_or_incomplete_source_closure() -> None:
    with pytest.raises(ValueError, match="closure differs"):
        build_candidate_publication_report(_attribution(), {1: _response(1)})
    with pytest.raises(ValueError, match="uniquely link dataset"):
        parse_dataset_publications(1, _response(2))
    response = json.loads(_response(1))
    response["data"][0]["publication"]["datasets"][0]["primary"] = "true"
    with pytest.raises(ValueError, match="not typed"):
        parse_dataset_publications(1, _bytes(response))
    response["data"][0]["publication"]["datasets"][0]["primary"] = None
    assert (
        parse_dataset_publications(1, _bytes(response))[0]["source_primary_flag"]
        is None
    )
    response["data"].append(deepcopy(response["data"][0]))
    with pytest.raises(ValueError, match="invalid or duplicate"):
        parse_dataset_publications(1, _bytes(response))
    changed = _attribution()
    changed["dataset_rows"][0]["dataset_id"] = "neotoma:dataset:99"
    with pytest.raises(ValueError, match="identity differs"):
        build_candidate_publication_report(changed, {1: _response(1), 2: _response(2)})
    changed = _attribution()
    changed["dataset_rows"][0]["source_country_code"] = "UNKNOWN"
    with pytest.raises(ValueError, match="unknown country partition"):
        build_candidate_publication_report(changed, {1: _response(1), 2: _response(2)})
