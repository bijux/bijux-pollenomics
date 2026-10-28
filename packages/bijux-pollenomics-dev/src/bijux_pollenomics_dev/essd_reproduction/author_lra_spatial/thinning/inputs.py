"""Project qualified pair fits into new, outcome-free thinning ancestry."""

from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import SiteRecord
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

from ..inputs import (
    BASELINES,
    METHOD,
    _composition,
    _forward,
    _Reader,
    _vector,
    canonical,
    decode,
    digest,
    require,
)
from ..products import check_sources
from .cohort import select_cohort

_QUALIFIED_NAMES = {
    "result",
    "inputs",
    "nominal",
    "prediction_manifest",
    "candidates",
    "outer_scores",
    "choices",
    "selection_manifest",
    "protocol",
    "verification",
}
_STATIC_FORWARD = (
    "preparation_profile",
    "forward_method_profile",
    "geometry_profile",
    "deposition_units",
    "full_k",
    "full_terrestrial_fraction",
    "ring_bounds_m",
    "regional_cutoff_m",
    "target_geometry_sha256",
    "support_profile",
    "local_support_radius_m",
    "declared_target_inversion_rings",
    "declared_target_forward_rings",
)
_EXOGENOUS_FORWARD = (
    "parameter_input_ids",
    "geometry_input_ids",
    "temporal_support_id",
    "method_profile",
    "engine_build_id",
)


def _equal(left: Any, right: Any, message: str) -> None:
    require(canonical(left) == canonical(right), message)


def _member(
    parent: dict[str, Any], member: dict[str, Any], pin: dict[str, Any]
) -> None:
    name = member["path"]
    require(
        type(name) is str and Path(name).name == name,
        "Qualified direct member required",
    )
    _equal(
        {**member, "path": str(Path(parent["path"]).parent / name)},
        pin,
        "Qualified result member binding differs",
    )


def _inventory(
    parent: dict[str, Any], descriptor: dict[str, Any], upstream: dict[str, Any]
) -> None:
    nominal = [row for row in descriptor["shards"] if row["method"] == METHOD]
    require(len(nominal) == 1, "Unique nominal source descriptor required")
    expected = [
        {**pin, "storage": "archive_object"}
        for pin in [
            *parent["author_inputs"],
            *parent["sources"].values(),
            nominal[0]["saved_product_admission"],
        ]
    ] + [{**parent["authority"], "storage": "repository"}]
    require(
        len(expected) == len(upstream["sources"]) == 42,
        "Original42 source identities required",
    )
    _equal(
        sorted(expected, key=canonical),
        sorted(upstream["sources"], key=canonical),
        "Original source readset differs from qualified primary pins",
    )


def _qualification(
    repository: Path, archive: Path, protocol: dict[str, Any], reader: _Reader
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    pins = protocol["qualified_sources"]
    require(set(pins) == _QUALIFIED_NAMES, "Exact qualified source roles required")
    # Choices and outer losses are authenticated bytes only until the new freeze.
    documents = {
        name: decode(reader.read(pin, archived=False))
        for name, pin in pins.items()
        if name not in {"choices", "outer_scores"}
    }
    parent, upstream = documents["protocol"], documents["inputs"]
    result, verified = documents["result"], documents["verification"]
    require(
        result["schema_version"] == "author-spatial-result.v1"
        and result["status"] == "produced_awaiting_independent_verification"
        and verified["schema_version"] == "author-spatial-independent-readback.v1"
        and verified["status"] == "verified"
        and result["source_commit"]
        == verified["source_commit"]
        == protocol["upstream_source_commit"]
        and result["source_guards_passed"] is True
        and verified["source_guards_passed"] is True
        and verified["sources"]["passed"] is True
        and verified["sources"]["source_objects"]
        == result["scientific_sources_checked"]
        == 42
        and verified["numerical_predictions"]["status"] == "passed"
        and verified["selection_and_scoring"]["status"] == "passed"
        and result["protocol_sha256"] == pins["protocol"]["sha256"],
        "Qualified source execution and independent status required",
    )
    for name in ("inputs", "nominal", "candidates", "choices", "outer_scores"):
        _member(pins["result"], result["products"][name], pins[name])
    for name in ("prediction_manifest", "selection_manifest"):
        _member(pins["result"], result[name], pins[name])
    prediction = documents["prediction_manifest"]
    require(
        prediction["schema_version"] == "author-spatial-prediction-freeze.v1",
        "Original prediction freeze schema",
    )
    require(
        set(prediction["files"]) == {"inputs", "nominal", "candidates"},
        "Original closed prediction population",
    )
    for name, pin in prediction["files"].items():
        _member(pins["prediction_manifest"], pin, pins[name])
    selection = documents["selection_manifest"]
    require(
        selection["schema_version"] == "author-spatial-selection-freeze.v1",
        "Original selection freeze schema",
    )
    _member(pins["selection_manifest"], selection["files"]["choices"], pins["choices"])
    _member(
        pins["selection_manifest"],
        selection["prediction_manifest"],
        pins["prediction_manifest"],
    )
    nominal = documents["nominal"]
    require(
        nominal["passed"] is True
        and nominal["failures"] == []
        and nominal["contexts"] == 225
        and nominal["forward_calls"] == 675
        and nominal["reference_baselines"]
        == nominal["vegetation_comparisons"]
        == nominal["pollen_comparisons"]
        == 675
        and nominal["maximum_vegetation_absolute_error"]
        == nominal["maximum_pollen_absolute_error"]
        == 0.0
        and nominal["absolute_tolerance"] == 1e-12,
        "Unchanged qualified675-slot nominal correspondence required",
    )
    require(
        upstream["schema_version"] == "author-lra-spatial-inputs.v1"
        and parent["nominal_transport"] == METHOD
        and parent["scales_km"] == [20.0, 100.0],
        "Qualified point-source profile differs",
    )
    descriptor = decode(reader.read(parent["sources"]["recovered_shards"]))
    _inventory(parent, descriptor, upstream)
    combined = [
        *deepcopy(upstream["sources"]),
        *[{**pin, "storage": "repository"} for pin in pins.values()],
    ]
    require(
        len({(p["storage"], p["path"]) for p in combined}) == len(combined),
        "Unique source path roles required",
    )
    check_sources(repository, archive, {"sources": combined})
    return documents, parent, combined


def _pairs(
    upstream: dict[str, Any], native: dict[str, Any], parent: dict[str, Any]
) -> dict[tuple[str, str], dict[str, Any]]:
    taxa, groups = upstream["taxa"], upstream["groups"]
    require(
        native["schema_version"] == "author-love-transport-training.v1"
        and native["method"] == METHOD
        and native["candidate"] == parent["nominal_candidate"]
        and native["protocol_sha256"] == parent["nominal_training_protocol_sha256"]
        and len(native["numerical_requests"]) == 39
        and len(native["logical_requests"]) == 2715
        and digest(native["logical_requests"]) == parent["logical_ancestry_sha256"],
        "Original39 native source request identity differs",
    )
    result: dict[tuple[str, str], dict[str, Any]] = {}
    primary_pairs: dict[tuple[str, str], str] = {}
    request_owners: dict[str, tuple[str, str]] = {}
    for link in native["logical_requests"]:
        pair = (link["local_record_id"], link["regional_anchor_record_id"])
        request = link["request_sha256"]
        require(
            request in native["numerical_requests"]
            and pair[0] in groups
            and pair[1] in groups
            and pair[0] != pair[1]
            and (pair not in primary_pairs or primary_pairs[pair] == request)
            and (request not in request_owners or request_owners[request] == pair),
            "Original native local/anchor/request ownership conflicts",
        )
        primary_pairs[pair], request_owners[request] = request, pair
    require(
        len(primary_pairs) == len(request_owners) == 39,
        "Complete primary39 pair mapping required",
    )
    require(
        len(upstream["contexts"]) == 225,
        "Complete original225 metadata contexts required",
    )
    for context in upstream["contexts"]:
        anchor = context["anchor"]
        require(
            anchor in context["fold"]["train_record_ids"]
            and len(context["predictors"])
            == len({row["record_id"] for row in context["predictors"]})
            and {row["record_id"] for row in context["predictors"]}
            == set(context["fold"]["train_record_ids"]) - {anchor},
            "Complete unique original local-pair membership required",
        )
        for predictor in context["predictors"]:
            local, request = predictor["record_id"], predictor["request_sha256"]
            require(
                local != anchor and local in groups and anchor in groups,
                "Physical pair ownership differs",
            )
            require(
                primary_pairs.get((local, anchor)) == request,
                "Qualified packet/native pair source differs",
            )
            row = native["numerical_requests"][request]
            require(
                row["request_sha256"] == request
                and row["item_id"] == local
                and row["taxa"] == taxa,
                "Native pair owner or axis differs",
            )
            selected = row["selections"]
            require(
                type(selected) is list and len(selected) == 2,
                "Both selected source rings required",
            )
            covers, attempts, fits = [], [], []
            for ring, item in enumerate(selected):
                require(
                    type(item["ring_index"]) is int
                    and item["ring_index"] == ring
                    and item["request_sha256"] == request,
                    "Source selected ring/request differs",
                )
                attempt = item["selected_attempt_sha256"]
                require(
                    type(attempt) is str
                    and len(attempt) == 64
                    and all(c in "0123456789abcdef" for c in attempt),
                    "Selected native attempt identity required",
                )
                covers.append(_composition(item["composition"], taxa))
                attempts.append(attempt)
                fits.append(
                    "nominal-fit:"
                    + digest({"request": request, "selected_attempt": attempt})
                )
            expected = {
                "record_id": local,
                "group_id": groups[local],
                "covers_by_ring": covers,
                "request_sha256": request,
                "selected_attempt_sha256s": attempts,
                "fit_refs": fits,
                "scientific_parent_ids": [local, anchor],
            }
            _equal(
                predictor,
                expected,
                "Saved pair/selected rings differ from native source",
            )
            _vector(row["regional_cover"], len(taxa))
            _composition(dict(zip(taxa, row["regional_cover"], strict=True)), taxa)
            value = {"predictor": expected, "regional_cover": row["regional_cover"]}
            key = (local, anchor)
            if key in result:
                _equal(
                    result[key], value, "Repeated pair has conflicting source identity"
                )
            else:
                result[key] = value
    require(len(result) == 39, "Complete unique39 native pair inventory required")
    return result


def _regional(
    forward: dict[str, Any], cover: list[float], ppe: list[float]
) -> list[float]:
    return [
        ppe[taxon]
        * cover[taxon]
        * math.fsum(
            row[taxon] * fraction
            for row, fraction in zip(
                forward["full_k"][2:],
                forward["full_terrestrial_fraction"][2:],
                strict=True,
            )
        )
        for taxon in range(len(ppe))
    ]


def _close(left: list[float], right: list[float]) -> None:
    require(
        len(left) == len(right)
        and all(
            math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-10)
            for a, b in zip(left, right, strict=True)
        ),
        "Anchor-specific saved regional deposition differs",
    )


def _references(
    upstream: dict[str, Any], candidates: list[dict[str, Any]], selected: list[str]
) -> list[dict[str, Any]]:
    contexts = {row["context_id"]: row for row in upstream["contexts"]}
    require(
        len(contexts) == 225 and len(candidates) == 450,
        "Original complete reference population required",
    )
    indexed = {}
    for candidate in candidates:
        key = (candidate["context_id"], candidate["length_scale_km"])
        require(
            key not in indexed and key[0] in contexts and key[1] in {20.0, 100.0},
            "Unique original fixed-scale reference required",
        )
        source = contexts[key[0]]
        _equal(
            candidate["scientific_refs"],
            source["scientific_refs"],
            "Original reference scientific ancestry differs",
        )
        require(
            candidate["target"] == source["target"]
            and candidate["outer_target"] == source["outer_target"]
            and candidate["kind"] == source["kind"],
            "Original reference role differs",
        )
        require(
            candidate["status"] == "predicted",
            "Qualified original reference prediction unavailable",
        )
        for field in ("vegetation_fraction", "pollen_fraction"):
            _composition(
                dict(zip(upstream["taxa"], candidate[field], strict=True)),
                upstream["taxa"],
            )
        indexed[key] = candidate
    result = []
    for target in selected:
        outer = [
            row
            for row in contexts.values()
            if row["kind"] == "outer" and row["target"] == target
        ]
        require(len(outer) == 1, "Unique full-fifteen target reference required")
        context = outer[0]
        baselines = context["reference_baselines"]
        require(
            len(baselines) == 3
            and [row["baseline"] for row in baselines] == list(BASELINES),
            "Three original baseline references required",
        )
        for row in [*baselines, indexed[(context["context_id"], 20.0)]]:
            baseline = row.get("baseline")
            method = baseline if baseline is not None else "hellinger_20km"
            result.append(
                {
                    "target": target,
                    "method_id": method,
                    "status": "predicted",
                    "vegetation_fraction": _composition(
                        row["vegetation_fraction"], upstream["taxa"]
                    )
                    if baseline is not None
                    else list(row["vegetation_fraction"]),
                    "pollen_fraction": _composition(
                        row["pollen_fraction"], upstream["taxa"]
                    )
                    if baseline is not None
                    else list(row["pollen_fraction"]),
                    "source_channel": "full_fifteen_"
                    + (baseline if baseline is not None else "h20"),
                    "original_context_id": context["context_id"],
                    "scientific_refs": deepcopy(context["scientific_refs"]),
                }
            )
    require(len(result) == 40, "Complete matched40 retained references required")
    return result


def load_inputs(
    repository: Path, archive: Path, protocol: dict[str, Any]
) -> dict[str, Any]:
    """Construct ten fresh training roles without model or scoring-outcome calls."""
    require(
        protocol["schema_version"] == "author-lra-geographic-thinning.v1",
        "Thinning source protocol schema",
    )
    require(
        protocol["cohort"]["size"] == 10
        and protocol["cohort"]["expected_distinct_pairs"] == 17
        and protocol["models"]["transport"] == METHOD
        and protocol["models"]["baselines"] == list(BASELINES)
        and protocol["models"]["hellinger_scales_km"] == [20.0, 100.0],
        "Prospective fixed thinning profile differs",
    )
    reader = _Reader(repository, archive)
    documents, parent, sources = _qualification(repository, archive, protocol, reader)
    upstream = documents["inputs"]
    catalogue = {row["path"]: row for row in parent["author_inputs"]}
    require(len(catalogue) == 37, "Original37 author metadata inventory required")
    experiment = decode(reader.read(catalogue["experiment.json"]))
    sites = experiment["sites"]
    require(
        len(sites) == len({site["record_id"] for site in sites}) == 15,
        "Fifteen original physical identities required",
    )
    records = [
        SiteRecord(row["record_id"], row["site_id"], tuple(row["identity_keys"]))
        for row in sites
    ]
    full_folds = grouped_leave_one_out(records)
    require(
        len(full_folds) == 15
        and all(len(fold.test_record_ids) == 1 for fold in full_folds),
        "Full transitive identity families must precede thinning",
    )
    groups = {
        record: fold.test_group_ids[0]
        for fold in full_folds
        for record in fold.test_record_ids
    }
    _equal(groups, upstream["groups"], "Qualified physical group identities differ")
    geometries, geometry_refs = {}, {}
    for site in sites:
        pin = catalogue[site["geometry"]["path"]]
        _equal(
            site["geometry"],
            {key: pin[key] for key in ("path", "sha256")},
            "Primary geometry identity differs",
        )
        geometry = decode(reader.read(pin))
        metadata = geometry["sample_metadata"]
        require(
            metadata["site_id"] == site["site_id"]
            and metadata["bin_id"] == "author-TW5"
            and metadata["age_type"] == "calendar_bp"
            and metadata["age_support_bp"] == [[1250, 1750]],
            "Original target support differs",
        )
        geometries[site["record_id"]], geometry_refs[site["record_id"]] = geometry, pin
    cohort = select_cohort(geometries)
    _equal(
        cohort["selection_order"],
        protocol["cohort"]["expected_selection_order"],
        "Prespecified nominal geographic selection differs",
    )
    selected, excluded = cohort["selected"], cohort["excluded"]
    taxa = upstream["taxa"]
    require(len(taxa) == len(set(taxa)) == 30, "Original30 taxon axis required")
    _equal(taxa, experiment["request_template"]["taxa"], "Source taxon axis differs")
    _equal(
        upstream["support"],
        {
            "support_profile": experiment["support_profile"],
            "local_support_radius_m": experiment["local_support_radius_m"],
            "taxa": taxa,
            "temporal_matching": experiment["request_template"]["temporal_matching"],
            "versions": experiment["request_template"]["versions"],
        },
        "Qualified support differs from original experiment",
    )
    require(
        experiment["local_ring_count"] == 2
        and experiment["local_support_radius_m"] == 1000
        and experiment["support_profile"] == "same-outer-radius-homogeneous-v1",
        "Fixed original local support required",
    )
    parameters = experiment["request_template"]["parameters"]
    require(
        [row["taxon"] for row in parameters] == taxa, "Source parameter axis differs"
    )
    ppe = [row["ppe"] for row in parameters]
    _vector(ppe, 30, positive=True)
    native = decode(reader.read(parent["sources"]["nominal_training"]))
    pairs = _pairs(upstream, native, parent)
    priority = experiment["regional_priority"]
    require(
        len(priority) == len(set(priority)) == 15 and set(priority) == set(groups),
        "Original full regional priority required",
    )
    contexts, used = [], set()
    support_id = "experiment-support:" + digest(upstream["support"])
    for target in selected:
        training = sorted(set(selected) - {target})
        forbidden = sorted({target, *excluded})
        anchor = next(record for record in priority if record in training)
        locals_ = sorted(set(training) - {anchor})
        require(
            len(training) == 9 and len(forbidden) == 6 and len(locals_) == 8,
            "Complete nine-owner closure required",
        )
        fold = {
            "fold_id": groups[target],
            "train_record_ids": training,
            "test_record_ids": [target],
            "train_group_ids": sorted(groups[owner] for owner in training),
            "test_group_ids": [groups[target]],
        }
        predictors = []
        regional: list[float] | None = None
        for local in locals_:
            require(
                (local, anchor) in pairs,
                "Required thinned local-anchor pair is not qualified",
            )
            source = pairs[(local, anchor)]
            if regional is None:
                regional = source["regional_cover"]
            _equal(
                source["regional_cover"],
                regional,
                "Thinned common anchor source differs between fits",
            )
            predictors.append(deepcopy(source["predictor"]))
            used.add((local, anchor))
        if regional is None:
            raise ValueError("Selected regional source required")
        originals = [
            row
            for row in upstream["contexts"]
            if row["target"] == target and row["anchor"] == anchor
        ]
        require(bool(originals), "Anchor-specific qualified target geometry missing")
        original = min(originals, key=lambda row: row["context_id"])
        forward = {key: deepcopy(original["forward"][key]) for key in _STATIC_FORWARD}
        exogenous = {
            key: deepcopy(original["forward"]["forward_inputs"][key])
            for key in _EXOGENOUS_FORWARD
        }
        _equal(
            exogenous["geometry_input_ids"],
            ["experiment-geometry:" + geometry_refs[target]["sha256"]],
            "Source forward target geometry identifier differs",
        )
        _equal(
            exogenous["parameter_input_ids"],
            [
                "experiment-parameters:"
                + digest(
                    {
                        "parameters": parameters,
                        "evidence": experiment["request_template"]["evidence"],
                    }
                )
            ],
            "Source forward parameter identity differs",
        )
        require(
            exogenous["temporal_support_id"]
            == "experiment-time:"
            + digest(
                {
                    "metadata": geometries[target]["sample_metadata"],
                    "matching": experiment["request_template"]["temporal_matching"],
                }
            ),
            "Source forward temporal identity differs",
        )
        # This engine identity describes the saved kernels, not the binary used
        # by a future forecast execution.
        for row in upstream["contexts"]:
            if row["target"] != target:
                continue
            _equal(
                {key: row["forward"][key] for key in _STATIC_FORWARD},
                forward,
                "Exogenous target forward geometry differs across source roles",
            )
            _equal(
                {
                    key: row["forward"]["forward_inputs"][key]
                    for key in _EXOGENOUS_FORWARD
                },
                exogenous,
                "Exogenous forward identity differs across source roles",
            )
        for row in originals:
            _equal(
                {key: row["forward"][key] for key in _STATIC_FORWARD},
                forward,
                "Target-specific static forward geometry differs",
            )
            _equal(
                row["forward"]["regional_cover"],
                regional,
                "Native/target regional source handoff differs",
            )
            _equal(
                row["forward"]["forward_inputs"]["ppe"],
                ppe,
                "Original saved parameter PPE differs",
            )
        deposition = _regional(forward, regional, ppe)
        for row in originals:
            _close(deposition, row["forward"]["forward_inputs"]["regional_deposition"])
        distances = {
            groups[local]: cohort["distance_matrix_m"][target][local] / 1000.0
            for local in locals_
        }
        forward.update(
            {
                "outer_fold": fold,
                "regional_anchor_record_id": anchor,
                "regional_anchor_group_id": groups[anchor],
                "regional_value_source_record_ids": [anchor],
                "regional_identity_source_record_ids": training,
                "regional_identity_policy": "conservative_all_training_fit_receipts",
                "predictor_group_ids": sorted(distances),
                "distances_km": distances,
                "regional_cover": list(regional),
                "forward_inputs": {
                    **exogenous,
                    "regional_input_ids": [
                        "thinning-regional:"
                        + digest(
                            {
                                "regional_owner_id": anchor,
                                "regional_cover": regional,
                                "support_id": support_id,
                            }
                        )
                    ],
                    "taxa": taxa,
                    "ppe": ppe,
                    "regional_deposition": deposition,
                    "local_k": forward["full_k"][:2],
                    "terrestrial_fraction": forward["full_terrestrial_fraction"][:2],
                },
            }
        )
        _forward(
            forward,
            taxa=taxa,
            fold=fold,
            anchor=anchor,
            target=target,
            groups=groups,
            geometries=geometries,
            geometry_pins=geometry_refs,
            regional_cover=regional,
            experiment=experiment,
        )
        contexts.append(
            {
                "context_id": "author-thinning:"
                + digest({"fold": fold, "selected": selected, "forbidden": forbidden}),
                "kind": "outer",
                "outer_target": target,
                "target": target,
                "fold": fold,
                "anchor": anchor,
                "predictors": predictors,
                "coordinates": {
                    record: deepcopy(cohort["coordinates"][record])
                    for record in sorted({target, *locals_})
                },
                "forward": forward,
                "scientific_refs": {
                    "training_record_ids": training,
                    "forbidden_record_ids": forbidden,
                    "selected_fit_ids": [row["fit_refs"][1] for row in predictors],
                    "regional_owner_id": anchor,
                    "support_id": support_id,
                    "target_geometry_id": "experiment-geometry:"
                    + geometry_refs[target]["sha256"],
                },
            }
        )
    require(len(used) == 17, "Complete17 cached pair population required")
    observations = {row["record_id"]: row for row in upstream["observation_refs"]}
    require(
        len(upstream["observation_refs"]) == len(observations) == 15
        and set(observations) == set(groups),
        "Original physical observation reference inventory differs",
    )
    for site in sites:
        pin = catalogue[site["raw"]["path"]]
        _equal(
            observations[site["record_id"]],
            {**pin, "record_id": site["record_id"]},
            "Unopened scoring observation identity differs",
        )
        _equal(
            site["raw"],
            {key: pin[key] for key in ("path", "sha256")},
            "Original raw source identity differs",
        )
    packet = {
        "schema_version": "author-lra-thinning-inputs.v1",
        "taxa": taxa,
        "groups": groups,
        "cohort": cohort,
        "contexts": contexts,
        "observation_refs": [deepcopy(observations[target]) for target in selected],
        "geometries": geometries,
        "geometry_refs": geometry_refs,
        "pair_catalogue": [
            {
                "local_record_id": local,
                "regional_anchor_record_id": anchor,
                **{
                    key: deepcopy(pairs[(local, anchor)]["predictor"][key])
                    for key in (
                        "request_sha256",
                        "selected_attempt_sha256s",
                        "fit_refs",
                        "scientific_parent_ids",
                    )
                },
            }
            for local, anchor in sorted(used)
        ],
        "retained_reference_predictions": _references(
            upstream, documents["candidates"], selected
        ),
        "sources": sources,
        "support": deepcopy(upstream["support"]),
        "summary": {
            "contexts": 10,
            "training_owners_per_fold": 9,
            "local_predictors_per_fold": 8,
            "cached_pairs": 17,
            "retained_references": 40,
            "upstream_nominal_slots_reused": 675,
            "new_inverse_fits": 0,
            "new_kernel_calls": 0,
            "new_forward_calls": 0,
            "new_random_draws": 0,
            "outcomes_decoded": 0,
        },
    }
    check_sources(repository, archive, packet)
    return packet
