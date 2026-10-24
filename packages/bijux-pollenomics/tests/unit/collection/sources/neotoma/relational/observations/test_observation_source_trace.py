"""Trace one pinned source observation into its materialized relational row."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.relational.identifiers import digest
from tests.support.neotoma.relational_shapes import nested, rows
from tests.support.repository import REPOSITORY_ROOT as ROOT

SOURCE_SNAPSHOT_ID = (
    "sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791"
)


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_pinned_observation_attributes_and_parent_ids_survive() -> None:
    raw = _json(
        ROOT / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-001.json"
    )
    source_rows = [
        row
        for row in rows(raw["rows"])
        if nested(row, "site")["siteid"] == 12
        and nested(row, "site", "collectionunit", "dataset")["datasetid"] == 12
    ]
    assert len(source_rows) == 1
    site = nested(source_rows[0], "site")
    unit = nested(site, "collectionunit")
    dataset = nested(unit, "dataset")
    samples = [
        sample for sample in rows(dataset["samples"]) if sample["sampleid"] == 355236
    ]
    assert len(samples) == 1
    datum_rows = [
        datum for datum in rows(samples[0]["datum"]) if datum.get("taxonid") == 309
    ]
    assert len(datum_rows) == 1
    datum = datum_rows[0]
    assert datum == {
        "units": "NISP",
        "value": 1,
        "context": None,
        "element": "pollen",
        "taxonid": 309,
        "symmetry": None,
        "taxongroup": "Vascular plants",
        "elementtype": "pollen",
        "variablename": "Typha latifolia",
        "ecologicalgroup": "AQVP",
    }

    materialized = _json(
        ROOT / "data/neotoma/relational/surfaces/observations/part-00002.json"
    )
    observation_id = f"neotoma:observation:355236:{digest(datum)[:20]}:1"
    observations = [
        row
        for row in rows(materialized["rows"])
        if row["observation_id"] == observation_id
    ]
    assert len(observations) == 1
    observation = observations[0]
    assert observation["source_snapshot_id"] == SOURCE_SNAPSHOT_ID
    assert observation["source_payload"] == datum
    assert observation["sample_id"] == f"neotoma:sample:{samples[0]['sampleid']}"
    assert observation["dataset_id"] == f"neotoma:dataset:{dataset['datasetid']}"
    assert observation["collection_unit_id"] == (
        f"neotoma:collection-unit:{unit['collectionunitid']}"
    )
    assert observation["site_id"] == f"neotoma:site:{site['siteid']}"
    assert observation["variable_id"] == f"neotoma:variable:{datum['taxonid']}"
    assert {
        "source_unit": observation["source_unit"],
        "source_value": observation["source_value"],
        "source_element": observation["source_element"],
        "source_element_type": observation["source_element_type"],
        "source_taxon_group": observation["source_taxon_group"],
        "source_ecological_group": observation["source_ecological_group"],
        "source_reported_name": observation["source_reported_name"],
        "source_taxon_id": observation["source_taxon_id"],
        "source_context": observation["source_context"],
    } == {
        "source_unit": datum["units"],
        "source_value": datum["value"],
        "source_element": datum["element"],
        "source_element_type": datum["elementtype"],
        "source_taxon_group": datum["taxongroup"],
        "source_ecological_group": datum["ecologicalgroup"],
        "source_reported_name": datum["variablename"],
        "source_taxon_id": datum["taxonid"],
        "source_context": datum["context"],
    }
    assert observation["unit_family"] == "count"
    assert observation["aggregation_key"] == "neotoma:exact-unit:NISP"
    assert observation["detection_status"] == "reported_value"
    assert observation["source_denominator"] is None
    assert observation["denominator_status"] == "not_provided_by_source"
