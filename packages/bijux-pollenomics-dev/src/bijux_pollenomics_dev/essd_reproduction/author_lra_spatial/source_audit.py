"""Independent archive-to-packet custody for an already frozen spatial study.

The caller authenticates both prediction and selection freezes before invoking
this readback-only audit. No producer adapter, model, optimizer or outcome reader
is imported; observed counts are decoded only after all source joins pass.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

_METHOD = "gpm neutral"
_METHODS = {_METHOD, "gpm unstable", "lsm unstable", "lsm unstable low", "1overd"}
_BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")


def _check(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent source custody: " + message)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _same(value: Any, source: Any, label: str) -> None:
    _check(_canonical(value) == _canonical(source), label)


def _same_radius(value: Any, source: Any) -> None:
    """The saved typed radius may serialize an original integer as a float."""
    try:
        valid = (
            type(value) in (int, float)
            and type(source) in (int, float)
            and math.isfinite(value)
            and math.isfinite(source)
            and value > 0
            and source > 0
            and value == source
        )
    except OverflowError:
        valid = False
    _check(valid, "source forward support radius")


def _decode(raw: bytes) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in rows:
            _check(key not in value, "duplicate source JSON key")
            value[key] = item
        return value

    def invalid(value: str) -> Any:
        raise ValueError("Nonfinite source JSON: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


class _Sources:
    def __init__(self, repository: Path, archive: Path) -> None:
        self.repository = repository.resolve(strict=True)
        self.archive = archive.resolve(strict=True)
        self.refs: list[dict[str, Any]] = []
        self.size = 0

    def read(self, pin: dict[str, Any], *, authority: bool = False) -> bytes:
        _check(
            type(pin) is dict
            and set(pin) == {"path", "bytes", "sha256"}
            and type(pin["path"]) is str
            and bool(pin["path"])
            and type(pin["bytes"]) is int
            and 0 < pin["bytes"] <= 140 * 1024**2
            and type(pin["sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
            "closed bounded source pin",
        )
        sha = pin["sha256"]
        _check(
            all(row["sha256"] != sha for row in self.refs), "duplicate object identity"
        )
        if authority:
            relative = Path(pin["path"])
            _check(
                not relative.is_absolute() and ".." not in relative.parts,
                "authority path",
            )
            path = self.repository / relative
        else:
            path = self.archive / "objects" / sha[:2] / sha
        _check(
            path.is_file()
            and not any(part.is_symlink() for part in (path, *path.parents))
            and path.stat().st_size == pin["bytes"],
            "ordinary exact-size original object",
        )
        _check(self.size + pin["bytes"] <= 192 * 1024**2, "complete source byte bound")
        raw = path.read_bytes()
        _check(
            len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == sha,
            "source bytes differ",
        )
        self.size += len(raw)
        self.refs.append(
            {**pin, "storage": "repository" if authority else "archive_object"}
        )
        return raw


def _composition(value: Any, taxa: list[str]) -> list[float]:
    _check(
        type(value) is dict and set(value) == set(taxa),
        "complete source composition axis",
    )
    vector = [value[taxon] for taxon in taxa]
    _check(
        all(
            type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1 for x in vector
        ),
        "source composition domain",
    )
    _check(
        abs(math.fsum(vector) - 1) <= 1e-9, "source composition closure without repair"
    )
    return vector


def _groups(sites: list[dict[str, Any]]) -> dict[str, str]:
    _check(
        len(sites) == 15 and len({row["record_id"] for row in sites}) == 15,
        "fifteen source owners",
    )
    for index, row in enumerate(sites):
        for other in sites[index + 1 :]:
            own_keys, other_keys = (
                set(row["identity_keys"]),
                set(other["identity_keys"]),
            )
            own_names, other_names = (
                {row["record_id"], row["site_id"]},
                {other["record_id"], other["site_id"]},
            )
            _check(
                row["site_id"] != other["site_id"]
                and not own_keys.intersection(other_keys | other_names)
                and not other_keys.intersection(own_names),
                "source physical identity families overlap",
            )
    return {
        row["record_id"]: "site-group:" + _digest([row["record_id"]]) for row in sites
    }


def _fold(groups: dict[str, str], outer: str, target: str) -> dict[str, Any]:
    training = sorted(set(groups) - {outer, target})
    return {
        "fold_id": groups[target],
        "train_record_ids": training,
        "test_record_ids": [target],
        "train_group_ids": sorted(groups[owner] for owner in training),
        "test_group_ids": [groups[target]],
    }


def _contexts(
    packet: dict[str, Any],
    protocol: dict[str, Any],
    training: dict[str, Any],
    frozen: dict[str, Any],
    experiment: dict[str, Any],
    geometries: dict[str, Any],
    pins: dict[str, Any],
) -> None:
    taxa = experiment["request_template"]["taxa"]
    _check(
        type(taxa) is list
        and len(taxa) == len(set(taxa)) == 30
        and all(type(x) is str and x for x in taxa),
        "source thirty-taxon axis",
    )
    _same(packet["taxa"], taxa, "packet/source taxon order")
    parameters = experiment["request_template"]["parameters"]
    _check(
        type(parameters) is list and [row["taxon"] for row in parameters] == taxa,
        "source parameter taxon order",
    )
    ppe = [row["ppe"] for row in parameters]
    _check(
        all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in ppe),
        "source positive PPE axis",
    )
    sites = experiment["sites"]
    groups = _groups(sites)
    _same(packet["groups"], groups, "source physical group identities")
    support = {
        key: experiment[key] for key in ("support_profile", "local_support_radius_m")
    } | {
        "taxa": taxa,
        **{
            key: experiment["request_template"][key]
            for key in ("temporal_matching", "versions")
        },
    }
    _check(
        support["support_profile"] == "same-outer-radius-homogeneous-v1"
        and support["local_support_radius_m"] == 1000
        and experiment["local_ring_count"] == 2,
        "fixed source support",
    )
    _same(packet["support"], support, "source support metadata")
    _check(
        training["schema_version"] == "author-love-transport-training.v1"
        and training["method"] == _METHOD
        and training["candidate"] == protocol["nominal_candidate"]
        and training["protocol_sha256"] == protocol["nominal_training_protocol_sha256"],
        "native training identity",
    )
    numeric, logical = training["numerical_requests"], training["logical_requests"]
    _check(
        type(numeric) is dict
        and len(numeric) == 39
        and type(logical) is list
        and len(logical) == 2715,
        "39 numerical/2715 logical source requests",
    )
    _check(
        _digest(logical) == protocol["logical_ancestry_sha256"],
        "logical source identity",
    )
    links: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in logical:
        _check(
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
            "closed source ancestry",
        )
        links[(row["kind"], row["outer_target"], row["target"])].append(row)
    slots = frozen["slots"]
    _check(
        type(slots) is list and len(slots) == 3375,
        "3375 complete original candidate slots",
    )
    slot_index = {}
    for row in slots:
        key = (
            row["kind"],
            row["outer_target"],
            row["target"],
            row["method"],
            row["baseline"],
        )
        _check(
            key not in slot_index
            and row["method"] in _METHODS
            and row["baseline"] in _BASELINES
            and row["status"] in {"predicted", "refused"},
            "unique declared source candidate slot",
        )
        slot_index[key] = row
    rows = packet["contexts"]
    _check(type(rows) is list and len(rows) == 225, "complete 225 packet contexts")
    contexts = {(row["kind"], row["outer_target"], row["target"]): row for row in rows}
    roles = {
        (kind, outer, target)
        for outer in groups
        for target in groups
        for kind in ["outer" if outer == target else "inner"]
    }
    _check(
        set(contexts) == set(links) == roles and len(contexts) == 225,
        "complete independent outer/inner population",
    )
    _check(
        set(slot_index)
        == {
            (*role, method, baseline)
            for role in roles
            for method in _METHODS
            for baseline in _BASELINES
        },
        "source five-method population completeness",
    )
    used = set()
    for role_key in sorted(roles):
        context = contexts[role_key]
        kind, outer, target = role_key
        fold = _fold(groups, outer, target)
        anchor = next(
            owner
            for owner in experiment["regional_priority"]
            if owner in fold["train_record_ids"]
        )
        _same(context["fold"], fold, "source-independent exclusion fold")
        _check(context["anchor"] == anchor, "source regional priority")
        _check(
            context["context_id"]
            == "author-spatial:"
            + _digest(
                {"kind": kind, "outer_target": outer, "target": target, "fold": fold}
            ),
            "context scientific identity",
        )
        owners = sorted(set(fold["train_record_ids"]) - {anchor})
        source_links = links[role_key]
        _check(
            len(source_links) == len(owners)
            and {row["local_record_id"] for row in source_links} == set(owners),
            "all local source owners",
        )
        predictors = {row["record_id"]: row for row in context["predictors"]}
        _check(
            len(predictors) == len(context["predictors"]) == len(owners)
            and set(predictors) == set(owners),
            "complete predictor ownership",
        )
        selected_fits = []
        regional = None
        for link in sorted(source_links, key=lambda row: row["local_record_id"]):
            request = link["request_sha256"]
            _check(
                request in numeric
                and re.fullmatch(r"[0-9a-f]{64}", request) is not None
                and link["regional_anchor_record_id"] == anchor,
                "source fit owner and request",
            )
            _same(link["fold"], fold, "saved request fold")
            native = numeric[request]
            _check(
                native["request_sha256"] == request
                and native["item_id"] == link["local_record_id"]
                and native["taxa"] == taxa,
                "selected native request binding",
            )
            selected = native["selections"]
            _check(
                type(selected) is list and len(selected) == 2,
                "both selected source rings",
            )
            covers, attempts, fits = [], [], []
            for ring, selection in enumerate(selected):
                _check(
                    type(selection["ring_index"]) is int
                    and selection["ring_index"] == ring
                    and selection["request_sha256"] == request
                    and re.fullmatch(
                        r"[0-9a-f]{64}", selection["selected_attempt_sha256"]
                    )
                    is not None,
                    "source selected attempt/ring",
                )
                covers.append(_composition(selection["composition"], taxa))
                attempts.append(selection["selected_attempt_sha256"])
                fits.append(
                    "nominal-fit:"
                    + _digest({"request": request, "selected_attempt": attempts[-1]})
                )
            expected = {
                "record_id": native["item_id"],
                "group_id": groups[native["item_id"]],
                "covers_by_ring": covers,
                "request_sha256": request,
                "selected_attempt_sha256s": attempts,
                "fit_refs": fits,
                "scientific_parent_ids": [native["item_id"], anchor],
            }
            _same(
                predictors[native["item_id"]],
                expected,
                "exact saved training covers and ancestry",
            )
            if regional is None:
                regional = native["regional_cover"]
            _same(native["regional_cover"], regional, "shared source regional handoff")
            selected_fits.append(fits[1])
            used.add(request)
        baseline_rows = [
            slot_index[(*role_key, _METHOD, baseline)] for baseline in _BASELINES
        ]
        references = []
        for row in baseline_rows:
            _check(
                row["status"] == "predicted", "all 675 nominal source slots predicted"
            )
            _same(row["fold"], fold, "nominal slot fold")
            _same(
                row["geometry"],
                context["forward"],
                "full source forward geometry/baseline agreement",
            )
            prediction = row["prediction"]
            _check(
                prediction["fold_id"] == fold["fold_id"]
                and prediction["record_id"] == target
                and prediction["bin_id"] == "author-TW5"
                and prediction["baseline"] == row["baseline"],
                "source baseline prediction ownership",
            )
            for field in ("vegetation_fraction", "pollen_fraction"):
                _composition(prediction[field], taxa)
            references.append(
                {
                    field: prediction[field]
                    for field in ("baseline", "vegetation_fraction", "pollen_fraction")
                }
            )
        _same(
            context["reference_baselines"], references, "all nominal reference vectors"
        )
        forward = context["forward"]
        _same(forward["forward_inputs"]["taxa"], taxa, "saved forward taxon axis")
        _same(forward["forward_inputs"]["ppe"], ppe, "experiment-to-saved-forward PPE")
        _same(
            forward["support_profile"],
            experiment["support_profile"],
            "source forward support profile",
        )
        _same_radius(
            forward["local_support_radius_m"],
            experiment["local_support_radius_m"],
        )
        _same(forward["regional_cover"], regional, "forward regional source cover")
        _same(forward["outer_fold"], fold, "forward source fold")
        _check(
            forward["regional_anchor_record_id"] == anchor
            and forward["regional_anchor_group_id"] == groups[anchor],
            "forward anchor identity",
        )
        _same(
            forward["regional_value_source_record_ids"],
            [anchor],
            "regional value ownership",
        )
        _same(
            forward["regional_identity_source_record_ids"],
            fold["train_record_ids"],
            "regional conservative dependency owners",
        )
        _check(
            forward["regional_identity_policy"]
            == "conservative_all_training_fit_receipts",
            "regional identity policy",
        )
        _same(
            forward["declared_target_inversion_rings"],
            geometries[target]["inversion_rings"],
            "source inversion geometry",
        )
        _same(
            forward["declared_target_forward_rings"],
            geometries[target]["forward_rings"],
            "source forward geometry",
        )
        _check(
            forward["target_geometry_sha256"] == pins[target]["sha256"],
            "target geometry original identity",
        )
        _same(
            context["coordinates"],
            {
                owner: {
                    field: geometries[owner][field]
                    for field in ("latitude", "longitude")
                }
                for owner in sorted(set(owners) | {target})
            },
            "source literal coordinates",
        )
        _same(
            context["scientific_refs"],
            {
                "training_record_ids": fold["train_record_ids"],
                "selected_fit_ids": selected_fits,
                "regional_owner_id": anchor,
                "support_id": "experiment-support:" + _digest(support),
                "target_geometry_id": "experiment-geometry:" + pins[target]["sha256"],
            },
            "source-derived scientific references",
        )
    _check(used == set(numeric), "all 39 source request selections consumed")


def bind_sources(
    repository: Path,
    archive_root: Path,
    protocol: dict[str, Any],
    packet: dict[str, Any],
) -> tuple[dict[str, dict[str, int]], dict[str, Any]]:
    """Authenticate source custody after the caller closes both scientific freezes."""
    _check(
        protocol["nominal_transport"] == _METHOD
        and protocol["scales_km"] == [20.0, 100.0],
        "prospective nominal method/scales",
    )
    _check(packet["schema_version"] == "author-lra-spatial-inputs.v1", "packet schema")
    reader = _Sources(repository, archive_root)
    authority = _decode(reader.read(protocol["authority"], authority=True))
    _check(
        authority["source_candidate"] == protocol["nominal_candidate"]
        and authority["independent_semantics"]["approved"] is True
        and authority["independent_semantics"]["scientific_saved_products_admitted"]
        is True,
        "source admission authority",
    )
    sources = protocol["sources"]
    _check(
        set(sources) == {"nominal_training", "candidate_freeze", "recovered_shards"},
        "scientific input inventory",
    )
    descriptor = _decode(reader.read(sources["recovered_shards"]))
    _check(
        descriptor["schema_version"] == "author-love-transport-shards.v1"
        and len(descriptor["shards"]) == 5
        and {row["method"] for row in descriptor["shards"]} == _METHODS,
        "complete recovered method descriptors",
    )
    nominal = next(row for row in descriptor["shards"] if row["method"] == _METHOD)
    _same(
        {key: nominal["training"][key] for key in ("bytes", "sha256")},
        {key: sources["nominal_training"][key] for key in ("bytes", "sha256")},
        "recovered training identity",
    )
    admission = _decode(reader.read(nominal["saved_product_admission"]))
    _check(
        admission["approved"] is True
        and admission["scientific_saved_products_admitted"] is True
        and admission["candidate"] == protocol["nominal_candidate"]
        and admission["method"] == _METHOD
        and admission["training_protocol_sha256"]
        == protocol["nominal_training_protocol_sha256"],
        "selected fit admission certificate",
    )
    _same(
        {key: admission["training"][key] for key in ("bytes", "sha256")},
        {key: sources["nominal_training"][key] for key in ("bytes", "sha256")},
        "admitted selected training bytes",
    )
    author = protocol["author_inputs"]
    _check(
        type(author) is list and len(author) == 37, "37 exact original author inputs"
    )
    catalogue = {pin["path"]: pin for pin in author}
    _check(
        len(catalogue) == 37 and all(Path(name).name == name for name in catalogue),
        "unique source basenames",
    )
    bodies = {
        name: _decode(reader.read(pin))
        for name, pin in catalogue.items()
        if not name.endswith("-raw.json")
    }
    experiment = bodies["experiment.json"]
    sites = experiment["sites"]
    geometry_pins, geometries, observation_refs = {}, {}, []
    expected_names = {
        "chronology.json",
        "decision.json",
        "dependency-lock.json",
        "experiment.json",
        "parameters.json",
        "source-report.json",
        "taxa.json",
    }
    for site in sites:
        record = site["record_id"]
        geometry_name, raw_name = site["geometry"]["path"], site["raw"]["path"]
        _check(
            record not in geometries
            and geometry_name in bodies
            and raw_name in catalogue
            and raw_name == geometry_name.replace("-geometry.json", "-raw.json"),
            "unique geometry/observation source owner",
        )
        for role, name in (("geometry", geometry_name), ("raw", raw_name)):
            _same(
                site[role],
                {"path": name, "sha256": catalogue[name]["sha256"]},
                "author declared source identity",
            )
        geometry = bodies[geometry_name]
        for field, limit in (("latitude", 90), ("longitude", 180)):
            coordinate = geometry[field]
            _check(
                type(coordinate) in (int, float)
                and math.isfinite(coordinate)
                and abs(coordinate) <= limit,
                "source finite geographic coordinate",
            )
        metadata = geometry["sample_metadata"]
        _check(
            metadata["site_id"] == site["site_id"]
            and metadata["bin_id"] == "author-TW5"
            and metadata["age_type"] == "calendar_bp"
            and metadata["age_support_bp"] == [[1250, 1750]],
            "source sample owner and chronology",
        )
        geometries[record], geometry_pins[record] = geometry, catalogue[geometry_name]
        observation_refs.append({**catalogue[raw_name], "record_id": record})
        expected_names.update((geometry_name, raw_name))
    _check(
        set(catalogue) == expected_names
        and len(geometries) == len(observation_refs) == 15,
        "complete original owner/source inventory",
    )
    _same(
        packet["observation_refs"],
        sorted(observation_refs, key=lambda row: row["path"]),
        "source-bound observation references",
    )
    training = _decode(reader.read(sources["nominal_training"]))
    frozen = _decode(reader.read(sources["candidate_freeze"]))
    _contexts(packet, protocol, training, frozen, experiment, geometries, geometry_pins)
    counts = {}
    for site in sites:
        record, raw_name = site["record_id"], site["raw"]["path"]
        raw = _decode(reader.read(catalogue[raw_name]))
        sample, metadata = raw["sample"], geometries[record]["sample_metadata"]
        _check(
            set(raw) == {"data_kind", "taxa", "sample"}
            and raw["data_kind"] == "source_observations",
            "original observation document",
        )
        _same(raw["taxa"], packet["taxa"], "observation taxon order")
        _check(
            set(sample) == set(metadata) | {"counts"},
            "exact observation metadata fields",
        )
        _same(
            {key: sample[key] for key in metadata},
            metadata,
            "observation geometry/time/owner join",
        )
        vector = sample["counts"]
        _check(
            type(vector) is list
            and len(vector) == 30
            and all(type(x) is int and x >= 0 for x in vector)
            and 0 < sum(vector) <= 2**53,
            "integer original counted denominator",
        )
        counts[record] = dict(zip(packet["taxa"], vector, strict=True))
    _check(len(reader.refs) == 42, "complete 42-object independent source readback")
    _same(
        sorted(packet["sources"], key=lambda pin: pin["sha256"]),
        sorted(reader.refs, key=lambda pin: pin["sha256"]),
        "complete packet source accounting",
    )
    _same(
        packet["summary"],
        {
            "contexts": 225,
            "outer_contexts": 15,
            "inner_contexts": 210,
            "numerical_requests": 39,
            "logical_ancestry_rows": 2715,
            "frozen_source_slots": 3375,
            "source_bytes": reader.size,
            "outcomes_decoded": 0,
        },
        "source input preparation summary",
    )
    return counts, {
        "passed": True,
        "source_objects": len(reader.refs),
        "source_bytes": reader.size,
        "author_inputs": 37,
        "contexts": 225,
        "nominal_source_slots": 675,
        "all_source_candidate_slots": 3375,
        "numerical_requests": 39,
        "logical_requests": 2715,
        "observed_owners": len(counts),
        "counted_mass": sum(sum(row.values()) for row in counts.values()),
        "scope": "Exact original bytes, literal source-to-packet joins and observed denominators; no new fits, kernels, spatial replay or claim of caller-freeze enforcement",
    }
