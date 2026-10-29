"""Artificial whole-site API, conditional refusal and prediction-freeze boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)

ROOT = Path.cwd()
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT",
    ROOT
    / "docs/report/pollen-reconstruction/author-lra-constrained/temporal-development",
)
API = runpy.run_path(str(SOURCE / "replay.py"), run_name="temporal_replay_tests")
TOPOLOGY = runpy.run_path(
    str(SOURCE / "topology.py"), run_name="temporal_topology_tests"
)
FIXTURE = runpy.run_path(
    str(
        ROOT
        / "packages/bijux-pollenomics/tests/unit/analysis/lra_validation/experiments/test_inputs.py"
    ),
    run_name="temporal_input_schema_fixture",
)
TAXA = ["Taxon" + str(index) for index in range(30)]


def store(root: Path, name: str, value: Any) -> dict[str, Any]:
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    (root / name).write_bytes(raw)
    return {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}


def fixture(root: Path, window: int) -> tuple[dict[str, Any], dict[str, Any]]:
    n, younger, older, label = TOPOLOGY["WINDOWS"][window]
    experiment = FIXTURE["fixture_inputs"](root, count=n)
    experiment["profile"] = "source-observations-withheld-site-baselines-v1"
    template = experiment["request_template"]
    template.update(
        data_kind="source_observations",
        method_profile="ring-taxon-preserving",
        taxa=TAXA,
        parameters=[
            {"taxon": taxon, "fallspeed_m_s": 0.024, "ppe": 1, "ppe_sd": 0}
            for taxon in TAXA
        ],
    )
    template["configuration"] = {
        "seed": 7,
        "love": {
            "method": "optimized",
            "stochastic": False,
            "max_ring": 2,
            "repeats": 1,
            "distance_weighting": "gpm neutral",
            "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
            "optimized_profile": "ring-taxon-preserving",
            "optimizer_backend": "scipy.slsqp-simplex-uniform",
            "optimizer_iterations": 300,
            "optimizer_max_evaluations": 16000,
            "optimizer_tolerance": 1e-8,
        },
        "reveals": {
            "stochastic": False,
            "iterations": 2,
            "distance_weighting": "gpm neutral",
            "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
        },
    }
    template["temporal_matching"]["bins"] = [
        {"bin_id": "author-TW" + str(window), "younger_bp": younger, "older_bp": older}
    ]
    for index, site in enumerate(experiment["sites"]):
        original = site["site_id"]
        site_id = "ARTIFICIAL" + str(index)
        site.update(site_id=site_id, record_id="author:" + site_id)
        metadata = {
            "site_id": site_id,
            "sample_id": site_id + ":TW" + str(window),
            "coordinate": label,
            "bin_id": "author-TW" + str(window),
            "age_type": "calendar_bp",
            "age_support_bp": [[younger, older]],
            "chronology_evidence_id": "chronology",
        }
        raw = {
            "data_kind": "source_observations",
            "taxa": TAXA,
            "sample": dict(metadata, counts=[600 + index, 400 - index, *([0] * 28)]),
        }
        site["raw"] = store(root, original + "-raw.json", raw)
        geometry = json.loads((root / site["geometry"]["path"]).read_bytes())
        geometry["sample_metadata"] = metadata
        geometry["inversion_rings"].append(deepcopy(geometry["forward_rings"][2]))
        site["geometry"] = store(root, site["geometry"]["path"], geometry)
    experiment["regional_priority"] = [s["record_id"] for s in experiment["sites"]]
    store(root, "experiment.json", experiment)
    profile = {
        "taxa": TAXA,
        "parameters_sha256": TOPOLOGY["digest"](template["parameters"]),
        "configuration": template["configuration"],
    }
    return experiment, profile


@pytest.mark.parametrize(
    "window,n,logical,unique", [(4, 13, 143, 23), (6, 14, 168, 25)]
)
def test_complete_artificial_request_api_and_whole_site_topology(
    tmp_path: Path, window: int, n: int, logical: int, unique: int
) -> None:
    experiment, profile = fixture(tmp_path / "inputs", window)
    topology = TOPOLOGY["build"](
        SourceExperimentSpec(experiment), tmp_path / "inputs", window, profile
    )
    counts = topology["manifest"]["counts"]
    assert counts == {
        "sites": n,
        "folds": n,
        "logical_requests": logical,
        "unique_requests": unique,
        "prediction_slots": 3 * n,
    }
    assert len({item.item_id for item in topology["numeric"].values()}) == unique
    for context in topology["contexts"]:
        target = set(context["fold"].test_record_ids)
        assert target.isdisjoint(context["fold"].train_record_ids)
        assert all(
            site.record.record_id not in target for site in context["predictors"]
        )
    changed = deepcopy(experiment)
    changed["sites"][0]["identity_keys"] = ["same-core"]
    changed["sites"][1]["identity_keys"] = ["same-core"]
    with pytest.raises(ValueError, match="whole physical site"):
        TOPOLOGY["build"](
            SourceExperimentSpec(changed), tmp_path / "inputs", window, profile
        )


@pytest.mark.parametrize("window", [4, 6])
def test_mixed_baselines_freeze_before_any_outcome_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, window: int
) -> None:
    prepared = tmp_path / "inputs"
    experiment, profile = fixture(prepared, window)
    spec = SourceExperimentSpec(experiment)
    topology = TOPOLOGY["build"](spec, prepared, window, profile)
    namespace = API["run"].__globals__
    authority_pin = {
        "path": str(tmp_path / "authority.json"),
        "sha256": "f" * 64,
        "bytes": 1,
    }
    observed = {**topology["manifest"], "projected_authority": authority_pin}
    request = API["write"](tmp_path / "requests.json", observed)
    preflight = API["write"](
        tmp_path / "metadata-preflight.json",
        {
            "schema_version": "development-input-isolation-metadata-preflight.v1",
            "approved": True,
            "source_inputs_before_after_unchanged": True,
            "candidate": "c" * 40,
            "scientific_api_calls": 0,
            "fits": 0,
            "host_version": "0.1.9.dev123",
            "lra_version": "0.1.9.dev456",
        },
    )
    input_rows = []
    for path in prepared.iterdir():
        raw = path.read_bytes()
        input_rows.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        )
    existing = runpy.run_path(
        str(
            ROOT
            / "docs/report/pollen-reconstruction/author-lra-constrained/cohort-development/replay.py"
        ),
        run_name="temporal_artificial_outcome",
    )
    real_outcome = existing["outcome_counts"]
    output = tmp_path / "output"
    output.mkdir()
    accesses: list[str] = []

    def outcome(*args: Any, **kwargs: Any) -> Any:
        frozen = json.loads((output / "prediction-freeze.json").read_bytes())
        assert (
            len(frozen["slots"]) == topology["manifest"]["counts"]["prediction_slots"]
        )
        assert (output / "outcome-access.jsonl").stat().st_size > 0
        accesses.append("after complete frozen inventory")
        return real_outcome(*args, **kwargs)

    existing["outcome_counts"] = outcome
    monkeypatch.setitem(namespace, "libraries", lambda *_: (TOPOLOGY, existing))
    monkeypatch.setitem(namespace, "admitted", lambda *_: ({}, input_rows))
    binding = SimpleNamespace(version="0.1.9.dev456")
    identity = SimpleNamespace(
        payload=lambda: {"runtime_environment": {"bijux-pollenomics": "0.1.9.dev123"}}
    )
    monkeypatch.setitem(namespace, "load_engine", lambda **_: binding)
    monkeypatch.setitem(namespace, "capture_code_identity", lambda *_: identity)
    monkeypatch.setitem(namespace, "verify_code_identity", lambda *_: None)
    items = [
        SimpleNamespace(
            request_sha256=checksum, item_status="completed", product=object()
        )
        for checksum in topology["numeric"]
    ]
    for item in items:
        item.as_dict = lambda: {"item_status": "completed"}
    batch = SimpleNamespace(
        items=items, interrupted=False, as_dict=lambda: {"artificial_batch": True}
    )
    monkeypatch.setitem(namespace, "run_lra_batch", lambda *_args, **_kwargs: batch)
    compositions = dict.fromkeys(TAXA, 1 / 30)
    monkeypatch.setitem(
        namespace,
        "extract_reconstruction",
        lambda *_: (compositions, tuple([1 / 30] * 30), {}),
    )

    def predict(
        one: Any, fold: Any, target: Any, _fits: Any, _groups: Any, **_kwargs: Any
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        baseline = one.baselines[0]
        if baseline == "nearest_site":
            raise ValidationRefusal(
                "forward_model_refused",
                "Forward deposition has nonfinite or zero total mass",
            )
        return [
            {
                "fold_id": fold.fold_id,
                "record_id": target.record.record_id,
                "baseline": baseline,
                "bin_id": "author-TW" + str(window),
                "pollen_fraction": compositions,
            }
        ], {}

    monkeypatch.setitem(namespace, "predict_fold", predict)
    report = API["run"](
        tmp_path,
        prepared,
        window,
        {"profile": profile, "maintained_sources": []},
        authority_pin,
        request,
        output,
        metadata_pin=preflight,
        candidate="c" * 40,
    )
    assert report["predicted_slots"] == 2 * len(spec.sites)
    assert report["refused_slots"] == len(spec.sites)
    assert len(report["scores"]) == 2 * len(spec.sites)
    assert len(accesses) == len(spec.sites)
    assert report["scientific_acceptance"] == "not_evaluated"
    monkeypatch.setitem(
        namespace,
        "predict_fold",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ValueError("unexpected source fault")
        ),
    )
    with pytest.raises(ValueError, match="unexpected source fault"):
        API["predictions"](
            spec, topology, {item.request_sha256: item for item in items}, prepared
        )
