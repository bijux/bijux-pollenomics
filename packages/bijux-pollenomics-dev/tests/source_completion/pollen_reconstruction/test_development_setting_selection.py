"""Exact joint-pair coverage, alias provenance and freeze-before-outcome contracts."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

ROOT = Path.cwd()
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT",
    ROOT / "reports/science/development-setting-selection/source",
)
CHOICE = runpy.run_path(str(SOURCE / "choice.py"))
READER = runpy.run_path(str(SOURCE / "sources.py"))
REPLAY = runpy.run_path(str(SOURCE / "replay.py"))
POLICY = json.loads((SOURCE.parent / "protocol.json").read_bytes())
ELIGIBLE = runpy.run_path(str(ROOT / POLICY["eligible_metric_source"]["path"]))[
    "eligible_metric"
]
Json = dict[str, Any]


def metric(tv: float = 0.25) -> Json:
    return {
        "status": "scored",
        "target": "pollen_composition",
        "mae_fraction": tv / 15,
        "rmse_fraction": tv / 10,
        "bias_fraction": 0.0,
        "total_variation": tv,
        "count_conditioned_deviance": 0.5,
        "zero_probability_positive_count": False,
        "signed_error_by_taxon": [[t, 0.0] for t in POLICY["taxa"]],
        "observed_total_count": 100,
        "scored_taxon_count": 30,
        "taxon_count": 30,
        "missing_observed_taxa": [],
    }


def unit() -> tuple[list[str], Json, list[Json], dict[tuple[str, str, str, str], Json]]:
    records = ["author:synthetic-" + str(i).zfill(2) for i in range(15)]
    groups = {r: "site-group:" + READER["digest"]([r]) for r in records}
    catalogue = deepcopy(POLICY["catalogue"])
    rows = {}
    for pair in catalogue:
        if pair["eligibility"] != "saved_prediction":
            continue
        for target in records[1:]:
            training = sorted(set(records) - {records[0], target})
            rows[(pair["candidate_id"], pair["spatial_id"], records[0], target)] = {
                "method": pair["method"],
                "baseline": pair["spatial_id"],
                "outer_target": records[0],
                "inner_target": target,
                "inner_train_record_ids": training,
                "inner_train_group_ids": sorted(groups[r] for r in training),
                "bin_id": "author-TW5",
                "status": "scored",
                "metrics": metric(),
                "prediction_sha256": "a" * 64,
            }
    return records, groups, catalogue, rows


def choose(value: Any) -> Json:
    records, groups, catalogue, rows = value
    result: Json = CHOICE["choose"](
        records[0], records, groups, catalogue, rows, ELIGIBLE
    )
    return result


def test_full_pair_grid_ties_candidate_then_spatial_and_retains_all_failures() -> None:
    value = unit()
    result = choose(value)
    assert result["selected_pair"] == {
        "candidate_id": "gpm-neutral-fixed-start",
        "spatial_id": "inverse_distance_squared",
        "source_candidate_id": "gpm-neutral-fixed-start",
    }
    assert len(result["ranking"]) == 32
    assert sum(r["status"] == "prerequisite_refused" for r in result["ranking"]) == 8
    value[2].reverse()
    assert choose(value)["selected_pair"] == result["selected_pair"]


def test_complete_coverage_beats_lower_partial_mean_and_all_failure_refuses() -> None:
    value = unit()
    key = next(iter(value[3]))
    for row in value[3].values():
        if (
            row["method"] == value[3][key]["method"]
            and row["baseline"] == value[3][key]["baseline"]
        ):
            row["metrics"]["total_variation"] = 0.0
    value[3][key].update(status="refused", metrics=None)
    result = choose(value)
    assert result["selected_pair"] is not None
    assert (
        result["selected_pair"]["source_candidate_id"],
        result["selected_pair"]["spatial_id"],
    ) != key[:2]
    assert all(
        r["mean_inner_total_variation"] is None
        for r in result["ranking"]
        if r["complete_inner_predictions"] < 14
    )
    for row in value[3].values():
        row.update(status="refused", metrics=None)
    refused = choose(value)
    assert refused["status"] == "refused" and refused["selected_pair"] is None
    assert len(refused["ranking"]) == 32


@pytest.mark.parametrize(
    "mode",
    [
        "missing",
        "foreign-outer",
        "outer-label",
        "nested-outer-label",
        "alias",
        "duplicate-training",
        "wrong-time",
        "unknown-pair",
        "duplicate-catalogue",
        "invalid-metric",
        "refused-with-score",
    ],
)
def test_foreign_or_incomplete_choice_input_refuses(mode: str) -> None:
    value = unit()
    records, groups, catalogue, rows = value
    key = next(iter(rows))
    row = rows[key]
    if mode == "missing":
        del rows[key]
    elif mode == "foreign-outer":
        row["outer_target"] = records[1]
    elif mode == "outer-label":
        row["metrics"]["outer_target_count"] = 100
        row["outer_target_count"] = 100
    elif mode == "nested-outer-label":
        row["metrics"]["outer_target_count"] = 100
    elif mode == "alias":
        groups[records[1]] = groups[records[0]]
    elif mode == "duplicate-training":
        row["inner_train_record_ids"][-1] = row["inner_train_record_ids"][0]
    elif mode == "wrong-time":
        row["bin_id"] = "author-TW4"
    elif mode == "unknown-pair":
        rows[("foreign", "method", records[0], records[1])] = row
    elif mode == "duplicate-catalogue":
        catalogue.append(catalogue[0])
    elif mode == "invalid-metric":
        row["metrics"]["total_variation"] = float("nan")
    else:
        row["status"] = "refused"
    with pytest.raises(ValueError):
        choose(value)


def write(root: Path, name: str, value: Any) -> Json:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    path.write_bytes(body)
    import hashlib

    return {
        "path": str(path),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
    }


def world(root: Path) -> Json:
    records, groups, _, _ = unit()
    protocol: Json = deepcopy(POLICY)
    protocol.update(records=records, groups=groups)
    protocol["maintained_sources"] = [
        {**r, "path": str(ROOT / r["path"])} for r in protocol["maintained_sources"]
    ]
    protocol["eligible_metric_source"]["path"] = str(
        ROOT / protocol["eligible_metric_source"]["path"]
    )
    protocol["experiment"] = write(
        root,
        "experiment.json",
        {
            "sites": [
                {
                    "record_id": r,
                    "site_id": r.removeprefix("author:"),
                    "identity_keys": [],
                }
                for r in records
            ],
            "baselines": protocol["baselines"],
        },
    )
    protocol["forecast"] = write(
        root,
        "forecast.json",
        {"grid": [{"id": r} for r in protocol["declared_setting_ids"]]},
    )
    aux = {
        "ring_support": {
            "approved": True,
            "actual_exit": 0,
            "source_derived_equivalence_admitted": True,
            "summary": {
                "equal_selected_covers": 39,
                "nominal_probability_value_projections": 675,
                "new_prediction_manifests_executed": False,
            },
        },
        "analytical": {
            "approved": True,
            "scientific_saved_products_admitted": True,
            "summary": {"ring_dispositions": 78, "raw_closed_composition_rings": 0},
        },
        "clr": {
            "approved": True,
            "scientific_saved_products_admitted": True,
            "summary": {
                "actual_expected_domain_refusals": 450,
                "successful_ridge_solves": 0,
            },
        },
        "de": {
            "approved": True,
            "scientific_saved_products_admitted": True,
            "summary": {"requests": 39, "accepted_rings": 0, "refused_rings": 78},
        },
        "de_execution": {"actual_exit": 0},
        "de_source_review": {
            "approved": True,
            "source_manifest_sha256": "6732cdae89752a7592e640e803798aeb2fb783b2ef8fbd7a6307b34505f802c2",
        },
        "legacy": {"approved": True, "summary": {"request_refusals": 39}},
        "circular_source_review": {"approved": True},
        "temporal": {"approved": True},
    }
    protocol["auxiliary"] = {
        name: write(root, "synthetic-authorities/" + name + ".json", value)
        for name, value in aux.items()
    }
    for pair in protocol["catalogue"]:
        if pair["eligibility"] == "source_equivalent_alias":
            pair["evidence"] = protocol["auxiliary"]["ring_support"]
    for axis in protocol["axes"]:
        slots, scores, outcomes, dispositions = [], [], [], []
        for method in axis["methods"]:
            for outer in records:
                for target in records:
                    kind = "outer" if target == outer else "inner"
                    training = sorted(set(records) - {target, outer})
                    fold = {
                        "train_record_ids": training,
                        "test_record_ids": [target],
                        "train_group_ids": sorted(groups[r] for r in training),
                        "test_group_ids": [groups[target]],
                    }
                    for baseline in protocol["baselines"]:
                        slot = {
                            "kind": kind,
                            "method": method,
                            "baseline": baseline,
                            "outer_target": outer,
                            "target": target,
                            "status": "predicted",
                            "fold": fold,
                            "prediction": {"prediction_manifest_sha256": "c" * 64},
                        }
                        slots.append(slot)
                        if kind == "inner":
                            scores.append(
                                {
                                    "method": method,
                                    "baseline": baseline,
                                    "outer_target": outer,
                                    "inner_target": target,
                                    "inner_train_record_ids": training,
                                    "inner_train_group_ids": fold["train_group_ids"],
                                    "bin_id": "author-TW5",
                                    "status": "scored",
                                    "metrics": metric(),
                                    "prediction_sha256": READER["digest"](slot),
                                }
                            )
                        else:
                            dispositions.append(
                                {
                                    "outer_target": outer,
                                    "method": method,
                                    "baseline": baseline,
                                    "status": "predicted",
                                }
                            )
                            outcomes.append(
                                {
                                    "outer_target": outer,
                                    "method": method,
                                    "baseline": baseline,
                                    **metric(),
                                }
                            )
        axis["candidate_freeze"] = write(
            root, axis["id"] + "/freeze.json", {"slots": slots}
        )
        axis["inner_scores"] = write(root, axis["id"] + "/inner.json", scores)
        axis["report"] = write(
            root,
            axis["id"] + "/report.json",
            {
                "candidate_freeze": axis["candidate_freeze"],
                "candidate_scores": outcomes,
                "candidate_dispositions": dispositions,
                "synthetic_outer_outcome_marker": True,
            },
        )
        authority = {
            "source_candidate": axis["source_candidate"],
            "independent_semantics": {
                "approved": True,
                "scientific_saved_products_admitted": True,
            },
            "raw_trace_products": {
                "evaluation:" + role: {k: axis[key][k] for k in ("sha256", "bytes")}
                for role, key in [
                    ("inner-scores.json", "inner_scores"),
                    ("candidate-prediction-freeze.json", "candidate_freeze"),
                    ("report.json", "report"),
                ]
            },
        }
        axis["authority"] = write(root, axis["id"] + "/authority.json", authority)
    return protocol


def test_complete_saved_reader_and_fifteen_freezes_precede_outer_decode(
    tmp_path: Path,
) -> None:
    protocol = world(tmp_path / "inputs")
    output = tmp_path / "products"
    namespace = READER["load"].__globals__
    original = namespace["decode"]
    accesses = []

    def guarded(body: bytes) -> Any:
        if b'"synthetic_outer_outcome_marker"' in body:
            assert (output / "selected-prediction-freeze.json").is_file()
            frozen = json.loads(
                (output / "selected-prediction-freeze.json").read_bytes()
            )
            assert len(frozen["choices"]) == len(frozen["slots"]) == 15
            accesses.append(True)
        return original(body)

    namespace["decode"] = guarded
    try:
        result = REPLAY["run"](ROOT, protocol, output, READER, CHOICE)
    finally:
        namespace["decode"] = original
    assert len(accesses) == 2 and result["selected_predictions"] == 15
    frozen = json.loads((output / "selected-prediction-freeze.json").read_bytes())
    assert all(
        row["source_prediction_manifest_sha256"] == "c" * 64 for row in frozen["slots"]
    )
    assert all(
        row["selected_pair"]["spatial_id"] == "inverse_distance_squared"
        for row in frozen["slots"]
    )
    evidence = json.loads((output / "selection-evidence.json").read_bytes())
    assert len(evidence["physical_inner_rows"]) == 4410
    assert all(
        "signed_error_by_taxon" in row["original_row"]["metrics"]
        for row in evidence["physical_inner_rows"]
    )


@pytest.mark.parametrize("mode", ["duplicate", "changed-nominal", "false-alias"])
def test_saved_reader_join_and_alias_evidence_refuse(mode: str, tmp_path: Path) -> None:
    protocol = world(tmp_path / "inputs")
    if mode == "false-alias":
        protocol["auxiliary"]["ring_support"] = write(
            tmp_path, "bad-proof.json", {"approved": False}
        )
        with pytest.raises((ValueError, KeyError)):
            READER["qualify_auxiliary"](ROOT, protocol)
        return
    axis = protocol["axes"][0 if mode == "duplicate" else 1]
    rows = json.loads(Path(axis["inner_scores"]["path"]).read_bytes())
    if mode == "duplicate":
        rows[1] = rows[0]
    else:
        next(r for r in rows if r["method"] == "gpm neutral")["metrics"][
            "rmse_fraction"
        ] += 0.1
    axis["inner_scores"] = write(tmp_path, "changed-inner.json", rows)
    authority = json.loads(Path(axis["authority"]["path"]).read_bytes())
    authority["raw_trace_products"]["evaluation:inner-scores.json"] = {
        k: axis["inner_scores"][k] for k in ("sha256", "bytes")
    }
    axis["authority"] = write(tmp_path, "changed-authority.json", authority)
    with pytest.raises(ValueError):
        READER["load"](ROOT, protocol)
