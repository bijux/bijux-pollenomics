"""Independent small-source custody fixtures; no scientific producer imports."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.source_audit import (
    _same,
    _same_radius,
    bind_sources,
)

_BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
_METHODS = ("gpm neutral", "gpm unstable", "lsm unstable", "lsm unstable low", "1overd")


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode()


def _hash(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _fixture(root: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    repository, archive = root / "repository", root / "archive"
    repository.mkdir(parents=True)
    archive.mkdir()
    taxa = [f"taxon:{index}" for index in range(30)]
    owners = [f"record:{index:02}" for index in range(15)]
    groups = {owner: "site-group:" + _hash([owner]) for owner in owners}
    source_pins: list[dict[str, Any]] = []

    def store(name: str, value: Any) -> dict[str, Any]:
        raw = _bytes(value)
        sha = hashlib.sha256(raw).hexdigest()
        path = archive / "objects" / sha[:2] / sha
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"path": name, "bytes": len(raw), "sha256": sha}

    sites, geometries, geometry_pins, observations = [], {}, {}, []
    for index, owner in enumerate(owners):
        name = f"owner-{index:02}"
        metadata = {
            "site_id": name,
            "bin_id": "author-TW5",
            "age_type": "calendar_bp",
            "age_support_bp": [[1250, 1750]],
        }
        geometry = {
            "latitude": 50.0 + index / 10,
            "longitude": index / 10,
            "sample_metadata": metadata,
            "inversion_rings": [[0, 500], [500, 1000]],
            "forward_rings": [[0, 500], [500, 1000], [1000, 10000]],
        }
        geometry_pin = store(name + "-geometry.json", geometry)
        raw_pin = store(
            name + "-raw.json",
            {
                "data_kind": "source_observations",
                "taxa": taxa,
                "sample": {**metadata, "counts": [index + 1, *([0] * 29)]},
            },
        )
        geometry_pins[owner], geometries[owner] = geometry_pin, geometry
        source_pins.extend((geometry_pin, raw_pin))
        observations.append({**raw_pin, "record_id": owner})
        sites.append(
            {
                "record_id": owner,
                "site_id": name,
                "identity_keys": [],
                "geometry": {key: geometry_pin[key] for key in ("path", "sha256")},
                "raw": {key: raw_pin[key] for key in ("path", "sha256")},
            }
        )
    experiment: dict[str, Any] = {
        "sites": sites,
        "regional_priority": owners,
        "support_profile": "same-outer-radius-homogeneous-v1",
        "local_support_radius_m": 1000,
        "local_ring_count": 2,
        "request_template": {
            "taxa": taxa,
            "parameters": [{"taxon": taxon, "ppe": 2.0} for taxon in taxa],
            "temporal_matching": {"bin": "author-TW5"},
            "versions": {"parameters": "synthetic"},
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
    support = {
        "support_profile": experiment["support_profile"],
        "local_support_radius_m": 1000,
        "taxa": taxa,
        "temporal_matching": experiment["request_template"]["temporal_matching"],
        "versions": experiment["request_template"]["versions"],
    }
    numeric, logical, slots, contexts = {}, [], [], []
    composition = {taxon: float(index == 0) for index, taxon in enumerate(taxa)}
    regional = list(composition.values())
    for outer in owners:
        for target in owners:
            kind = "outer" if target == outer else "inner"
            train = sorted(set(owners) - {outer, target})
            fold = {
                "fold_id": groups[target],
                "train_record_ids": train,
                "test_record_ids": [target],
                "train_group_ids": sorted(groups[owner] for owner in train),
                "test_group_ids": [groups[target]],
            }
            anchor = next(owner for owner in owners if owner in train)
            locals_ = sorted(set(train) - {anchor})
            predictors, fit_refs = [], []
            for local in locals_:
                request = _hash({"local": local, "anchor": anchor})
                attempts = [
                    _hash({"request": request, "ring": ring}) for ring in (0, 1)
                ]
                fits = [
                    "nominal-fit:"
                    + _hash({"request": request, "selected_attempt": attempt})
                    for attempt in attempts
                ]
                numeric[request] = {
                    "item_id": local,
                    "request_sha256": request,
                    "taxa": taxa,
                    "regional_cover": regional,
                    "selections": [
                        {
                            "ring_index": ring,
                            "request_sha256": request,
                            "selected_attempt_sha256": attempts[ring],
                            "composition": composition,
                        }
                        for ring in (0, 1)
                    ],
                }
                logical.append(
                    {
                        "kind": kind,
                        "outer_target": outer,
                        "target": target,
                        "fold": fold,
                        "local_record_id": local,
                        "regional_anchor_record_id": anchor,
                        "request_sha256": request,
                    }
                )
                predictors.append(
                    {
                        "record_id": local,
                        "group_id": groups[local],
                        "covers_by_ring": [regional, regional],
                        "request_sha256": request,
                        "selected_attempt_sha256s": attempts,
                        "fit_refs": fits,
                        "scientific_parent_ids": [local, anchor],
                    }
                )
                fit_refs.append(fits[1])
            forward = {
                "outer_fold": fold,
                "regional_cover": regional,
                "regional_anchor_record_id": anchor,
                "regional_anchor_group_id": groups[anchor],
                "regional_value_source_record_ids": [anchor],
                "regional_identity_source_record_ids": train,
                "regional_identity_policy": "conservative_all_training_fit_receipts",
                "declared_target_inversion_rings": geometries[target][
                    "inversion_rings"
                ],
                "declared_target_forward_rings": geometries[target]["forward_rings"],
                "target_geometry_sha256": geometry_pins[target]["sha256"],
                "fixture_full_forward": [1.0, 2.0, 3.0],
                "forward_inputs": {"taxa": taxa, "ppe": [2.0] * 30},
                "support_profile": experiment["support_profile"],
                "local_support_radius_m": 1000.0,
            }
            references = [
                {
                    "baseline": baseline,
                    "vegetation_fraction": composition,
                    "pollen_fraction": composition,
                }
                for baseline in _BASELINES
            ]
            context = {
                "context_id": "author-spatial:"
                + _hash(
                    {
                        "kind": kind,
                        "outer_target": outer,
                        "target": target,
                        "fold": fold,
                    }
                ),
                "kind": kind,
                "outer_target": outer,
                "target": target,
                "fold": fold,
                "anchor": anchor,
                "predictors": predictors,
                "forward": forward,
                "reference_baselines": references,
                "coordinates": {
                    owner: {
                        field: geometries[owner][field]
                        for field in ("latitude", "longitude")
                    }
                    for owner in sorted(set(locals_) | {target})
                },
                "scientific_refs": {
                    "training_record_ids": train,
                    "selected_fit_ids": fit_refs,
                    "regional_owner_id": anchor,
                    "support_id": "experiment-support:" + _hash(support),
                    "target_geometry_id": "experiment-geometry:"
                    + geometry_pins[target]["sha256"],
                },
            }
            contexts.append(context)
            for method in _METHODS:
                for baseline in _BASELINES:
                    row = {
                        "kind": kind,
                        "outer_target": outer,
                        "target": target,
                        "method": method,
                        "baseline": baseline,
                        "status": "predicted",
                        "fold": fold,
                    }
                    if method == "gpm neutral":
                        row.update(
                            {
                                "geometry": forward,
                                "prediction": {
                                    "baseline": baseline,
                                    "fold_id": fold["fold_id"],
                                    "record_id": target,
                                    "bin_id": "author-TW5",
                                    "vegetation_fraction": composition,
                                    "pollen_fraction": composition,
                                },
                            }
                        )
                    slots.append(row)
    assert len(numeric) == 39 and len(logical) == 2715 and len(slots) == 3375
    training = {
        "schema_version": "author-love-transport-training.v1",
        "method": "gpm neutral",
        "candidate": "source-candidate",
        "protocol_sha256": "synthetic-protocol",
        "numerical_requests": numeric,
        "logical_requests": logical,
    }
    training_pin = store("saved/training.json", training)
    freeze_pin = store("saved/freeze.json", {"slots": slots})
    admission_pin = store(
        "saved/admission.json",
        {
            "approved": True,
            "scientific_saved_products_admitted": True,
            "candidate": "source-candidate",
            "method": "gpm neutral",
            "training_protocol_sha256": "synthetic-protocol",
            "training": training_pin,
        },
    )
    descriptor_pin = store(
        "saved/descriptor.json",
        {
            "schema_version": "author-love-transport-shards.v1",
            "shards": [
                {
                    "method": method,
                    "training": training_pin,
                    "saved_product_admission": admission_pin,
                }
                for method in _METHODS
            ],
        },
    )
    authority = {
        "source_candidate": "source-candidate",
        "independent_semantics": {
            "approved": True,
            "scientific_saved_products_admitted": True,
        },
    }
    authority_bytes = _bytes(authority)
    (repository / "authority.json").write_bytes(authority_bytes)
    authority_pin = {
        "path": "authority.json",
        "bytes": len(authority_bytes),
        "sha256": hashlib.sha256(authority_bytes).hexdigest(),
    }
    protocol = {
        "nominal_transport": "gpm neutral",
        "scales_km": [20.0, 100.0],
        "nominal_candidate": "source-candidate",
        "nominal_training_protocol_sha256": "synthetic-protocol",
        "logical_ancestry_sha256": _hash(logical),
        "authority": authority_pin,
        "author_inputs": source_pins,
        "sources": {
            "nominal_training": training_pin,
            "candidate_freeze": freeze_pin,
            "recovered_shards": descriptor_pin,
        },
    }
    accounting = [
        {**pin, "storage": "repository" if pin is authority_pin else "archive_object"}
        for pin in [
            authority_pin,
            descriptor_pin,
            admission_pin,
            *source_pins,
            training_pin,
            freeze_pin,
        ]
    ]
    packet = {
        "schema_version": "author-lra-spatial-inputs.v1",
        "taxa": taxa,
        "contexts": contexts,
        "groups": groups,
        "support": support,
        "observation_refs": sorted(observations, key=lambda row: row["path"]),
        "sources": accounting,
        "summary": {
            "contexts": 225,
            "outer_contexts": 15,
            "inner_contexts": 210,
            "numerical_requests": 39,
            "logical_ancestry_rows": 2715,
            "frozen_source_slots": 3375,
            "source_bytes": sum(pin["bytes"] for pin in accounting),
            "outcomes_decoded": 0,
        },
    }
    return repository, archive, protocol, packet


@pytest.fixture(scope="module")
def original(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    return _fixture(tmp_path_factory.mktemp("source-custody"))


def test_full_literal_binding_retains_zero_counts_and_all_contexts(
    original: tuple[Path, Path, dict[str, Any], dict[str, Any]],
) -> None:
    counts, facts = bind_sources(*original)
    assert len(counts) == 15
    assert facts["counted_mass"] == sum(range(1, 16))
    assert facts["source_objects"] == 42
    assert facts["contexts"] == 225 and facts["nominal_source_slots"] == 675
    assert all(
        len(row) == 30 and list(row.values())[1:] == [0] * 29 for row in counts.values()
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "cover",
        "attempt",
        "parent",
        "context_missing",
        "fold_target",
        "forward",
        "coordinates",
        "baseline",
        "observed_owner",
        "taxa",
        "source_inventory",
        "summary",
        "support",
    ],
)
def test_no_unchecked_packet_trust(
    original: tuple[Path, Path, dict[str, Any], dict[str, Any]], mutation: str
) -> None:
    repository, archive, protocol, original_packet = original
    packet = deepcopy(original_packet)
    context = packet["contexts"][0]
    if mutation == "cover":
        context["predictors"][0]["covers_by_ring"][1] = [0.0, 1.0] + [0.0] * 28
    elif mutation == "attempt":
        context["predictors"][0]["selected_attempt_sha256s"][1] = "f" * 64
    elif mutation == "parent":
        context["predictors"][0]["scientific_parent_ids"] = [context["target"]]
    elif mutation == "context_missing":
        packet["contexts"].pop()
    elif mutation == "fold_target":
        context["fold"]["train_record_ids"][0] = context["target"]
    elif mutation == "forward":
        context["forward"]["fixture_full_forward"][0] += 0.25
    elif mutation == "coordinates":
        context["coordinates"][context["target"]]["latitude"] += 1
    elif mutation == "baseline":
        context["reference_baselines"][0]["pollen_fraction"] = {
            taxon: float(index == 1) for index, taxon in enumerate(packet["taxa"])
        }
    elif mutation == "observed_owner":
        packet["observation_refs"][0]["record_id"] = "wrong-owner"
    elif mutation == "taxa":
        packet["taxa"] = list(reversed(packet["taxa"]))
    elif mutation == "source_inventory":
        packet["sources"].pop()
    elif mutation == "summary":
        packet["summary"]["outcomes_decoded"] = 15
    else:
        packet["support"]["local_support_radius_m"] = 1001
    with pytest.raises(ValueError):
        bind_sources(repository, archive, protocol, packet)


def test_source_byte_change_refuses_before_packet_join(tmp_path: Path) -> None:
    repository, archive, protocol, packet = _fixture(tmp_path)
    pin = protocol["sources"]["nominal_training"]
    path = archive / "objects" / pin["sha256"][:2] / pin["sha256"]
    value = bytearray(path.read_bytes())
    value[0] = ord("[")
    path.write_bytes(value)
    with pytest.raises(ValueError, match="source bytes differ"):
        bind_sources(repository, archive, protocol, packet)


def test_repository_authority_cannot_escape_root(
    original: tuple[Path, Path, dict[str, Any], dict[str, Any]],
) -> None:
    repository, archive, original_protocol, packet = original
    protocol = deepcopy(original_protocol)
    protocol["authority"]["path"] = "../authority.json"
    with pytest.raises(ValueError, match="authority path"):
        bind_sources(repository, archive, protocol, packet)


def test_radius_accepts_equal_typed_values_without_relaxing_literal_custody() -> None:
    _same_radius(1000.0, 1000)
    _same_radius(1000, 1000.0)
    with pytest.raises(ValueError, match="other source field"):
        _same(1000.0, 1000, "other source field")
    for first, second in ((1000.0000000000001, 1000), (1000, 1000.0000000000001)):
        with pytest.raises(ValueError, match="source forward support radius"):
            _same_radius(first, second)


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        "1000",
        None,
        float("nan"),
        float("inf"),
        float("-inf"),
        0,
        0.0,
        -1000,
        10**1000,
    ],
)
def test_equal_but_invalid_radius_values_are_refused(value: Any) -> None:
    with pytest.raises(ValueError, match="source forward support radius"):
        _same_radius(value, value)


def _replace_source(
    archive: Path,
    protocol: dict[str, Any],
    packet: dict[str, Any],
    old: dict[str, Any],
    value: Any,
) -> dict[str, Any]:
    raw = _bytes(value)
    sha = hashlib.sha256(raw).hexdigest()
    destination = archive / "objects" / sha[:2] / sha
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    new = {"path": old["path"], "bytes": len(raw), "sha256": sha}
    for index, pin in enumerate(protocol["author_inputs"]):
        if pin["path"] == old["path"]:
            protocol["author_inputs"][index] = new
    for row in packet["sources"]:
        if row["path"] == old["path"]:
            row.update(new)
    packet["summary"]["source_bytes"] = sum(row["bytes"] for row in packet["sources"])
    return new


@pytest.mark.parametrize(
    "mutation",
    [
        "boolean",
        "fractional",
        "negative",
        "empty_mass",
        "unsafe_integer",
        "taxa_order",
        "chronology",
        "extra_metadata",
    ],
)
def test_even_authenticated_outcomes_require_exact_counts_and_metadata(
    original: tuple[Path, Path, dict[str, Any], dict[str, Any]], mutation: str
) -> None:
    repository, archive, original_protocol, original_packet = original
    protocol, packet = deepcopy(original_protocol), deepcopy(original_packet)
    ref = packet["observation_refs"][0]
    pin = {key: ref[key] for key in ("path", "bytes", "sha256")}
    raw = json.loads(
        (archive / "objects" / pin["sha256"][:2] / pin["sha256"]).read_bytes()
    )
    if mutation in {"boolean", "fractional", "negative", "unsafe_integer"}:
        raw["sample"]["counts"][0] = {
            "boolean": True,
            "fractional": 0.5,
            "negative": -1,
            "unsafe_integer": 2**53 + 1,
        }[mutation]
    elif mutation == "empty_mass":
        raw["sample"]["counts"] = [0] * 30
    elif mutation == "taxa_order":
        raw["taxa"] = list(reversed(raw["taxa"]))
    elif mutation == "chronology":
        raw["sample"]["age_support_bp"] = [[1250, 1800]]
    else:
        raw["sample"]["invented"] = "not source geometry metadata"
    new = _replace_source(archive, protocol, packet, pin, raw)
    ref.update(new)
    experiment_pin = next(
        row for row in protocol["author_inputs"] if row["path"] == "experiment.json"
    )
    experiment = json.loads(
        (
            archive
            / "objects"
            / experiment_pin["sha256"][:2]
            / experiment_pin["sha256"]
        ).read_bytes()
    )
    site = next(
        row for row in experiment["sites"] if row["record_id"] == ref["record_id"]
    )
    site["raw"]["sha256"] = new["sha256"]
    _replace_source(archive, protocol, packet, experiment_pin, experiment)
    with pytest.raises(ValueError, match="observation|counted denominator"):
        bind_sources(repository, archive, protocol, packet)
