"""Small qualified source fixtures for fresh thinning roles and strict custody."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import (
    inputs as original,
)
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning import inputs
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.thinning.cohort import (
    select_cohort,
)
from tests.essd_reproduction.author_lra_spatial.test_inputs import (
    read_object,
    saved_inputs,
)


def _fixture(
    root: Path,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    repository, archive, parent = saved_inputs(root)

    def archive_value(name: str, value: Any) -> dict[str, Any]:
        body = original.canonical(value)
        sha = hashlib.sha256(body).hexdigest()
        path = archive / "objects" / sha[:2] / sha
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {"path": name, "bytes": len(body), "sha256": sha}

    catalogue = {row["path"]: row for row in parent["author_inputs"]}
    experiment = read_object(archive, catalogue["experiment.json"])
    experiment["request_template"]["evidence"] = []
    experiment_pin = archive_value("experiment.json", experiment)
    parent["author_inputs"] = [
        experiment_pin if row["path"] == "experiment.json" else row
        for row in parent["author_inputs"]
    ]
    geometry_by_record = {
        site["record_id"]: read_object(archive, catalogue[site["geometry"]["path"]])
        for site in experiment["sites"]
    }
    geometry_ref = {
        site["record_id"]: catalogue[site["geometry"]["path"]]
        for site in experiment["sites"]
    }
    frozen = read_object(archive, parent["sources"]["candidate_freeze"])
    for slot in frozen["slots"]:
        if "geometry" in slot:
            # The older custody-only fixture used a placeholder. This fixture's
            # declared .03 tail coefficient, .25 fraction, 1/30 cover and PPE2
            # require .0005; no forward engine or original study is executed.
            slot["geometry"]["forward_inputs"]["regional_deposition"] = [0.0005] * 30
            context = slot["geometry"]["forward_inputs"]
            context["parameter_input_ids"] = [
                "experiment-parameters:"
                + original.digest(
                    {
                        "parameters": experiment["request_template"]["parameters"],
                        "evidence": [],
                    }
                )
            ]
            context["geometry_input_ids"] = [
                "experiment-geometry:" + geometry_ref[slot["target"]]["sha256"]
            ]
            context["temporal_support_id"] = "experiment-time:" + original.digest(
                {
                    "metadata": geometry_by_record[slot["target"]]["sample_metadata"],
                    "matching": experiment["request_template"]["temporal_matching"],
                }
            )
    parent["sources"]["candidate_freeze"] = archive_value(
        parent["sources"]["candidate_freeze"]["path"], frozen
    )
    upstream = original.load_inputs(repository, archive, parent)
    catalogue = {row["path"]: row for row in parent["author_inputs"]}
    experiment = read_object(archive, catalogue["experiment.json"])
    geometries = {
        site["record_id"]: read_object(archive, catalogue[site["geometry"]["path"]])
        for site in experiment["sites"]
    }
    native = read_object(archive, parent["sources"]["nominal_training"])
    destination = repository / "qualified"
    destination.mkdir()

    def store(name: str, value: Any, *, raw: bool = False) -> dict[str, Any]:
        body = value if raw else original.canonical(value)
        (destination / name).write_bytes(body)
        return {
            "path": "qualified/" + name,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }

    def member(pin: dict[str, Any]) -> dict[str, Any]:
        return {**pin, "path": Path(pin["path"]).name}

    pins = {
        "protocol": store("protocol.json", parent),
        "inputs": store("inputs.json", upstream),
    }
    nominal = {
        "passed": True,
        "failures": [],
        "contexts": 225,
        "forward_calls": 675,
        "reference_baselines": 675,
        "vegetation_comparisons": 675,
        "pollen_comparisons": 675,
        "maximum_vegetation_absolute_error": 0.0,
        "maximum_pollen_absolute_error": 0.0,
        "absolute_tolerance": 1e-12,
    }
    pins["nominal"] = store("nominal.json", nominal)
    candidates = []
    for context in upstream["contexts"]:
        source = context["reference_baselines"][0]
        for scale in (20.0, 100.0):
            candidates.append(
                {
                    "context_id": context["context_id"],
                    "kind": context["kind"],
                    "target": context["target"],
                    "outer_target": context["outer_target"],
                    "length_scale_km": scale,
                    "scientific_refs": context["scientific_refs"],
                    "status": "predicted",
                    "vegetation_fraction": [
                        source["vegetation_fraction"][taxon]
                        for taxon in upstream["taxa"]
                    ],
                    "pollen_fraction": [
                        source["pollen_fraction"][taxon] for taxon in upstream["taxa"]
                    ],
                }
            )
    pins["candidates"] = store("candidates.json", candidates)
    pins["prediction_manifest"] = store(
        "prediction-manifest.json",
        {
            "schema_version": "author-spatial-prediction-freeze.v1",
            "files": {
                name: member(pins[name]) for name in ("inputs", "nominal", "candidates")
            },
        },
    )
    # These are deliberately not JSON: intake must authenticate, never decode them.
    pins["choices"] = store(
        "choices.json", b"unopened prior selection losses", raw=True
    )
    pins["outer_scores"] = store(
        "outer-scores.json", b"unopened prior target outcomes", raw=True
    )
    pins["selection_manifest"] = store(
        "selection-manifest.json",
        {
            "schema_version": "author-spatial-selection-freeze.v1",
            "files": {"choices": member(pins["choices"])},
            "prediction_manifest": member(pins["prediction_manifest"]),
        },
    )
    pins["result"] = store(
        "result.json",
        {
            "schema_version": "author-spatial-result.v1",
            "status": "produced_awaiting_independent_verification",
            "source_commit": "qualified-source",
            "source_guards_passed": True,
            "scientific_sources_checked": 42,
            "protocol_sha256": pins["protocol"]["sha256"],
            "products": {
                name: member(pins[name])
                for name in (
                    "inputs",
                    "nominal",
                    "candidates",
                    "choices",
                    "outer_scores",
                )
            },
            "prediction_manifest": member(pins["prediction_manifest"]),
            "selection_manifest": member(pins["selection_manifest"]),
        },
    )
    pins["verification"] = store(
        "verification.json",
        {
            "schema_version": "author-spatial-independent-readback.v1",
            "status": "verified",
            "source_commit": "qualified-source",
            "source_guards_passed": True,
            "sources": {"passed": True, "source_objects": 42},
            "numerical_predictions": {"status": "passed"},
            "selection_and_scoring": {"status": "passed"},
        },
    )
    protocol = {
        "schema_version": "author-lra-geographic-thinning.v1",
        "upstream_source_commit": "qualified-source",
        "qualified_sources": pins,
        "cohort": {
            "size": 10,
            "expected_distinct_pairs": 17,
            "expected_selection_order": select_cohort(geometries)["selection_order"],
        },
        "models": {
            "transport": "gpm neutral",
            "baselines": list(original.BASELINES),
            "hellinger_scales_km": [20.0, 100.0],
        },
    }
    return repository, archive, protocol, upstream, native


@pytest.fixture(scope="module")
def qualified(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    return _fixture(tmp_path_factory.mktemp("thinning-source"))


def test_source_projection_has_fresh_complete_roles_and_no_outcome_decode(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
) -> None:
    repository, archive, protocol, _, _ = qualified
    packet = inputs.load_inputs(repository, archive, protocol)
    assert len(packet["contexts"]) == len(packet["observation_refs"]) == 10
    assert len(packet["pair_catalogue"]) == 17
    assert len(packet["retained_reference_predictions"]) == 40
    assert len(packet["sources"]) == 52
    assert "upstream_packet" not in packet
    assert (
        packet["summary"]["outcomes_decoded"]
        == packet["summary"]["new_forward_calls"]
        == 0
    )
    for context in packet["contexts"]:
        training = set(context["fold"]["train_record_ids"])
        forbidden = set(context["scientific_refs"]["forbidden_record_ids"])
        assert len(training) == 9 and len(forbidden) == 6
        assert not training & forbidden
        assert forbidden == {context["target"], *packet["cohort"]["excluded"]}
        assert {row["record_id"] for row in context["predictors"]} == training - {
            context["anchor"]
        }
        assert context["forward"]["regional_identity_source_record_ids"] == sorted(
            training
        )
        assert len(context["forward"]["distances_km"]) == 8
        assert (
            context["forward"]["regional_identity_policy"]
            == "conservative_all_training_fit_receipts"
        )
        assert "reference_baselines" not in context
        assert all(
            set(row["scientific_parent_ids"]) <= training
            for row in context["predictors"]
        )
        assert set(context["scientific_refs"]) == {
            "training_record_ids",
            "forbidden_record_ids",
            "selected_fit_ids",
            "regional_owner_id",
            "support_id",
            "target_geometry_id",
        }
    assert all(
        row["source_channel"].startswith("full_fifteen_")
        for row in packet["retained_reference_predictions"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_pair",
        "wrong_anchor",
        "ring",
        "attempt",
        "cover",
        "regional",
        "duplicate_pair",
    ],
)
def test_native_selected_fit_and_pair_corruption_is_not_repaired(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
    mutation: str,
) -> None:
    _, archive, protocol, source_packet, source_native = qualified
    parent = original.decode(
        (qualified[0] / protocol["qualified_sources"]["protocol"]["path"]).read_bytes()
    )
    packet, native = deepcopy(source_packet), deepcopy(source_native)
    request = next(iter(native["numerical_requests"]))
    row = native["numerical_requests"][request]
    if mutation == "missing_pair":
        del native["numerical_requests"][request]
    elif mutation == "wrong_anchor":
        for link in native["logical_requests"]:
            if link["request_sha256"] == request:
                link["regional_anchor_record_id"] = link["local_record_id"]
        parent["logical_ancestry_sha256"] = original.digest(native["logical_requests"])
    elif mutation == "ring":
        row["selections"][1]["ring_index"] = 0
    elif mutation == "attempt":
        row["selections"][1]["selected_attempt_sha256"] = "a" * 64
    elif mutation == "cover":
        row["selections"][1]["composition"][packet["taxa"][1]] = 0.75
    elif mutation == "regional":
        row["regional_cover"][0] = -1.0
    else:
        packet["contexts"][0]["predictors"][1] = deepcopy(
            packet["contexts"][0]["predictors"][0]
        )
    with pytest.raises((ValueError, KeyError)):
        inputs._pairs(packet, native, parent)


@pytest.mark.parametrize(
    "surface", ["inputs", "nominal", "verification", "choices", "outer_scores"]
)
def test_changed_qualified_source_bytes_refuse(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    surface: str,
) -> None:
    repository, archive, protocol, _, _ = qualified
    path = repository / protocol["qualified_sources"][surface]["path"]
    read = original._Reader.read
    if surface in {"choices", "outer_scores"}:
        from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import products

        actual = products.file_sha
        monkeypatch.setattr(
            products,
            "file_sha",
            lambda candidate: "0" * 64 if candidate == path else actual(candidate),
        )
    else:

        def changed(self: Any, pin: dict[str, Any], *, archived: bool = True) -> bytes:
            value = read(self, pin, archived=archived)
            if pin["path"] == protocol["qualified_sources"][surface]["path"]:
                # Simulate an authenticated but semantically changed source document.
                decoded = original.decode(value)
                if surface == "inputs":
                    decoded["schema_version"] = "unknown"
                elif surface == "nominal":
                    decoded["passed"] = False
                else:
                    decoded["status"] = "unverified"
                return original.canonical(decoded)
            return value

        monkeypatch.setattr(original._Reader, "read", changed)
    with pytest.raises(ValueError):
        inputs.load_inputs(repository, archive, protocol)


def test_requested_cohort_order_cannot_be_changed_to_match_cached_pairs(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
) -> None:
    repository, archive, protocol, _, _ = qualified
    changed = deepcopy(protocol)
    changed["cohort"]["expected_selection_order"].reverse()
    with pytest.raises(ValueError, match="geographic selection"):
        inputs.load_inputs(repository, archive, changed)


@pytest.mark.parametrize(
    "mutation",
    [
        "physical_alias",
        "parameter",
        "age_support",
        "duplicate_observation",
        "quantitative_parent",
    ],
)
def test_source_metadata_and_exact_family_admission_remain_consequential(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repository, archive, protocol, _, _ = qualified
    read = original._Reader.read

    def controlled(self: Any, pin: dict[str, Any], *, archived: bool = True) -> bytes:
        raw = read(self, pin, archived=archived)
        if pin["path"] == "experiment.json" and mutation in {
            "physical_alias",
            "parameter",
        }:
            value = original.decode(raw)
            if mutation == "physical_alias":
                value["sites"][1]["identity_keys"] = [value["sites"][0]["site_id"]]
            else:
                value["request_template"]["parameters"][0]["ppe"] = 2.25
            return original.canonical(value)
        if pin["path"].endswith("-geometry.json") and mutation == "age_support":
            value = original.decode(raw)
            value["sample_metadata"]["age_support_bp"] = [[1000, 1750]]
            return original.canonical(value)
        if pin["path"] == protocol["qualified_sources"]["inputs"][
            "path"
        ] and mutation in {"duplicate_observation", "quantitative_parent"}:
            value = original.decode(raw)
            if mutation == "duplicate_observation":
                value["observation_refs"].append(deepcopy(value["observation_refs"][0]))
            else:
                context = value["contexts"][0]
                context["predictors"][0]["scientific_parent_ids"].append(
                    context["target"]
                )
            return original.canonical(value)
        return raw

    monkeypatch.setattr(original._Reader, "read", controlled)
    with pytest.raises(ValueError):
        inputs.load_inputs(repository, archive, protocol)


def test_nominal_proof_is_reused_without_a_forward_or_outcome_call(
    qualified: tuple[Path, Path, dict[str, Any], dict[str, Any], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_lra.reconstruction import forward

    repository, archive, protocol, _, _ = qualified

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Input projection must not replay a forward model")

    monkeypatch.setattr(forward, "forward_deposition", forbidden)
    packet = inputs.load_inputs(repository, archive, protocol)
    assert packet["summary"]["upstream_nominal_slots_reused"] == 675
    assert packet["summary"]["outcomes_decoded"] == 0
