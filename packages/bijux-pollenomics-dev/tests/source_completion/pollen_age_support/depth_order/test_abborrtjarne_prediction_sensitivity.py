"""Controlled native rows and frozen predictions, without real ABBO outcomes."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_membership as ledger,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    abborrtjarne_prediction_sensitivity as adapter,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources as native,
)


@pytest.fixture
def controlled() -> tuple[
    list[dict[str, str]], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    rows, samples = [], []
    for index in range(107):
        age = [1750, 2250, 2750, 4750][index] if index < 4 else 6000 + index
        counts = dict.fromkeys(adapter.TAXA, 1) if index == 0 else {adapter.TAXA[0]: 1}
        counts["Pinus"] = 1
        datum = [
            {
                "element": "pollen",
                "elementtype": "pollen",
                "units": "NISP",
                "context": None,
                "variablename": name,
                "taxonid": ordinal,
                "value": count,
            }
            for ordinal, (name, count) in enumerate(counts.items(), start=1)
        ]
        samples.append(
            {
                "sampleid": index,
                "analysisunitid": index,
                "depth": index,
                "ages": [{"agetype": native.CALIBRATED_BP, "age": age}],
                "datum": datum,
            }
        )
        rows.append(
            dict(
                zip(
                    ledger.SUPPORT_FIELDS,
                    [
                        f"neotoma:sample:{index}",
                        str(index),
                        str(age),
                        str(age),
                        str(age),
                        "",
                        "",
                        "outside_common_bins",
                        str(sum(counts.values())),
                        str(sum(counts.values()) - 1),
                    ],
                    strict=True,
                )
            )
        )
    raw = {
        "rows": [
            {
                "site": {
                    "siteid": 13338,
                    "dataset": {
                        "datasetid": 19913,
                        "datasettype": "pollen",
                        "database": "European Pollen Database",
                    },
                    "collectionunit": {
                        "dataset": {"datasetid": 19913, "samples": samples}
                    },
                }
            }
        ]
    }
    predictions, fits = [], []
    for b in adapter.BINS:
        for index, method in enumerate(adapter.METHODS):
            fraction = dict.fromkeys(adapter.TAXA, 0.0)
            fraction[adapter.TAXA[0]] = [1.0, 0.0, 0.5, 0.25][index]
            fraction[adapter.TAXA[1]] = 1.0 - fraction[adapter.TAXA[0]]
            predictions.append(
                {
                    "bin_id": b,
                    "candidate_id": method,
                    "target_dataset_id": "19913",
                    "target_site_id": "13338",
                    "target_coordinate_used": {
                        "latitude": 63.88333,
                        "longitude": 14.45,
                    },
                    "target_outcome_input": "target count profile was not opened by this prediction process",
                    "taxon_denominator": list(adapter.TAXA),
                    "predicted_fractions": fraction,
                    "training_dataset_ids": ["53995", "54001"],
                }
            )
            fit = {
                "bin_id": b,
                "method": method,
                "training_dataset_ids": ["53995", "54001"],
                "training_site_ids": ["28869", "28872"],
                "training_manifest_sha256": "a" * 64,
            }
            if method == "clr_rbf_ridge":
                fit.update(model_sha256="b" * 64, prediction_sha256="c" * 64)
            fits.append(fit)
    frozen = {
        "schema_version": "swedish-direct-pollen-held-out-predictions.v1",
        "target_dataset_id": "19913",
        "target_site_id": "13338",
        "predictions": predictions,
        "fit_records": fits,
    }
    config = {
        "closed_taxa": list(adapter.TAXA),
        "common_age_bin_ids": list(adapter.BINS),
        "methods": list(adapter.METHODS),
        "age_bin_width_cal_bp": 500,
    }
    return rows, raw, frozen, config


def _support(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=ledger.SUPPORT_FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _bytes(value: Any) -> bytes:
    return json.dumps(value).encode()


def test_complete_controlled_adapter_preserves_source_axis_and_compacts_witnesses(
    controlled: Any,
) -> None:
    rows, raw, frozen, config = controlled
    result = adapter.derive(_support(rows), _bytes(raw), _bytes(frozen), _bytes(config))
    assert len(result["sample_order"]) == 107
    assert result["taxon_axis"] == list(adapter.TAXA)
    assert len(result["bins"]) == 4
    assert result["native_age_order"]["attainable"]
    for row in result["bins"]:
        assert row["feasible_block_count"] == row["scored_block_count"] == 1
        assert len(row["method_mae_bounds"]) == 4
        assert len(row["paired_mae_difference_bounds"]) == 6
        assert not row["unique_winner_changes"] and not row["winner_set_changes"]
        assert row["possible_winners"]
        assert len(row["attaining_allocations"]) == 1
        for allocation in row["attaining_allocations"].values():
            assert len(allocation["pooled_taxon_counts"]) == 16
            assert len(allocation["age_order"]["ages_in_source_order"]) == 107
        for bound in row["method_mae_bounds"] + row["paired_mae_difference_bounds"]:
            for endpoint in (bound["lower"], bound["upper"]):
                assert endpoint["allocation"] in row["attaining_allocations"]
                assert type(endpoint["value"]["numerator"]) is int
        for winners in row["winner_sets"]:
            assert winners["minimum_mae"]["allocation"] in row["attaining_allocations"]
    assert _bytes(result).count(b'"sample_id"') == 107
    assert len(_bytes(result)) < 100_000
    assert "structural-zero" in result["zero_semantics"]
    assert "No whole-study" in result["limits"][1]


@pytest.mark.parametrize("mode", ["inconsistent", "empty"])
def test_complete_source_refusals_remain_explicit(controlled: Any, mode: str) -> None:
    rows, raw, frozen, config = deepcopy(controlled)
    samples = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"]
    for index, (row, sample) in enumerate(zip(rows, samples, strict=True)):
        if mode == "inconsistent":
            row["depth_cm"] = str(-index)
            sample["depth"] = -index
        else:
            age = 6000 + index
            row["neotoma_age_cal_bp"] = str(age)
            row["legacyage_min_cal_bp"] = str(age)
            row["legacyage_max_cal_bp"] = str(age)
            sample["ages"][0]["age"] = age
    result = adapter.derive(_support(rows), _bytes(raw), _bytes(frozen), _bytes(config))
    assert result["native_age_order"]["attainable"] == (mode == "empty")
    for row in result["bins"]:
        assert row["refusal"] == (
            "native_age_order_infeasible"
            if mode == "inconsistent"
            else "no_feasible_nonempty_selection"
        )
        assert not row["scored_block_count"] and not row["possible_winners"]
        assert not row["attaining_allocations"]
        if mode == "empty":
            assert len(row["empty_selection_age_order"]["ages_in_source_order"]) == 107


@pytest.mark.parametrize(
    "change",
    [
        "depth",
        "age",
        "sample_id",
        "duplicate_sample",
        "closed_total",
        "all_total",
        "null",
        "missing",
        "bool",
        "nonintegral",
        "duplicate_pair",
        "unit",
    ],
)
def test_native_source_semantic_changes_refuse_before_scoring(
    controlled: Any, change: str
) -> None:
    rows, raw, _, _ = deepcopy(controlled)
    samples = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"]
    sample = samples[0]
    datum = sample["datum"][0]
    if change == "depth":
        sample["depth"] += 1
    elif change == "age":
        sample["ages"][0]["age"] += 1
    elif change == "sample_id":
        sample["sampleid"] = 999
    elif change == "duplicate_sample":
        samples.append(deepcopy(sample))
    elif change == "closed_total":
        datum["value"] += 1
    elif change == "all_total":
        sample["datum"][-1]["value"] += 1
    elif change == "null":
        datum["value"] = None
    elif change == "missing":
        del datum["value"]
    elif change == "bool":
        datum["value"] = True
    elif change == "nonintegral":
        datum["value"] = 0.5
    elif change == "duplicate_pair":
        sample["datum"].append(deepcopy(datum))
    elif change == "unit":
        datum["units"] = "percentage"
    with pytest.raises(ValueError):
        adapter._native_counts(raw, rows)


@pytest.mark.parametrize(
    "admitted", ["integral_float", "context", "same_name_other_id_zero"]
)
def test_native_counts_reuse_maintained_measurement_and_aggregation_contract(
    controlled: Any, admitted: str
) -> None:
    rows, raw, _, _ = deepcopy(controlled)
    expected = adapter._native_counts(raw, rows)
    sample = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][0]
    datum = sample["datum"][0]
    if admitted == "integral_float":
        for row in sample["datum"]:
            row["value"] = float(row["value"])
    elif admitted == "context":
        datum["context"] = "retained literal context"
    else:
        duplicate_name = {**datum, "taxonid": 999999, "value": 0}
        sample["datum"].append(duplicate_name)
    assert adapter._native_counts(raw, rows) == expected


@pytest.mark.parametrize(
    "change",
    [
        "target",
        "train_target",
        "axis",
        "unknown_method",
        "duplicate",
        "missing_bin",
        "nonfinite",
        "null",
        "unclosed",
        "fit_identity",
        "fit_target",
    ],
)
def test_frozen_prediction_identity_or_support_changes_refuse(
    controlled: Any, change: str
) -> None:
    _, _, frozen, config = deepcopy(controlled)
    prediction = frozen["predictions"][0]
    if change == "target":
        prediction["target_site_id"] = "28869"
    elif change == "train_target":
        prediction["training_dataset_ids"] = ["19913", "54001"]
    elif change == "axis":
        prediction["taxon_denominator"] = list(reversed(adapter.TAXA))
    elif change == "unknown_method":
        prediction["candidate_id"] = "unreviewed"
    elif change == "duplicate":
        frozen["predictions"][-1] = deepcopy(prediction)
    elif change == "missing_bin":
        frozen["predictions"].pop()
    elif change == "nonfinite":
        prediction["predicted_fractions"][adapter.TAXA[0]] = float("nan")
    elif change == "null":
        prediction["predicted_fractions"][adapter.TAXA[0]] = None
    elif change == "unclosed":
        prediction["predicted_fractions"][adapter.TAXA[0]] = 0.5
    elif change == "fit_identity":
        frozen["fit_records"][0]["training_manifest_sha256"] = ""
    elif change == "fit_target":
        frozen["fit_records"][0]["training_site_ids"] = ["13338", "28872"]
    with pytest.raises(ValueError):
        adapter._predictions(frozen, config)


@pytest.mark.parametrize("changes", [False, True])
def test_run_reads_each_input_once_and_requires_stable_committed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changes: bool
) -> None:
    (tmp_path / "artifacts").mkdir()
    contents = {path: str(path).encode() for path in adapter.INPUTS}
    for relative, body in contents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    monkeypatch.setattr(
        adapter,
        "INPUTS",
        {path: hashlib.sha256(body).hexdigest() for path, body in contents.items()},
    )
    revisions = iter(["a" * 40, ("b" if changes else "a") * 40])
    monkeypatch.setattr(adapter, "_revision", lambda _: next(revisions))
    monkeypatch.setattr(adapter, "derive", lambda *args: {"controlled": True})
    reads: list[Path] = []
    original = Path.read_bytes

    def read_once(path: Path) -> bytes:
        reads.append(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read_once)
    output = tmp_path / "artifacts/result.json"
    if changes:
        with pytest.raises(ValueError, match="source changed"):
            adapter.run(tmp_path, output)
        assert not output.exists()
    else:
        result = adapter.run(tmp_path, output)
        assert result["source_git_revision"] == "a" * 40
        assert result["controlled"] and len(result["input_identities"]) == 4
        assert json.loads(output.read_text()) == result
    assert reads.count(tmp_path / adapter.RAW) == 1
    assert len(reads) == 4


def test_raw_integrity_and_duplicate_json_fields_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "artifacts").mkdir()
    raw = tmp_path / adapter.RAW
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"changed")
    monkeypatch.setattr(adapter, "_revision", lambda _: "a" * 40)
    with pytest.raises(ValueError, match="input identity differs"):
        adapter.run(tmp_path, tmp_path / "artifacts/result.json")
    with pytest.raises(ValueError, match="Duplicate source"):
        adapter._json(b'{"a":1,"a":2}')
