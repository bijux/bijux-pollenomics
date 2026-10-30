"""Join admitted saved fits and forward geometry without opening outcomes.

Archive identities account for complete received objects. Numerical ancestry is
instead attached to each context's allowed training owners and selected fits.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import SiteRecord
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out

METHOD = "gpm neutral"
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
METHODS = (METHOD, "gpm unstable", "lsm unstable", "lsm unstable low", "1overd")
MAX_OBJECT_BYTES = 140 * 1024**2
MAX_TOTAL_BYTES = 192 * 1024**2


def require(condition: object, message: str) -> None:
    """Raise a refusal when a declared spatial-input condition fails."""
    if not condition:
        raise ValueError(message)


def canonical(value: Any) -> bytes:
    """Use the original scientific metadata's canonical JSON representation."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(value: Any) -> str:
    """Hash the canonical encoding of a source-bound spatial value."""
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw: bytes) -> Any:
    """Decode scientific JSON without duplicate keys or nonfinite constants."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "Duplicate scientific JSON key")
            result[key] = value
        return result

    def nonfinite(value: str) -> Any:
        raise ValueError("Nonfinite scientific JSON literal: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _pin(pin: Any) -> None:
    require(
        type(pin) is dict
        and set(pin) == {"path", "bytes", "sha256"}
        and type(pin["path"]) is str
        and bool(pin["path"])
        and type(pin["bytes"]) is int
        and 0 < pin["bytes"] <= MAX_OBJECT_BYTES
        and type(pin["sha256"]) is str
        and re.fullmatch("[0-9a-f]{64}", pin["sha256"]) is not None,
        "Exact bounded scientific object pin required",
    )


def _same_identity(left: Any, right: Any) -> bool:
    _pin(left)
    _pin(right)
    return (left["bytes"], left["sha256"]) == (right["bytes"], right["sha256"])


class _Reader:
    def __init__(self, repository: Path, archive_root: Path) -> None:
        self.repository = repository.resolve(strict=True)
        self.archive = archive_root.resolve(strict=True)
        self.refs: list[dict[str, Any]] = []
        self.seen: set[str] = set()
        self.total = 0

    def read(self, pin: dict[str, Any], *, archived: bool = True) -> bytes:
        _pin(pin)
        sha = pin["sha256"]
        require(sha not in self.seen, "Scientific object read twice")
        path: Path
        if archived:
            path = self.archive / "objects" / sha[:2] / sha
        else:
            relative = Path(pin["path"])
            require(
                not relative.is_absolute() and ".." not in relative.parts,
                "Repository authority must have a relative path",
            )
            path = self.repository / relative
        require(
            path.is_file()
            and not any(parent.is_symlink() for parent in (path, *path.parents))
            and path.stat().st_size == pin["bytes"],
            "Original scientific object missing or physically redirected",
        )
        require(self.total + pin["bytes"] <= MAX_TOTAL_BYTES, "Source byte ceiling")
        raw = path.read_bytes()
        require(
            len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == sha,
            "Scientific source byte identity differs",
        )
        self.seen.add(sha)
        self.total += len(raw)
        self.refs.append(
            {**pin, "storage": "archive_object" if archived else "repository"}
        )
        return raw


def _number(value: Any, *, positive: bool = False) -> float:
    require(
        type(value) in (int, float)
        and math.isfinite(value)
        and (value > 0 if positive else value >= 0),
        "Finite strict saved numerical domain required",
    )
    return float(value)


def _vector(value: Any, length: int, *, positive: bool = False) -> None:
    require(
        type(value) is list and len(value) == length, "Saved numerical axis differs"
    )
    for item in value:
        _number(item, positive=positive)


def _composition(value: Any, taxa: list[str]) -> list[float]:
    require(
        type(value) is dict and set(value) == set(taxa),
        "Full composition axis required",
    )
    result = [_number(value[taxon]) for taxon in taxa]
    require(
        all(x <= 1 for x in result) and abs(sum(result) - 1) <= 1e-9,
        "Saved cover must be closed",
    )
    return result


def _forward(
    value: dict[str, Any],
    *,
    taxa: list[str],
    fold: dict[str, Any],
    anchor: str,
    target: str,
    groups: dict[str, str],
    geometries: dict[str, Any],
    geometry_pins: dict[str, Any],
    regional_cover: list[float],
    experiment: dict[str, Any],
) -> None:
    inputs = value["forward_inputs"]
    predictors = set(fold["train_record_ids"]) - {anchor}
    predictor_groups = {groups[record] for record in predictors}
    require(
        canonical(value["outer_fold"]) == canonical(fold)
        and value["regional_anchor_record_id"] == anchor
        and value["regional_anchor_group_id"] == groups[anchor]
        and value["regional_value_source_record_ids"] == [anchor]
        and value["regional_identity_source_record_ids"]
        == list(fold["train_record_ids"])
        and value["regional_identity_policy"]
        == "conservative_all_training_fit_receipts"
        and set(value["predictor_group_ids"]) == predictor_groups
        and len(value["predictor_group_ids"]) == len(predictors)
        and set(value["distances_km"]) == predictor_groups
        and value["target_geometry_sha256"] == geometry_pins[target]["sha256"]
        and value["declared_target_inversion_rings"]
        == geometries[target]["inversion_rings"]
        and value["declared_target_forward_rings"]
        == geometries[target]["forward_rings"]
        and value["support_profile"] == experiment["support_profile"]
        and value["local_support_radius_m"] == experiment["local_support_radius_m"]
        and canonical(value["regional_cover"]) == canonical(regional_cover)
        and inputs["taxa"] == taxa,
        "Forward geometry/fold/anchor/source identity differs",
    )
    for distance in value["distances_km"].values():
        _number(distance)
    n = len(taxa)
    for name in ("ppe", "regional_deposition"):
        _vector(inputs[name], n, positive=name == "ppe")
    require(
        inputs["ppe"]
        == [row["ppe"] for row in experiment["request_template"]["parameters"]],
        "Forward PPE differs from declared parameter axis",
    )
    require(
        type(inputs["local_k"]) is list and len(inputs["local_k"]) == 2,
        "Two local forward rings required",
    )
    for row in inputs["local_k"]:
        _vector(row, n)
    _vector(inputs["terrestrial_fraction"], 2)
    require(
        all(x <= 1 for x in inputs["terrestrial_fraction"]),
        "Terrestrial fractions exceed one",
    )
    require(
        type(value["full_k"]) is list and len(value["full_k"]) >= 2,
        "Complete forward rings required",
    )
    for row in value["full_k"]:
        _vector(row, n)
    _vector(value["full_terrestrial_fraction"], len(value["full_k"]))
    require(
        all(x <= 1 for x in value["full_terrestrial_fraction"])
        and inputs["local_k"] == value["full_k"][:2]
        and inputs["terrestrial_fraction"] == value["full_terrestrial_fraction"][:2],
        "Saved local/full forward factors disagree",
    )
    require(
        len(value["ring_bounds_m"]) == len(value["full_k"]),
        "Full ring boundary population differs",
    )
    previous = None
    for pair in value["ring_bounds_m"]:
        _vector(pair, 2)
        require(
            pair[0] < pair[1] and (previous is None or pair[0] == previous),
            "Noncontiguous forward ring boundaries",
        )
        previous = pair[1]
    _number(value["regional_cutoff_m"], positive=True)


def _join(
    training: dict[str, Any],
    frozen: dict[str, Any],
    experiment: dict[str, Any],
    geometries: dict[str, Any],
    geometry_pins: dict[str, Any],
    protocol: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, Any]]:
    require(
        training["schema_version"] == "author-love-transport-training.v1"
        and training["method"] == METHOD
        and training["candidate"] == protocol["nominal_candidate"]
        and training["protocol_sha256"] == protocol["nominal_training_protocol_sha256"],
        "Admitted nominal training header differs",
    )
    numeric = training["numerical_requests"]
    logical_rows = training["logical_requests"]
    require(
        type(numeric) is dict
        and len(numeric) == 39
        and type(logical_rows) is list
        and len(logical_rows) == 2715,
        "Complete39/2715 native population required",
    )
    require(
        digest(logical_rows) == protocol["logical_ancestry_sha256"],
        "Original logical ancestry differs",
    )
    taxa = experiment["request_template"]["taxa"]
    require(
        type(taxa) is list
        and len(taxa) == len(set(taxa)) == 30
        and all(type(x) is str and x for x in taxa),
        "Full thirty-taxon axis required",
    )
    parameters = experiment["request_template"]["parameters"]
    require(
        [row["taxon"] for row in parameters] == taxa, "Parameter taxon order differs"
    )
    sites = {row["record_id"]: row for row in experiment["sites"]}
    require(
        len(sites) == len(experiment["sites"]) == len(geometries) == 15
        and set(sites) == set(geometries),
        "Fifteen unique source site identities required",
    )
    records = [
        SiteRecord(row["record_id"], row["site_id"], tuple(row["identity_keys"]))
        for row in sites.values()
    ]
    outer_folds = grouped_leave_one_out(records)
    require(len(outer_folds) == 15, "Fifteen independent original site groups required")
    groups = {
        record: fold.test_group_ids[0]
        for fold in outer_folds
        for record in fold.test_record_ids
    }
    for record, geometry in geometries.items():
        sample = geometry["sample_metadata"]
        require(
            sample["site_id"] == sites[record]["site_id"]
            and sample["bin_id"] == "author-TW5"
            and sample["age_type"] == "calendar_bp"
            and sample["age_support_bp"] == [[1250, 1750]],
            "Source target time/identity differs",
        )
        for name, limit in (("latitude", 90), ("longitude", 180)):
            value = geometry[name]
            require(
                type(value) in (int, float)
                and math.isfinite(value)
                and abs(value) <= limit,
                "Finite source coordinate required",
            )
    covers = {}
    for key, row in numeric.items():
        require(
            re.fullmatch("[0-9a-f]{64}", key) is not None
            and row["request_sha256"] == key
            and row["taxa"] == taxa
            and row["item_id"] in sites
            and type(row["selections"]) is list
            and len(row["selections"]) == 2,
            "Native request/axis/ring owner differs",
        )
        _vector(row["regional_cover"], len(taxa))
        rings = []
        for ring, selected in enumerate(row["selections"]):
            require(
                type(selected) is dict
                and type(selected["ring_index"]) is int
                and selected["ring_index"] == ring
                and selected["request_sha256"] == key
                and re.fullmatch("[0-9a-f]{64}", selected["selected_attempt_sha256"])
                is not None,
                "Selected fit request/ring identity differs",
            )
            rings.append(_composition(selected["composition"], taxa))
        covers[key] = rings
    logical: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in logical_rows:
        require(
            set(row)
            == {
                "kind",
                "outer_target",
                "target",
                "fold",
                "local_record_id",
                "regional_anchor_record_id",
                "request_sha256",
            },
            "Closed logical ancestry row required",
        )
        logical[(row["kind"], row["outer_target"], row["target"])].append(row)
    slots = frozen["slots"]
    require(
        type(slots) is list and len(slots) == 3375,
        "Complete3375 frozen source slots required",
    )
    candidates: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    inventory: set[tuple[str, str, str, str, str]] = set()
    for row in slots:
        key = (row["kind"], row["outer_target"], row["target"])
        identity = (*key, row["method"], row["baseline"])
        require(
            key in logical
            and row["method"] in METHODS
            and row["baseline"] in BASELINES
            and identity not in inventory
            and row["status"] in {"predicted", "refused"},
            "Foreign/duplicate frozen candidate slot",
        )
        inventory.add(identity)
        if row["method"] == METHOD:
            candidates[key].append(row)
    support = {
        "support_profile": experiment["support_profile"],
        "local_support_radius_m": experiment["local_support_radius_m"],
        "taxa": taxa,
        "temporal_matching": experiment["request_template"]["temporal_matching"],
        "versions": experiment["request_template"]["versions"],
    }
    require(
        support["support_profile"] == "same-outer-radius-homogeneous-v1"
        and support["local_support_radius_m"] == 1000
        and experiment["local_ring_count"] == 2,
        "Declared local support differs",
    )
    support_id = "experiment-support:" + digest(support)
    contexts = []
    used_requests: set[str] = set()
    for outer in outer_folds:
        outer_target = outer.test_record_ids[0]
        inner = grouped_leave_one_out(
            [record for record in records if record.record_id in outer.train_record_ids]
        )
        for kind, fold in [("outer", outer), *(("inner", fold) for fold in inner)]:
            target = fold.test_record_ids[0]
            key = (kind, outer_target, target)
            require(
                outer_target not in fold.train_record_ids
                and target not in fold.train_record_ids,
                "Held-out owner leaked into fitting ancestry",
            )
            anchor = next(
                record
                for record in experiment["regional_priority"]
                if record in fold.train_record_ids
            )
            expected = set(fold.train_record_ids) - {anchor}
            rows = logical.pop(key)
            require(
                len(rows) == len(expected) == (13 if kind == "outer" else 12)
                and {row["local_record_id"] for row in rows} == expected
                and len({row["request_sha256"] for row in rows}) == len(rows),
                "Complete local predictor membership required",
            )
            predictors = []
            regional_cover: list[float] | None = None
            scientific_refs = []
            for row in sorted(rows, key=lambda item: item["local_record_id"]):
                request = row["request_sha256"]
                require(
                    request in numeric
                    and canonical(row["fold"]) == canonical(fold.as_dict())
                    and row["regional_anchor_record_id"] == anchor
                    and numeric[request]["item_id"] == row["local_record_id"],
                    "Selected training ownership/fold/anchor mismatch",
                )
                native = numeric[request]
                if regional_cover is None:
                    regional_cover = native["regional_cover"]
                require(
                    canonical(native["regional_cover"]) == canonical(regional_cover),
                    "Regional handoff differs between local fits",
                )
                fit_refs = [
                    "nominal-fit:"
                    + digest(
                        {
                            "request": request,
                            "selected_attempt": selected["selected_attempt_sha256"],
                        }
                    )
                    for selected in native["selections"]
                ]
                predictors.append(
                    {
                        "record_id": row["local_record_id"],
                        "group_id": groups[row["local_record_id"]],
                        "covers_by_ring": covers[request],
                        "request_sha256": request,
                        "selected_attempt_sha256s": [
                            selected["selected_attempt_sha256"]
                            for selected in native["selections"]
                        ],
                        "fit_refs": fit_refs,
                        "scientific_parent_ids": [row["local_record_id"], anchor],
                    }
                )
                scientific_refs.append(fit_refs[1])
                used_requests.add(request)
            selected_slots = candidates.pop(key)
            require(
                len(selected_slots) == 3
                and {row["baseline"] for row in selected_slots} == set(BASELINES)
                and all(
                    row["status"] == "predicted"
                    and canonical(row["fold"]) == canonical(fold.as_dict())
                    for row in selected_slots
                ),
                "Complete nominal saved geometry required",
            )
            forward = selected_slots[0]["geometry"]
            require(
                all(
                    canonical(row["geometry"]) == canonical(forward)
                    for row in selected_slots
                ),
                "Baseline-specific forward geometry differs",
            )
            by_baseline = {row["baseline"]: row for row in selected_slots}
            reference_baselines = []
            for baseline in BASELINES:
                prediction = by_baseline[baseline]["prediction"]
                require(
                    prediction["baseline"] == baseline
                    and prediction["fold_id"] == fold.fold_id
                    and prediction["record_id"] == target
                    and prediction["bin_id"] == "author-TW5",
                    "Saved reference prediction owner/fold/baseline differs",
                )
                for name in ("vegetation_fraction", "pollen_fraction"):
                    _composition(prediction[name], taxa)
                reference_baselines.append(
                    {
                        "baseline": baseline,
                        "vegetation_fraction": dict(prediction["vegetation_fraction"]),
                        "pollen_fraction": dict(prediction["pollen_fraction"]),
                    }
                )
            if regional_cover is None:
                raise ValueError("Missing regional handoff")
            _forward(
                forward,
                taxa=taxa,
                fold=fold.as_dict(),
                anchor=anchor,
                target=target,
                groups=groups,
                geometries=geometries,
                geometry_pins=geometry_pins,
                regional_cover=regional_cover,
                experiment=experiment,
            )
            contexts.append(
                {
                    "context_id": "author-spatial:"
                    + digest(
                        {
                            "kind": kind,
                            "outer_target": outer_target,
                            "target": target,
                            "fold": fold.as_dict(),
                        }
                    ),
                    "kind": kind,
                    "outer_target": outer_target,
                    "target": target,
                    "fold": fold.as_dict(),
                    "anchor": anchor,
                    "predictors": predictors,
                    "coordinates": {
                        record: {
                            name: geometries[record][name]
                            for name in ("latitude", "longitude")
                        }
                        for record in sorted(expected | {target})
                    },
                    "forward": forward,
                    "reference_baselines": reference_baselines,
                    "scientific_refs": {
                        "training_record_ids": list(fold.train_record_ids),
                        "selected_fit_ids": scientific_refs,
                        "regional_owner_id": anchor,
                        "support_id": support_id,
                        "target_geometry_id": "experiment-geometry:"
                        + geometry_pins[target]["sha256"],
                    },
                }
            )
    require(
        not logical
        and not candidates
        and len(contexts) == 225
        and used_requests == set(numeric)
        and len(inventory) == 3375,
        "Complete unique225 context join required",
    )
    return contexts, groups, support


def load_inputs(
    repository: Path, archive_root: Path, protocol: dict[str, Any]
) -> dict[str, Any]:
    """Read exact archived inputs once; return no observed pollen outcomes."""
    require(
        protocol["nominal_transport"] == METHOD
        and canonical(protocol["scales_km"]) == canonical([20.0, 100.0]),
        "Prospective fixed transport and scales required",
    )
    sources = protocol["sources"]
    require(
        set(sources) == {"nominal_training", "candidate_freeze", "recovered_shards"},
        "Exact saved scientific source inventory required",
    )
    reader = _Reader(repository, archive_root)
    authority = decode(reader.read(protocol["authority"], archived=False))
    require(
        authority["source_candidate"] == protocol["nominal_candidate"]
        and authority["independent_semantics"]["approved"] is True
        and authority["independent_semantics"]["scientific_saved_products_admitted"]
        is True,
        "Qualified saved-source authority required",
    )
    descriptor = decode(reader.read(sources["recovered_shards"]))
    require(
        descriptor["schema_version"] == "author-love-transport-shards.v1"
        and len(descriptor["shards"]) == len(METHODS)
        and {row["method"] for row in descriptor["shards"]} == set(METHODS),
        "Complete recovered transport source descriptor required",
    )
    nominal = next(row for row in descriptor["shards"] if row["method"] == METHOD)
    require(
        _same_identity(nominal["training"], sources["nominal_training"]),
        "Recovered training source differs",
    )
    admission = decode(reader.read(nominal["saved_product_admission"]))
    require(
        admission["approved"] is True
        and admission["scientific_saved_products_admitted"] is True
        and admission["candidate"] == protocol["nominal_candidate"]
        and admission["method"] == METHOD
        and admission["training_protocol_sha256"]
        == protocol["nominal_training_protocol_sha256"]
        and _same_identity(admission["training"], sources["nominal_training"]),
        "Selected saved training lacks independent source admission",
    )
    pins = protocol["author_inputs"]
    require(
        type(pins) is list and len(pins) == 37,
        "Original37 author source inputs required",
    )
    catalogue = {row["path"]: row for row in pins}
    require(
        len(catalogue) == 37 and all(Path(name).name == name for name in catalogue),
        "Unique basename source namespace required",
    )
    bodies = {}
    observation_refs = []
    for name, pin in catalogue.items():
        raw = reader.read(pin)
        if name.endswith("-raw.json"):
            observation_refs.append(dict(pin))
        else:
            bodies[name] = decode(raw)
    experiment = bodies["experiment.json"]
    expected_names = {
        "chronology.json",
        "decision.json",
        "dependency-lock.json",
        "experiment.json",
        "parameters.json",
        "source-report.json",
        "taxa.json",
    }
    geometries = {}
    geometry_pins = {}
    for site in experiment["sites"]:
        name = site["geometry"]["path"]
        raw_name = site["raw"]["path"]
        require(
            name in catalogue
            and raw_name in catalogue
            and set(site["geometry"]) == {"path", "sha256"}
            and set(site["raw"]) == {"path", "sha256"}
            and site["geometry"]["sha256"] == catalogue[name]["sha256"]
            and site["raw"]["sha256"] == catalogue[raw_name]["sha256"],
            "Source geometry/observation pin differs",
        )
        geometries[site["record_id"]] = bodies[name]
        geometry_pins[site["record_id"]] = catalogue[name]
        require(
            raw_name == name.replace("-geometry.json", "-raw.json"),
            "Declared observation/geometry filenames differ",
        )
        expected_names.update((name, raw_name))
    observation_owners = {
        site["raw"]["path"]: site["record_id"] for site in experiment["sites"]
    }
    require(
        len(observation_owners) == 15, "Unique unopened observation owners required"
    )
    observation_refs = [
        {**pin, "record_id": observation_owners[pin["path"]]}
        for pin in observation_refs
    ]
    require(
        set(catalogue) == expected_names and len(observation_refs) == 15,
        "Exact geometry/observation source population required",
    )
    training = decode(reader.read(sources["nominal_training"]))
    frozen = decode(reader.read(sources["candidate_freeze"]))
    contexts, groups, support = _join(
        training, frozen, experiment, geometries, geometry_pins, protocol
    )
    return {
        "schema_version": "author-lra-spatial-inputs.v1",
        "taxa": experiment["request_template"]["taxa"],
        "contexts": contexts,
        "groups": groups,
        "support": support,
        "observation_refs": sorted(observation_refs, key=lambda row: row["path"]),
        "sources": reader.refs,
        "summary": {
            "contexts": 225,
            "outer_contexts": 15,
            "inner_contexts": 210,
            "numerical_requests": 39,
            "logical_ancestry_rows": 2715,
            "frozen_source_slots": 3375,
            "source_bytes": reader.total,
            "outcomes_decoded": 0,
        },
    }
