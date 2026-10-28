"""Conditional geographic matrix proofs and independent source-pin admission."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.verification import (
    sources,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.verification.cohort import (
    audit_cohort,
)

from . import synthetic


def test_exact_metric_ties_have_lexicographic_selection_and_zero_coverage() -> None:
    packet, _, protocol = synthetic()
    assert (
        audit_cohort(packet, protocol)["selection_order"]
        == sorted(packet["groups"])[:10]
    )


@pytest.mark.parametrize(
    "defect",
    [
        "asymmetric",
        "nonfinite",
        "boolean",
        "coordinate",
        "model",
        "step",
        "tie",
        "missing_family",
        "coverage",
        "excluded",
    ],
)
def test_cohort_binds_full_source_geometry_and_literal_policy(defect: str) -> None:
    packet, _, protocol = deepcopy(synthetic())
    cohort = packet["cohort"]
    first, second = sorted(packet["groups"])[:2]
    if defect == "asymmetric":
        cohort["distance_matrix_m"][first][second] = 1.0
    elif defect == "nonfinite":
        cohort["distance_matrix_m"][first][second] = float("nan")
    elif defect == "boolean":
        cohort["distance_matrix_m"][first][second] = False
    elif defect == "coordinate":
        packet["geometries"][first]["longitude"] = 1.0
    elif defect == "model":
        cohort["distance_model"] = "spherical"
    elif defect == "step":
        cohort["steps"][1]["candidate_values_m"][second] = 1.0
    elif defect == "tie":
        cohort["selection_order"][0], cohort["selection_order"][1] = (
            cohort["selection_order"][1],
            cohort["selection_order"][0],
        )
    elif defect == "missing_family":
        packet["groups"].pop(first)
    elif defect == "coverage":
        cohort["coverage_m"] = 1.0
    else:
        cohort["excluded"] = []
    with pytest.raises((ValueError, KeyError)):
        audit_cohort(packet, protocol)


def test_source_pin_refuses_hash_tamper_escape_and_symlink(tmp_path: Path) -> None:
    raw = b'{"owner":"literal"}'
    path = tmp_path / "source.json"
    path.write_bytes(raw)
    pin = {
        "path": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    assert sources.read_pin(tmp_path, pin) == {"owner": "literal"}
    for mutated in (
        {**pin, "sha256": "0" * 64},
        {**pin, "path": "../source.json"},
        {**pin, "bytes": True},
    ):
        with pytest.raises(ValueError):
            sources.read_pin(tmp_path, mutated)
    alias = tmp_path / "alias.json"
    alias.symlink_to(path)
    with pytest.raises(ValueError):
        sources.read_pin(tmp_path, {**pin, "path": alias.name})


@pytest.fixture(scope="module")
def projected(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    # Portable arrangement only: the maintained reader output is the candidate
    # under test, never the independent source or numerical expectation.
    from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.inputs import (
        load_inputs,
    )
    from tests.essd_reproduction.author_lra_spatial.thinning.test_inputs import _fixture

    repository, archive, protocol, old_packet, _ = _fixture(
        tmp_path_factory.mktemp("independent-thinning-source")
    )
    pins = protocol["qualified_sources"]

    def store(name: str, value: Any) -> None:
        path = repository / pins[name]["path"]
        raw = json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        path.write_bytes(raw)
        pins[name] = {
            "path": pins[name]["path"],
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    refs = {r["record_id"]: r for r in old_packet["observation_refs"]}
    metrics = dict.fromkeys(("mae_fraction", "total_variation", "hellinger"), 0.0)
    store(
        "outer_scores",
        [
            {
                "outer_target": t,
                "status": "scored",
                "selected_scale_km": 20.0,
                "observed_count": 30,
                "observed_reference": refs[t],
                "matched_baselines": dict.fromkeys(
                    ("training_mean", "nearest_site", "inverse_distance_squared"),
                    metrics,
                ),
                "metrics": metrics,
            }
            for t in sorted(old_packet["groups"])
        ],
    )
    store("choices", [])
    selection = json.loads(
        (repository / pins["selection_manifest"]["path"]).read_text()
    )
    selection["files"]["choices"] = {
        **pins["choices"],
        "path": Path(pins["choices"]["path"]).name,
    }
    store("selection_manifest", selection)
    result = json.loads((repository / pins["result"]["path"]).read_text())
    for role in ("choices", "outer_scores"):
        result["products"][role] = {**pins[role], "path": Path(pins[role]["path"]).name}
    result["selection_manifest"] = {
        **pins["selection_manifest"],
        "path": Path(pins["selection_manifest"]["path"]).name,
    }
    store("result", result)
    protocol["models"]["new_population"] = {
        "outer_folds": 10,
        "training_owners_per_fold": 9,
        "local_predictors_per_fold": 8,
        "new_prediction_slots": 50,
    }
    packet = load_inputs(repository, archive, protocol)
    counts = {t: dict.fromkeys(old_packet["taxa"], 1) for t in old_packet["groups"]}
    return repository, archive, protocol, packet, counts


@pytest.fixture
def original_join(
    monkeypatch: pytest.MonkeyPatch, projected: tuple[Any, ...]
) -> tuple[Any, ...]:
    # Existing original42-object custody is qualified independently. This seam
    # isolates NEW17-pair projection without decoding intake's sentinel outcomes.
    *_, counts = projected
    monkeypatch.setattr(
        sources,
        "bind_sources",
        lambda *_: (counts, {"passed": True, "source_objects": 42}),
    )
    return projected


def test_postfreeze_projection_binds_all_pairs_and_reference_owners(
    original_join: tuple[Any, ...],
) -> None:
    repository, archive, protocol, packet, _ = original_join
    counts, facts = sources.audit_inputs(repository, archive, protocol, packet)
    assert set(counts) == set(packet["cohort"]["selected"])
    assert facts["native_pairs"] == 17
    assert len(facts["retained_reference_metrics"]) == 10


@pytest.mark.parametrize(
    "defect",
    [
        "local_cover",
        "attempt",
        "parent",
        "forbidden",
        "native_catalogue",
        "kernel",
        "regional_double_ppe",
        "geometry",
        "reference",
        "old_ancestry",
        "new_fit_claim",
    ],
)
def test_bad_primary_join_or_foreign_dependency_cannot_self_authenticate(
    original_join: tuple[Any, ...], defect: str
) -> None:
    repository, archive, protocol, packet, _ = original_join
    packet = deepcopy(packet)
    context = packet["contexts"][0]
    if defect == "local_cover":
        context["predictors"][0]["covers_by_ring"][1] = [1.0] + [0.0] * 29
    elif defect == "attempt":
        context["predictors"][0]["selected_attempt_sha256s"][1] = "f" * 64
    elif defect == "parent":
        context["predictors"][0]["scientific_parent_ids"][1] = context["target"]
    elif defect == "forbidden":
        context["scientific_refs"]["forbidden_record_ids"] = []
    elif defect == "native_catalogue":
        packet["pair_catalogue"].pop()
    elif defect == "kernel":
        context["forward"]["forward_inputs"]["local_k"][0][0] += 0.1
    elif defect == "regional_double_ppe":
        context["forward"]["forward_inputs"]["regional_deposition"][0] *= 2
    elif defect == "geometry":
        packet["geometries"][context["target"]]["latitude"] += 0.01
    elif defect == "reference":
        packet["retained_reference_predictions"][0]["scientific_refs"] = context[
            "scientific_refs"
        ]
    elif defect == "old_ancestry":
        context["forward"]["global_bank_sha256"] = "0" * 64
    else:
        packet["summary"]["new_inverse_fits"] = 1
    with pytest.raises((ValueError, KeyError)):
        sources.audit_inputs(repository, archive, protocol, packet)
