"""Authenticate complete saved populations without decoding held-out outcomes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import SiteRecord
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial import inputs


def saved_inputs(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    """Build a complete synthetic fifteen-site source archive, with no model calls."""
    repository, archive = root / "repository", root / "archive"
    repository.mkdir(parents=True)
    archive.mkdir()
    taxa = [f"taxon-{index}" for index in range(30)]
    sites = [f"author:site-{index:02}" for index in range(15)]
    source_pins: list[dict[str, Any]] = []

    def store(name: str, value: Any, *, raw: bool = False) -> dict[str, Any]:
        body = value if raw else inputs.canonical(value)
        sha = hashlib.sha256(body).hexdigest()
        destination = archive / "objects" / sha[:2] / sha
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        return {"path": name, "bytes": len(body), "sha256": sha}

    geometry_pins = {}
    geometries = {}
    site_rows: list[dict[str, Any]] = []
    rings = [
        {"inner_radius_m": 1, "outer_radius_m": 100},
        {"inner_radius_m": 100, "outer_radius_m": 1000},
        {"inner_radius_m": 1000, "outer_radius_m": 100000},
    ]
    for index, record in enumerate(sites):
        name = f"site-{index:02}"
        geometry = {
            "latitude": 50 + index / 10,
            "longitude": -5 + index / 10,
            "sample_metadata": {
                "site_id": name,
                "bin_id": "author-TW5",
                "age_type": "calendar_bp",
                "age_support_bp": [[1250, 1750]],
            },
            "inversion_rings": rings[:2],
            "forward_rings": rings,
        }
        geometries[record] = geometry
        geometry_pin = store(name + "-geometry.json", geometry)
        raw_pin = store(
            name + "-raw.json", ("unopened outcome " + record).encode(), raw=True
        )
        source_pins.extend((geometry_pin, raw_pin))
        geometry_pins[record] = geometry_pin
        site_rows.append(
            {
                "record_id": record,
                "site_id": name,
                "identity_keys": [],
                "raw": {key: raw_pin[key] for key in ("path", "sha256")},
                "geometry": {key: geometry_pin[key] for key in ("path", "sha256")},
            }
        )
    experiment = {
        "sites": site_rows,
        "regional_priority": sites,
        "support_profile": "same-outer-radius-homogeneous-v1",
        "local_support_radius_m": 1000,
        "local_ring_count": 2,
        "request_template": {
            "taxa": taxa,
            "parameters": [{"taxon": name, "ppe": 2.0} for name in taxa],
            "temporal_matching": {"bins": ["author-TW5"]},
            "versions": {"parameters": "declared-fixture"},
        },
    }
    source_pins.append(store("experiment.json", experiment))
    for name in (
        "chronology",
        "decision",
        "dependency-lock",
        "parameters",
        "source-report",
        "taxa",
    ):
        source_pins.append(store(name + ".json", {"fixture_owner": name}))
    records = [SiteRecord(row["record_id"], row["site_id"], ()) for row in site_rows]
    outer_folds = grouped_leave_one_out(records)
    groups = {
        record: fold.test_group_ids[0]
        for fold in outer_folds
        for record in fold.test_record_ids
    }
    regional = [1 / 30] * 30
    numeric = {}
    logical = []
    slots = []
    for outer in outer_folds:
        outer_target = outer.test_record_ids[0]
        inner = grouped_leave_one_out(
            [record for record in records if record.record_id in outer.train_record_ids]
        )
        for kind, fold in [("outer", outer), *(("inner", fold) for fold in inner)]:
            target = fold.test_record_ids[0]
            anchor = next(owner for owner in sites if owner in fold.train_record_ids)
            predictors = set(fold.train_record_ids) - {anchor}
            for local in sorted(predictors):
                request = inputs.digest({"local": local, "anchor": anchor})
                if request not in numeric:
                    numeric[request] = {
                        "item_id": local,
                        "request_sha256": request,
                        "taxa": taxa,
                        "regional_cover": regional,
                        "selections": [
                            {
                                "ring_index": ring,
                                "request_sha256": request,
                                "selected_attempt_sha256": inputs.digest(
                                    {"request": request, "ring": ring}
                                ),
                                "composition": {
                                    name: float(index == ring)
                                    for index, name in enumerate(taxa)
                                },
                            }
                            for ring in range(2)
                        ],
                    }
                logical.append(
                    {
                        "kind": kind,
                        "outer_target": outer_target,
                        "target": target,
                        "fold": fold.as_dict(),
                        "local_record_id": local,
                        "regional_anchor_record_id": anchor,
                        "request_sha256": request,
                    }
                )
            full_k = [[0.01] * 30, [0.02] * 30, [0.03] * 30]
            forward = {
                "preparation_profile": "fixture",
                "forward_method_profile": "gpm neutral",
                "geometry_profile": "fixture",
                "deposition_units": "fixture",
                "full_k": full_k,
                "full_terrestrial_fraction": [0.5, 0.25, 0.25],
                "ring_bounds_m": [[1, 100], [100, 1000], [1000, 100000]],
                "regional_cutoff_m": 100000,
                "regional_cover": regional,
                "forward_inputs": {
                    "taxa": taxa,
                    "regional_deposition": [0.01] * 30,
                    "local_k": full_k[:2],
                    "terrestrial_fraction": [0.5, 0.25],
                    "ppe": [2.0] * 30,
                    "regional_input_ids": ["fixture-regional"],
                    "parameter_input_ids": ["fixture-parameters"],
                    "geometry_input_ids": ["fixture-geometry"],
                    "temporal_support_id": "fixture-time",
                    "method_profile": "fixture-gpm-neutral",
                    "engine_build_id": "fixture",
                },
                "distances_km": {
                    groups[local]: float(1 + sites.index(local))
                    for local in sorted(predictors)
                },
                "target_geometry_sha256": geometry_pins[target]["sha256"],
                "regional_anchor_record_id": anchor,
                "regional_value_source_record_ids": [anchor],
                "regional_identity_source_record_ids": list(fold.train_record_ids),
                "regional_identity_policy": "conservative_all_training_fit_receipts",
                "regional_anchor_group_id": groups[anchor],
                "predictor_group_ids": [groups[local] for local in sorted(predictors)],
                "outer_fold": fold.as_dict(),
                "support_profile": experiment["support_profile"],
                "local_support_radius_m": 1000,
                "declared_target_inversion_rings": geometries[target][
                    "inversion_rings"
                ],
                "declared_target_forward_rings": geometries[target]["forward_rings"],
            }
            for method in inputs.METHODS:
                for baseline in inputs.BASELINES:
                    references = (
                        {
                            "geometry": forward,
                            "prediction": {
                                "fold_id": fold.fold_id,
                                "record_id": target,
                                "bin_id": "author-TW5",
                                "baseline": baseline,
                                "vegetation_fraction": {
                                    name: float(index == 0)
                                    for index, name in enumerate(taxa)
                                },
                                "pollen_fraction": {
                                    name: float(index == 1)
                                    for index, name in enumerate(taxa)
                                },
                            },
                        }
                        if method == inputs.METHOD
                        else {}
                    )
                    slots.append(
                        {
                            "kind": kind,
                            "outer_target": outer_target,
                            "target": target,
                            "method": method,
                            "fold": fold.as_dict(),
                            "baseline": baseline,
                            "status": "predicted",
                            **references,
                        }
                    )
    training = {
        "schema_version": "author-love-transport-training.v1",
        "method": inputs.METHOD,
        "candidate": "fixture-candidate",
        "protocol_sha256": "fixture-original-protocol",
        "numerical_requests": numeric,
        "logical_requests": logical,
    }
    training_pin = store("saved/training.json", training)
    admission = {
        "approved": True,
        "scientific_saved_products_admitted": True,
        "candidate": training["candidate"],
        "method": inputs.METHOD,
        "training_protocol_sha256": training["protocol_sha256"],
        "training": training_pin,
    }
    admission_pin = store("saved/admission.json", admission)
    descriptor = {
        "schema_version": "author-love-transport-shards.v1",
        "shards": [
            {
                "method": method,
                "training": training_pin,
                "saved_product_admission": admission_pin,
            }
            for method in inputs.METHODS
        ],
    }
    authority = {
        "source_candidate": training["candidate"],
        "independent_semantics": {
            "approved": True,
            "scientific_saved_products_admitted": True,
        },
    }
    authority_raw = inputs.canonical(authority)
    (repository / "authority.json").write_bytes(authority_raw)
    protocol = {
        "nominal_transport": inputs.METHOD,
        "scales_km": [20.0, 100.0],
        "nominal_candidate": training["candidate"],
        "nominal_training_protocol_sha256": training["protocol_sha256"],
        "logical_ancestry_sha256": inputs.digest(logical),
        "author_inputs": source_pins,
        "authority": {
            "path": "authority.json",
            "bytes": len(authority_raw),
            "sha256": hashlib.sha256(authority_raw).hexdigest(),
        },
        "sources": {
            "nominal_training": training_pin,
            "candidate_freeze": store("saved/freeze.json", {"slots": slots}),
            "recovered_shards": store("saved/recovered.json", descriptor),
        },
    }
    return repository, archive, protocol


@pytest.fixture(scope="module")
def sources(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any]]:
    return saved_inputs(tmp_path_factory.mktemp("spatial-source"))


def read_object(archive: Path, pin: dict[str, Any]) -> Any:
    return inputs.decode(
        (archive / "objects" / pin["sha256"][:2] / pin["sha256"]).read_bytes()
    )


def joined_sources(
    sources: tuple[Path, Path, dict[str, Any]],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    """Load the reusable fixture; semantic counterexamples stay in memory."""
    _, archive, original = sources
    protocol = deepcopy(original)
    catalogue = {row["path"]: row for row in protocol["author_inputs"]}
    experiment = read_object(archive, catalogue["experiment.json"])
    geometry_pins = {
        row["record_id"]: catalogue[row["geometry"]["path"]]
        for row in experiment["sites"]
    }
    geometries = {
        record: read_object(archive, pin) for record, pin in geometry_pins.items()
    }
    return (
        read_object(archive, protocol["sources"]["nominal_training"]),
        read_object(archive, protocol["sources"]["candidate_freeze"]),
        experiment,
        geometries,
        geometry_pins,
        protocol,
    )


def test_complete_contexts_exclude_targets_and_preserve_zero_taxa(
    sources: tuple[Path, Path, dict[str, Any]],
) -> None:
    packet = inputs.load_inputs(*sources)
    assert Counter(row["kind"] for row in packet["contexts"]) == {
        "outer": 15,
        "inner": 210,
    }
    assert len(packet["taxa"]) == 30
    assert packet["summary"]["outcomes_decoded"] == 0
    assert len(packet["observation_refs"]) == 15
    assert len(packet["sources"]) == 42
    assert all("record_id" in row for row in packet["observation_refs"])
    for context in packet["contexts"]:
        assert context["target"] not in context["fold"]["train_record_ids"]
        assert context["outer_target"] not in context["fold"]["train_record_ids"]
        assert len(context["predictors"]) == (13 if context["kind"] == "outer" else 12)
        assert context["anchor"] not in {
            row["record_id"] for row in context["predictors"]
        }
        assert set(context["scientific_refs"]["training_record_ids"]) == set(
            context["fold"]["train_record_ids"]
        )
        assert [row["baseline"] for row in context["reference_baselines"]] == list(
            inputs.BASELINES
        )
        assert all(
            set(row["vegetation_fraction"]) == set(packet["taxa"])
            and set(row["pollen_fraction"]) == set(packet["taxa"])
            for row in context["reference_baselines"]
        )
        for predictor in context["predictors"]:
            assert predictor["covers_by_ring"] == [
                [1.0, *([0.0] * 29)],
                [0.0, 1.0, *([0.0] * 28)],
            ]
            assert set(predictor["scientific_parent_ids"]) <= set(
                context["fold"]["train_record_ids"]
            )


@pytest.mark.parametrize(
    "mutation",
    [
        "slot_missing",
        "slot_duplicate",
        "slot_foreign",
        "baseline_geometry",
        "target_geometry",
        "target_ancestry",
        "distances",
        "ppe",
        "ring_factor",
        "boolean_kernel",
        "reference_owner",
        "reference_axis",
        "reference_nonclosed",
    ],
)
def test_saved_slot_identity_and_factors_refuse(
    sources: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    arguments = joined_sources(sources)
    frozen = arguments[1]
    row = frozen["slots"][0]
    if mutation == "slot_missing":
        frozen["slots"].pop()
    elif mutation == "slot_duplicate":
        frozen["slots"][-1] = deepcopy(row)
    elif mutation == "slot_foreign":
        row["target"] = "foreign-owner"
    elif mutation == "baseline_geometry":
        row["geometry"]["distances_km"][
            next(iter(row["geometry"]["distances_km"]))
        ] += 1
    elif mutation == "reference_owner":
        row["prediction"]["record_id"] = "foreign-owner"
    elif mutation == "reference_axis":
        row["prediction"]["pollen_fraction"].popitem()
    elif mutation == "reference_nonclosed":
        row["prediction"]["vegetation_fraction"][
            next(iter(row["prediction"]["vegetation_fraction"]))
        ] = 0.5
    else:
        # Repair all three baseline copies: refusal must use source binding,
        # rather than merely detecting inconsistent baseline duplicates.
        for item in frozen["slots"][:3]:
            geometry = item["geometry"]
            if mutation == "target_geometry":
                geometry["target_geometry_sha256"] = "f" * 64
            elif mutation == "target_ancestry":
                geometry["regional_value_source_record_ids"] = [row["target"]]
            elif mutation == "distances":
                geometry["distances_km"]["foreign-group"] = 1.0
            elif mutation == "ppe":
                geometry["forward_inputs"]["ppe"][0] = 3.0
            elif mutation == "ring_factor":
                geometry["forward_inputs"]["local_k"][0][0] += 1
            elif mutation == "boolean_kernel":
                geometry["forward_inputs"]["local_k"][0][0] = True
    with pytest.raises(ValueError):
        inputs._join(*arguments)


@pytest.mark.parametrize(
    "mutation",
    [
        "logical_missing",
        "duplicate_local",
        "heldout_fit",
        "foreign_anchor",
        "missing_numeric",
        "bad_ring",
        "nonfinite_cover",
        "lost_taxon",
    ],
)
def test_native_ancestry_and_composition_controls(
    sources: tuple[Path, Path, dict[str, Any]], mutation: str
) -> None:
    arguments = joined_sources(sources)
    training, protocol = arguments[0], arguments[-1]
    row = training["logical_requests"][0]
    numeric = training["numerical_requests"][row["request_sha256"]]
    if mutation == "logical_missing":
        training["logical_requests"].pop()
    elif mutation == "duplicate_local":
        training["logical_requests"][1] = deepcopy(row)
    elif mutation == "heldout_fit":
        row["local_record_id"] = row["target"]
    elif mutation == "foreign_anchor":
        row["regional_anchor_record_id"] = row["outer_target"]
    elif mutation == "missing_numeric":
        del training["numerical_requests"][row["request_sha256"]]
    elif mutation == "bad_ring":
        numeric["selections"][1]["ring_index"] = 0
    elif mutation == "nonfinite_cover":
        numeric["selections"][0]["composition"][
            next(iter(numeric["selections"][0]["composition"]))
        ] = True
    elif mutation == "lost_taxon":
        numeric["selections"][0]["composition"].popitem()
    # Rebind the declared logical digest, so counterexamples reach the semantic
    # ancestry admission rather than merely failing the raw-byte custody gate.
    protocol["logical_ancestry_sha256"] = inputs.digest(training["logical_requests"])
    with pytest.raises(ValueError):
        inputs._join(*arguments)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'])
def test_strict_json(raw: bytes) -> None:
    with pytest.raises(ValueError):
        inputs.decode(raw)


def test_hash_and_source_namespace_controls(
    sources: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, archive, original = sources
    protocol = deepcopy(original)
    protocol["author_inputs"][0]["bytes"] += 1
    with pytest.raises(ValueError, match="missing|identity"):
        inputs.load_inputs(repository, archive, protocol)
    protocol = deepcopy(original)
    protocol["author_inputs"][-1] = deepcopy(protocol["author_inputs"][0])
    with pytest.raises(ValueError, match="Unique basename"):
        inputs.load_inputs(repository, archive, protocol)


def test_fixed_profile_and_scale_controls(
    sources: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, archive, original = sources
    for field, value in (
        ("nominal_transport", "outer-selected"),
        ("scales_km", [20, 100]),
        ("scales_km", [20.0, 200.0]),
    ):
        protocol = {**original, field: value}
        with pytest.raises(ValueError, match="fixed transport"):
            inputs.load_inputs(repository, archive, protocol)


def test_byte_identity_refuses_same_length_tamper(tmp_path: Path) -> None:
    body = b'{"owned":1}'
    sha = hashlib.sha256(body).hexdigest()
    target = tmp_path / "objects" / sha[:2] / sha
    target.parent.mkdir(parents=True)
    target.write_bytes(b'{"owned":2}')
    pin = {"path": "received.json", "bytes": len(body), "sha256": sha}
    with pytest.raises(ValueError, match="byte identity"):
        inputs._Reader(tmp_path, tmp_path).read(pin)


def test_missing_and_redirected_archive_member_refuse(tmp_path: Path) -> None:
    body = b"{}"
    sha = hashlib.sha256(body).hexdigest()
    pin = {"path": "received.json", "bytes": len(body), "sha256": sha}
    with pytest.raises(ValueError, match="missing"):
        inputs._Reader(tmp_path, tmp_path).read(pin)
    source = tmp_path / "unowned.json"
    source.write_bytes(body)
    target = tmp_path / "objects" / sha[:2] / sha
    target.parent.mkdir(parents=True)
    target.symlink_to(source)
    with pytest.raises(ValueError, match="redirected"):
        inputs._Reader(tmp_path, tmp_path).read(pin)


def test_byte_and_repeat_read_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    body = b"{}"
    sha = hashlib.sha256(body).hexdigest()
    pin = {"path": "received.json", "bytes": len(body), "sha256": sha}
    target = tmp_path / "objects" / sha[:2] / sha
    target.parent.mkdir(parents=True)
    target.write_bytes(body)
    reader = inputs._Reader(tmp_path, tmp_path)
    assert reader.read(pin) == body
    with pytest.raises(ValueError, match="twice"):
        reader.read(pin)
    monkeypatch.setattr(inputs, "MAX_TOTAL_BYTES", 1)
    with pytest.raises(ValueError, match="byte ceiling"):
        inputs._Reader(tmp_path, tmp_path).read(pin)
