"""Public projection preserves native evidence without private row witnesses."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import runpy


def test_public_projection_excludes_private_workbook_and_lookup_rows(
    tmp_path: Path,
) -> None:
    repository = next(
        path
        for path in Path(__file__).resolve().parents
        if (path / "uv.lock").is_file()
    )
    project = runpy.run_path(
        str(
            repository
            / "reports/science/pollen-reconstruction/bokesjon-pilot/project.py"
        )
    )["project"]
    study = tmp_path / "study"
    study.mkdir()
    sentinel = "PRIVATE_ROW_WITNESS"
    native, parameters = {}, {}
    for name, dataset in (("BOKE", 54001), ("KRAG", 23013)):
        native[name] = {
            "dataset_id": dataset,
            "taxon_axis": [
                {
                    "taxon_id": 1,
                    "native_label": "Betula",
                    "known_NISP_sum": 7,
                    "aggregate_all_owner_count": 7,
                    "conditional_nondetection_eligible": True,
                    "cells": [
                        {"sample_id": 2, "state": "reported_positive", "count": 7}
                    ],
                }
            ],
        }
        parameters[name] = {
            "scientific_admission": False,
            "native_taxa": [
                {"native_label": "Betula", "author_lookup_candidate": sentinel}
            ],
            "landclim_targets": [
                {
                    "target_label": "Betula",
                    "source_parameter": {"FSP (m/s)": "0.024", "PPE (SD)": "5 (0.3)"},
                    "native_exact_matches": [{"taxon_id": 1, "native_label": "Betula"}],
                    "workbook_literal_exact_matches": [sentinel],
                    "workbook_whitespace_candidate_matches": [sentinel],
                }
            ],
        }
    for name, value in (
        ("result.json", {"schema_version": "bokesjon-pilot-source-result.v1"}),
        ("native-taxa.json", native),
        ("parameters.json", parameters),
    ):
        (study / name).write_text(json.dumps(value))
    metadata = b'{"rights":{"private_workbook_licensed":false}}\n'
    (study / "metadata.json").write_bytes(metadata)
    (study / "private-workbook.json").write_text(sentinel)
    output = tmp_path / "public"

    project(study, output)

    assert {path.name for path in output.iterdir()} == {
        "native-count-slots.csv",
        "taxon-support.csv",
        "parameter-targets.csv",
        "parameter-coverage.json",
        "core-metadata.json",
    }
    assert all(sentinel.encode() not in path.read_bytes() for path in output.iterdir())
    coverage = json.loads((output / "parameter-coverage.json").read_text())
    for value in coverage.values():
        assert value["native_taxa"] == [{"native_label": "Betula"}]
        assert value["private_author_mapping_rows_published"] is False
        assert value["scientific_admission"] is False
        assert value["landclim_targets"][0]["source_parameter"] == {
            "FSP (m/s)": "0.024",
            "PPE (SD)": "5 (0.3)",
        }
        assert not any(
            key.startswith("workbook_")
            for row in value["landclim_targets"]
            for key in row
        )
    with (output / "native-count-slots.csv").open(newline="") as stream:
        slots = list(csv.DictReader(stream))
    assert [(row["core"], row["reported_count"]) for row in slots] == [
        ("BOKE", "7"),
        ("KRAG", "7"),
    ]
    assert (output / "core-metadata.json").read_bytes() == metadata
    assert (study / "private-workbook.json").read_text() == sentinel
