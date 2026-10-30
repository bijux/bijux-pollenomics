"""Bind qualified saved count owners and target-free numerical fold inputs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Any

from .draws import CountOwner
from .predictions import FoldCase, LocalKernel

AXIS = ("Betula", "Ulmus")
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
NAMES = tuple(f"cal-bp-{n}-{n + 500}" for n in range(2700, 5700, 500))
SMALL = ("BOKE", "BUS", "SOLSOE83")
CORES = (*SMALL, "KRAGMJNY")
PARAMETERS = (
    {"taxon": "Betula", "fallspeed_m_s": 0.024, "ppe": 5.106, "ppe_sd": 0.303},
    {"taxon": "Ulmus", "fallspeed_m_s": 0.032, "ppe": 1.27, "ppe_sd": 0.05},
)
NATIVE = {
    "BOKE": (28872, 54001, 39241, 38422),
    "BUS": (28869, 53995, 39238, 38418),
    "SOLSOE83": (3432, 4446, 4304, 25740),
    "KRAGMJNY": (3204, 23013, 16622, 13366),
}


class InputError(ValueError):
    """A saved source, role, parameter or population binding is inconsistent."""


@dataclass(frozen=True)
class InputPacket:
    """Keep complete accounting separate from the three numerical fold cases."""

    owners: tuple[CountOwner, ...]
    cases: tuple[FoldCase, ...]
    folds: tuple[dict[str, Any], ...]
    dispositions: tuple[dict[str, Any], ...]
    nominal_predictions: tuple[dict[str, Any], ...]
    accounting: dict[str, Any]
    source_files: tuple[dict[str, Any], ...]


def require(condition: object, message: str) -> None:
    """Raise InputError when a predictive-input condition fails."""
    if not condition:
        raise InputError(message)


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _same(left: object, right: object) -> bool:
    return _canonical(left) == _canonical(right)


def _decode(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            require(key not in result, "Duplicate saved JSON key")
            result[key] = value
        return result

    def nonfinite(value: str) -> Any:
        raise InputError("Nonfinite JSON literal: " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _number(value: Any, *, positive: bool = False) -> float:
    require(type(value) in (int, float), "Strict saved numeric value required")
    require(
        math.isfinite(value) and (value > 0 if positive else value >= 0),
        "Saved numeric domain differs",
    )
    return float(value)


def _integer(value: Any, *, positive: bool = False) -> int:
    require(
        type(value) is int and (value > 0 if positive else value >= 0),
        "Strict saved integer required",
    )
    return int(value)


def _pair(values: Any, *, positive: bool = False) -> tuple[float, float]:
    require(type(values) is list and len(values) == 2, "Exact two-taxon axis required")
    return (
        _number(values[0], positive=positive),
        _number(values[1], positive=positive),
    )


class _Reader:
    def __init__(self, repository: Path) -> None:
        self.repository = repository.resolve(strict=True)
        self.refs: dict[str, dict[str, Any]] = {}
        self.raw: dict[str, bytes] = {}
        self.total = 0

    def path(self, value: str | Path) -> Path:
        relative = Path(value)
        require(".." not in relative.parts, "Parent path refused")
        path = relative if relative.is_absolute() else self.repository / relative
        require(
            path.resolve().is_relative_to(self.repository),
            "Source must remain in repository",
        )
        require(
            not any(p.is_symlink() for p in (path, *path.parents)),
            "Source alias refused",
        )
        return path

    def read(
        self,
        pin: dict[str, Any],
        *,
        base: Path | None = None,
        decode: bool = True,
        maximum: int = 4194304,
    ) -> Any:
        require(
            isinstance(pin, dict) and isinstance(pin.get("path"), str),
            "Source pin path required",
        )
        require(
            isinstance(pin.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
            "Source digest required",
        )
        path = self.path((base / pin["path"]) if base is not None else pin["path"])
        relative = path.relative_to(self.repository).as_posix()
        if relative not in self.raw:
            before = path.stat()
            require(
                path.is_file() and before.st_size <= maximum,
                "Bounded ordinary source required",
            )
            raw = path.read_bytes()
            after = path.stat()
            fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
            require(
                all(getattr(before, k) == getattr(after, k) for k in fields)
                and len(raw) == before.st_size <= maximum,
                "Source changed during read",
            )
            self.total += len(raw)
            require(self.total <= 64 * 1024 * 1024, "Saved source read ceiling")
            self.raw[relative] = raw
            self.refs[relative] = {
                "path": relative,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        raw = self.raw[relative]
        require(
            len(raw) <= maximum and self.refs[relative]["sha256"] == pin["sha256"],
            "Saved source digest differs",
        )
        if "bytes" in pin:
            require(_integer(pin["bytes"]) == len(raw), "Saved source size differs")
        return _decode(raw) if decode else raw

    def member(
        self, base: Path, files: dict[str, Any], name: str, *, decode: bool = True
    ) -> Any:
        require(name in files, "Saved native member is absent: " + name)
        return self.read(
            {"path": name, "sha256": files[name]}, base=base, decode=decode
        )


def _owner_id(core: str, name: str) -> str:
    _, dataset, unit, _ = NATIVE[core]
    return f"neotoma-{dataset}-{unit}-{name}"


def _same_pin(reader: _Reader, left: dict[str, Any], right: dict[str, Any]) -> bool:
    return reader.path(left["path"]) == reader.path(right["path"]) and all(
        type(left[k]) is type(right[k]) and left[k] == right[k]
        for k in ("bytes", "sha256")
    )


def _counts(raw: dict[str, Any], core: str, name: str) -> tuple[int, int]:
    require(
        raw["data_kind"] == "source_observations" and raw["taxa"] == list(AXIS),
        "Materialized count axis differs",
    )
    sample = raw["sample"]
    younger = int(name.split("-")[2])
    window = [float(younger), float(younger + 500)]
    require(
        sample["sample_id"] == _owner_id(core, name)
        and sample["site_id"] == f"neotoma-site-{NATIVE[core][0]}"
        and sample["bin_id"] == name,
        "Materialized source owner differs",
    )
    require(
        sample["age_type"] == "calendar_bp"
        and sample["age_support_bp"] == [window]
        and sample["coordinate"] == window[0]
        and type(sample["coordinate"]) in (int, float),
        "Frozen source chronology differs",
    )
    values = sample["counts"]
    require(type(values) is list and len(values) == 2, "Integer count pair required")
    counts = (_integer(values[0]), _integer(values[1]))
    require(0 < sum(counts) <= 2**53, "Positive exact panel denominator required")
    return counts


def _projection(
    row: dict[str, Any], counts: tuple[int, int], core: str, name: str
) -> None:
    site, dataset, unit, chronology = NATIVE[core]
    require(
        all(
            type(row[k]) is int
            for k in [
                "native_site",
                "native_dataset",
                "native_collection_unit",
                "selected_chronology",
            ]
        ),
        "Native identity must use strict integers",
    )
    require(
        (
            row["native_site"],
            row["native_dataset"],
            row["native_collection_unit"],
            row["selected_chronology"],
        )
        == (site, dataset, unit, chronology),
        "Qualified native source identity differs",
    )
    require(
        _integer(row["projected_panel_N"], positive=True) == sum(counts),
        "Projected panel denominator differs",
    )
    if core == "KRAGMJNY":
        require(
            row["native_collection_default_reference"] == 13365
            and type(row["native_collection_default_reference"]) is int
            and row["source_default_flags"] == {"13365": True, "13366": True}
            and all(type(v) is bool for v in row["source_default_flags"].values()),
            "Conflicting native default declarations must be retained",
        )
        require(
            _integer(row["reported_pollen_N"]) - _integer(row["excluded_pollen_N"])
            == sum(counts),
            "KRAG full/excluded mass differs",
        )
    else:
        require(
            row["record_id"] == _owner_id(core, name)
            and row["projected_axis"] == list(AXIS),
            "Original small-source projection differs",
        )
        require(
            _integer(row["source_panel_N"]) - _integer(row["excluded_panel_N"])
            == sum(counts),
            "Original full/excluded mass differs",
        )
        support = row["qualified_source_support"]
        require(
            _integer(support["native_sample_count"], positive=True) > 0
            and support["source_support_sha256"] == row["source_support_sha256"]
            and re.fullmatch(r"[0-9a-f]{64}", row["source_support_sha256"]) is not None,
            "Qualified small-source support differs",
        )
        younger = int(name.split("-")[2])
        require(
            support["window"] == [float(younger), float(younger + 500)],
            "Qualified support window differs",
        )


def _matrix_csv(
    raw: bytes, rings: list[dict[str, Any]]
) -> tuple[tuple[float, float], ...]:
    reader = csv.DictReader(io.StringIO(raw.decode()))
    require(reader.fieldnames == ["index", *AXIS], "Saved kernel taxon axis differs")
    rows = list(reader)
    require(len(rows) == len(rings) == 2, "Exactly two saved inversion rings required")
    result = []
    for row, ring in zip(rows, rings, strict=True):
        index = float(row["index"])
        require(
            math.isfinite(index) and index == _number(ring["mean_m"], positive=True),
            "Saved kernel ring order differs",
        )
        values = tuple(float(row[t]) for t in AXIS)
        require(
            all(math.isfinite(v) and v >= 0 for v in values),
            "Invalid saved kernel coefficient",
        )
        result.append((values[0], values[1]))
    return tuple(result)


def _regional_csv(raw: bytes) -> tuple[float, float]:
    reader = csv.DictReader(io.StringIO(raw.decode()))
    require(
        reader.fieldnames == ["index", "K"], "Regional deposition table axis differs"
    )
    rows = list(reader)
    require(
        [row["index"] for row in rows] == list(AXIS), "Regional taxon row order differs"
    )
    return (
        _number(float(rows[0]["K"]), positive=True),
        _number(float(rows[1]["K"]), positive=True),
    )


def _geometry(
    value: dict[str, Any], declaration: dict[str, Any], *, regional: bool
) -> None:
    radius = _number(declaration["radius_m"], positive=True)
    require(
        _pair([value["longitude"], value["latitude"]])
        == _pair([declaration["longitude"], declaration["latitude"]]),
        "Frozen source coordinates differ",
    )
    require(
        value["basin"] == {"diameter_m": 2 * radius, "site_type": "lake"},
        "Frozen static basin differs",
    )
    if regional:
        require(
            set(value) == {"basin", "sample_metadata", "longitude", "latitude"},
            "Regional-only geometry cannot acquire local rings",
        )
        return
    for field, edges in [
        ("inversion_rings", [radius + 1, 500.0, 1000.0]),
        ("forward_rings", [radius, 500.0, 1000.0, 10000.0, 100000.0]),
    ]:
        rows = value[field]
        require(len(rows) == len(edges) - 1, "Frozen geometry ring count differs")
        for row, lo, hi in zip(rows, edges[:-1], edges[1:], strict=True):
            require(
                _number(row["inner_m"], positive=True) == lo
                and _number(row["outer_m"], positive=True) == hi
                and _number(row["mean_m"], positive=True) == (lo + hi) / 2,
                "Frozen geometry ring grid differs",
            )
            require(
                _number(row["ring_area_m2"], positive=True)
                == _number(row["terrestrial_area_m2"], positive=True),
                "Frozen all-terrestrial geometry differs",
            )


def _native_kernel(
    reader: _Reader,
    item: dict[str, Any],
    owner: str,
    regional: str,
    raw_sources: dict[str, dict[str, Any]],
    geometries: dict[str, dict[str, Any]],
) -> tuple[LocalKernel, tuple[float, float]]:
    require(
        item["item_id"] == owner and item["item_status"] == "completed",
        "Active native item owner/status differs",
    )
    product = item["product"]
    directory = reader.path(product["directory"])
    manifest = reader.read(
        {"path": str(directory / "manifest.json"), "sha256": product["manifest_sha256"]}
    )
    require(
        manifest["schema_version"] == "lra-product.v1"
        and manifest["scientific_content_sha256"]
        == product["scientific_content_sha256"]
        and manifest["retained_taxa"] == list(AXIS),
        "Saved native product identity differs",
    )
    files = manifest["files"]
    request = reader.member(directory, files, "request.json")
    require(
        hashlib.sha256(_canonical(request)).hexdigest()
        == item["request_sha256"]
        == manifest["request_sha256"],
        "Native request identity differs",
    )
    require(
        request["taxa"] == list(AXIS)
        and request["pollen_unit"] == "count"
        and request["parameters"] == list(PARAMETERS)
        and request["data_kind"] == "source_observations",
        "Native axis/parameter profile differs",
    )
    require(
        _same(
            request["local"]["samples"],
            [{**raw_sources[owner]["sample"], "raw_evidence_id": "raw:" + owner}],
        )
        and _same(
            request["regional"]["samples"],
            [{**raw_sources[regional]["sample"], "raw_evidence_id": "raw:" + regional}],
        ),
        "Native request count owners differ",
    )
    require(
        request["rings"]
        == [
            {**ring, "geometry_evidence_id": "geometry:" + owner}
            for ring in geometries[owner]["inversion_rings"]
        ],
        "Saved inversion geometry differs",
    )
    local = _matrix_csv(
        reader.member(
            directory, files, "numerical/local_love/aux_Kloc.csv", decode=False
        ),
        request["rings"],
    )
    regional_k = _matrix_csv(
        reader.member(
            directory, files, "numerical/local_love/aux_Kreg.csv", decode=False
        ),
        request["rings"],
    )
    deposition = _regional_csv(
        reader.member(
            directory,
            files,
            "numerical/regional_reveals/deposition_factors.csv",
            decode=False,
        )
    )
    return LocalKernel(owner_id=owner, local_k=local, regional_k=regional_k), deposition


def _load_inputs(repository: Path, protocol: dict[str, Any]) -> InputPacket:
    """Read only qualified saved products; never enter score or native fit APIs."""
    require(
        set(protocol["sources"])
        == {"coupled_protocol", "input_index", "prediction_batch"},
        "Exact three source declarations required",
    )
    sampling = protocol["sampling"]
    require(
        type(sampling["replicates"]) is int
        and sampling["replicates"] == 1024
        and type(sampling["seed"]) is int
        and sampling["seed"] == 20261027
        and sampling["taxa"] == list(AXIS)
        and _pair(sampling["ppe_means"], positive=True) == (5.106, 1.27)
        and _pair(sampling["ppe_sds"], positive=True) == (0.303, 0.05),
        "Declared sampling/PPE profile differs",
    )
    reader = _Reader(repository)
    sources = protocol["sources"]
    coupled = reader.read(sources["coupled_protocol"])
    require(
        coupled["axis"] == list(AXIS)
        and coupled["parameters"] == list(PARAMETERS)
        and [r["id"] for r in coupled["small_cores"]] == list(SMALL),
        "Original source/parameter contract differs",
    )
    index = reader.read(sources["input_index"])
    batch = reader.read(sources["prediction_batch"])
    require(
        _same_pin(reader, index["protocol"], sources["coupled_protocol"])
        and _same_pin(reader, batch["protocol"], sources["coupled_protocol"])
        and _same_pin(reader, batch["input_index"], sources["input_index"]),
        "Materialization/prediction source pins disagree",
    )
    require(
        batch["operation"] == "prepare"
        and batch["all_bins_accounted"] is True
        and batch["requested_folds"] == 18
        and batch["requested_method_dispositions"] == 54
        and batch["status_counts"] == {"predicted": 9, "refused": 45},
        "Original prediction population differs",
    )
    require(
        [b["bin"] for b in batch["bins"]] == list(NAMES)
        and [e["directory"] for e in index["experiments"]] == list(NAMES),
        "Exact six ordered windows required",
    )
    inputs_root = reader.path(sources["input_index"]["path"]).parent
    predictions_root = reader.path(sources["prediction_batch"]["path"]).parent
    expected_members = {
        f"{name}/{member}.json"
        for name in NAMES
        for member in [
            *(f"{core}-{kind}" for core in CORES for kind in ["raw", "geometry"]),
            "chronology",
            "taxa",
            "parameters",
            "dependency_lock",
            "decision",
            "experiment",
            "projection",
        ]
    }
    member_pins = {p["path"]: p for p in index["members"]}
    require(
        len(member_pins) == len(index["members"]) == 90
        and set(member_pins) == expected_members,
        "Exact 90-member materialization required",
    )
    materialized = {
        name: reader.read(pin, base=inputs_root, maximum=65536)
        for name, pin in member_pins.items()
    }
    for pin in index["qualified_source_inputs"]:
        reader.read(pin, decode=False)
    require(
        _same_pin(reader, index["krag_audit"], coupled["krag_audit"]),
        "Original KRAG audit identity differs",
    )
    reader.read(index["krag_audit"], decode=False)
    owners = []
    cases = []
    folds = []
    nominal = []
    lineage: dict[str, Any] = {}
    all_dispositions = batch["method_dispositions"]
    require(
        type(all_dispositions) is list and len(all_dispositions) == 54,
        "Every original method disposition required",
    )
    disposition_keys = [(r["bin"], r["fold_id"], r["method"]) for r in all_dispositions]
    require(len(set(disposition_keys)) == 54, "Duplicate nominal disposition")
    expected_keys: list[tuple[str, str, str]] = []
    for bin_row, experiment_index in zip(
        batch["bins"], index["experiments"], strict=True
    ):
        name = bin_row["bin"]
        directory = inputs_root / name
        experiment = materialized[name + "/experiment.json"]
        require(
            experiment_index["experiment"]["sha256"]
            == member_pins[name + "/experiment.json"]["sha256"],
            "Experiment index digest differs",
        )
        ids = {core: _owner_id(core, name) for core in CORES}
        regional = ids["KRAGMJNY"]
        require(
            experiment["target_record_ids"]
            == experiment_index["target_record_ids"]
            == [ids[c] for c in SMALL]
            and experiment["regional_priority"] == [regional]
            and experiment_index["regional_source_record_id"] == regional,
            "Frozen source roles differ",
        )
        require(
            experiment["request_template"]["parameters"] == list(PARAMETERS)
            and experiment["request_template"]["taxa"] == list(AXIS),
            "Fixed PPE moments differ",
        )
        parameter_evidence = materialized[name + "/parameters.json"]
        require(
            _same(parameter_evidence["parameters"], list(PARAMETERS))
            and parameter_evidence["role"] == "parameters",
            "PPE evidence must remain target-free fixed parameters",
        )
        projections = materialized[name + "/projection.json"]
        require(
            [r["core"] for r in projections] == list(CORES),
            "Four ordered projection owners required",
        )
        raw_sources = {}
        geometries = {}
        for core, projection in zip(CORES, projections, strict=True):
            owner = ids[core]
            raw = materialized[f"{name}/{core}-raw.json"]
            counts = _counts(raw, core, name)
            _projection(projection, counts, core, name)
            owners.append(CountOwner(owner_id=owner, counts=counts))
            raw_sources[owner] = raw
            geometry = materialized[f"{name}/{core}-geometry.json"]
            geometries[owner] = geometry
            require(
                _same(
                    geometry["sample_metadata"],
                    {k: v for k, v in raw["sample"].items() if k != "counts"},
                ),
                "Geometry contains foreign sample metadata",
            )
            require(
                "counts" not in geometry["sample_metadata"],
                "Target geometry must be count-free",
            )
            declaration = (
                coupled["krag_geometry"]
                if core == "KRAGMJNY"
                else next(r for r in coupled["small_cores"] if r["id"] == core)
            )
            _geometry(geometry, declaration, regional=core == "KRAGMJNY")
            lineage[owner] = {
                "core": core,
                "raw": {
                    **member_pins[f"{name}/{core}-raw.json"],
                    "path": (directory / f"{core}-raw.json")
                    .relative_to(reader.repository)
                    .as_posix(),
                },
                "projection": projection,
                "panel_N": sum(counts),
            }
        local_fold_rows = bin_row["folds"]
        require(
            len(local_fold_rows) == 3
            and {r["test_record_ids"][0] for r in local_fold_rows}
            == {ids[c] for c in SMALL},
            "Three exact small-place heldout folds required",
        )
        descriptor = bin_row["prediction"]
        prediction_directory = reader.path(descriptor["directory"])
        require(
            prediction_directory == predictions_root / name
            and descriptor["interrupted"] is False,
            "Saved prediction directory/state differs",
        )
        manifest = reader.read(
            {
                "path": str(prediction_directory / "manifest.json"),
                "sha256": descriptor["manifest_sha256"],
            }
        )
        require(
            manifest["scientific_content_sha256"]
            == descriptor["scientific_content_sha256"],
            "Prediction content identity differs",
        )
        tables = {}
        for filename in ["preparations.json", "operations.json", "predictions.json"]:
            require(
                descriptor["retained_tables"][filename] == manifest["files"][filename],
                "Prediction table identity differs",
            )
            tables[filename] = reader.member(
                prediction_directory, manifest["files"], filename
            )
        preparation_rows = {r["fold_id"]: r for r in tables["preparations.json"]}
        operation_rows = {r["fold_id"]: r for r in tables["operations.json"]}
        predicted_rows = tables["predictions.json"]
        require(
            len(predicted_rows) == (9 if name == NAMES[0] else 0),
            "Nominal predictions differ from pre-score population",
        )
        for fold in local_fold_rows:
            fold_id = fold["fold_id"]
            target = fold["test_record_ids"][0]
            case_id = name + ":" + fold_id
            allowed = {ids[c] for c in CORES} - {target}
            locals_ = sorted(allowed - {regional})
            require(
                fold["test_record_ids"] == [target]
                and set(fold["train_record_ids"]) == allowed
                and len(fold["train_record_ids"]) == 3
                and fold["test_group_ids"] == [fold_id]
                and len(set(fold["train_group_ids"])) == 3
                and fold_id not in fold["train_group_ids"],
                "Heldout physical owner entered training",
            )
            dispositions = [
                r
                for r in all_dispositions
                if r["bin"] == name and r["fold_id"] == fold_id
            ]
            require(
                [r["method"] for r in dispositions] == list(METHODS),
                "All three nominal methods required",
            )
            expected_status = "predicted" if name == NAMES[0] else "refused"
            require(
                all(r["status"] == expected_status for r in dispositions),
                "Nominal eligibility cannot change",
            )
            expected_keys.extend((name, fold_id, method) for method in METHODS)
            scientific_refs = [lineage[owner]["raw"] for owner in [regional, *locals_]]
            target_core = next(c for c in SMALL if ids[c] == target)
            geometry_member = f"{name}/{target_core}-geometry.json"
            folds.append(
                {
                    "case_id": case_id,
                    "bin": name,
                    "fold_id": fold_id,
                    "target_id": target,
                    "regional_owner_id": regional,
                    "local_owner_ids": locals_,
                    "nominal_status": expected_status,
                    "nominal_refusal": None
                    if expected_status == "predicted"
                    else [
                        {
                            k: v
                            for k, v in r.items()
                            if k not in ["bin", "fold_id", "method"]
                        }
                        for r in dispositions
                    ],
                    "scientific_count_refs": scientific_refs,
                    "target_geometry_ref": {
                        **member_pins[geometry_member],
                        "path": (inputs_root / geometry_member)
                        .relative_to(reader.repository)
                        .as_posix(),
                    },
                    "parameter_ref": {
                        **member_pins[name + "/parameters.json"],
                        "path": (directory / "parameters.json")
                        .relative_to(reader.repository)
                        .as_posix(),
                    },
                    "kernel_refs": [],
                }
            )
            if expected_status != "predicted":
                continue
            prep = preparation_rows[fold_id]
            require(prep["outer_fold"] == fold, "Saved forward fold differs")
            target_geometry = geometries[target]
            target_core = next(c for c in SMALL if ids[c] == target)
            require(
                prep["target_geometry_sha256"]
                == member_pins[f"{name}/{target_core}-geometry.json"]["sha256"]
                and _same(
                    prep["declared_target_forward_rings"],
                    target_geometry["forward_rings"],
                )
                and _same(
                    prep["declared_target_inversion_rings"],
                    target_geometry["inversion_rings"],
                ),
                "Saved target geometry binding differs",
            )
            require(
                prep["ring_bounds_m"]
                == [
                    [r["inner_m"], r["outer_m"]]
                    for r in target_geometry["forward_rings"]
                ],
                "Forward ring bounds differ",
            )
            require(
                prep["regional_value_source_record_ids"] == [regional]
                and set(prep["regional_identity_source_record_ids"]) == allowed,
                "Saved regional source roles differ",
            )
            items = operation_rows[fold_id]["batch"]["items"]
            require(
                len(items) == 2 and {r["item_id"] for r in items} == set(locals_),
                "Both saved local training products required",
            )
            kernels = []
            regional_coefficients = []
            for owner in locals_:
                item = next(r for r in items if r["item_id"] == owner)
                kernel, deposition = _native_kernel(
                    reader, item, owner, regional, raw_sources, geometries
                )
                kernels.append(kernel)
                regional_coefficients.append(deposition)
                for filename in [
                    "numerical/local_love/aux_Kloc.csv",
                    "numerical/local_love/aux_Kreg.csv",
                    "numerical/regional_reveals/deposition_factors.csv",
                ]:
                    path = (
                        (reader.path(item["product"]["directory"]) / filename)
                        .relative_to(reader.repository)
                        .as_posix()
                    )
                    folds[-1]["kernel_refs"].append(
                        {"local_owner_id": owner, **reader.refs[path]}
                    )
            require(
                regional_coefficients[0] == regional_coefficients[1],
                "Shared KRAG coefficient differs across local requests",
            )
            full = prep["full_k"]
            fractions = prep["full_terrestrial_fraction"]
            require(
                len(full) == len(fractions) == 4
                and prep["forward_inputs"]["local_k"] == full[:2]
                and prep["forward_inputs"]["terrestrial_fraction"] == fractions[:2]
                and prep["forward_inputs"]["ppe"] == [5.106, 1.27],
                "Saved target forward ring grid differs",
            )
            full_pairs = [_pair(row) for row in full]
            fractions = tuple(_number(x) for x in fractions)
            require(
                fractions == (1.0, 1.0, 1.0, 1.0), "Frozen terrestrial fractions differ"
            )
            forward_regional = tuple(
                sum(full_pairs[i][j] * fractions[i] for i in [2, 3]) for j in [0, 1]
            )
            rows_for_fold = [r for r in predicted_rows if r["fold_id"] == fold_id]
            require(
                [r["baseline"] for r in rows_for_fold] == list(METHODS),
                "Complete closed nominal methods required",
            )
            for row in rows_for_fold:
                require(
                    row["record_id"] == target and row["bin_id"] == name,
                    "Nominal target owner differs",
                )
                pm = row["prediction_manifest"]
                require(
                    hashlib.sha256(_canonical(pm)).hexdigest()
                    == row["prediction_manifest_sha256"]
                    and pm["fold"] == fold
                    and pm["forward_inputs"] == prep["forward_inputs"],
                    "Closed prediction manifest differs",
                )
                closure = pm["allowed_input_closure"]
                require(
                    target not in closure
                    and {x for x in closure if x.startswith("neotoma-")} == allowed,
                    "Target count leaks into saved scientific closure",
                )
                require(
                    set(pm["input_lineage"]) <= set(closure)
                    and all(
                        set(children) <= set(closure)
                        for children in pm["input_lineage"].values()
                    ),
                    "Foreign count ancestry in saved prediction",
                )
                nominal.append(
                    {
                        "case_id": case_id,
                        "method": row["baseline"],
                        "pollen_fraction": _pair(
                            [row["pollen_fraction"][t] for t in AXIS]
                        ),
                        "vegetation_fraction": _pair(
                            [row["vegetation_fraction"][t] for t in AXIS]
                        ),
                        "regional_cover": _pair(prep["regional_cover"]),
                        "prediction_manifest_sha256": row["prediction_manifest_sha256"],
                    }
                )
            training = reader.member(
                prediction_directory, manifest["files"], "training.json"
            )
            training_fold = next(r for r in training if r["fold_id"] == fold_id)
            group_by_owner = {
                r["record_id"]: r["group_id"]
                for r in training_fold["training_products"]
            }
            require(
                set(group_by_owner) == set(locals_)
                and set(prep["distances_km"]) == set(group_by_owner.values()),
                "Saved local owner/distance mapping differs",
            )
            distances = tuple(
                _number(prep["distances_km"][group_by_owner[owner]], positive=True)
                for owner in locals_
            )
            cases.append(
                FoldCase(
                    case_id=case_id,
                    target_id=target,
                    regional_owner_id=regional,
                    local_owners=(kernels[0], kernels[1]),
                    regional_deposition=regional_coefficients[0],
                    forward_local_k=tuple(full_pairs[:2]),
                    forward_regional_k=(forward_regional[0], forward_regional[1]),
                    terrestrial_fraction=fractions[:2],
                    distances_km=(distances[0], distances[1]),
                    selected_ring_index=1,
                )
            )
    require(
        disposition_keys == expected_keys
        and len(owners) == 24
        and len(cases) == 3
        and len(folds) == 18
        and len(nominal) == 9,
        "Complete frozen population required",
    )
    require(
        len({o.owner_id for o in owners}) == 24
        and len({f["case_id"] for f in folds}) == 18,
        "Duplicate source owner or fold",
    )
    active = {case.regional_owner_id for case in cases} | {
        local.owner_id for case in cases for local in case.local_owners
    }
    require(
        len(active) == 4 and all(owner.endswith(NAMES[0]) for owner in active),
        "Only four active owner/windows may be drawn",
    )
    return InputPacket(
        tuple(owners),
        tuple(cases),
        tuple(folds),
        tuple(all_dispositions),
        tuple(nominal),
        {
            "source_population": index["source_population"],
            "owner_lineage": lineage,
            "active_draw_owner_ids": sorted(active),
            "sampling": sampling,
            "all_source_fingerprints_role": "accounting_only_not_fold_scientific_ancestry",
        },
        tuple(reader.refs[k] for k in sorted(reader.refs)),
    )


def load_inputs(repository: Path, protocol: dict[str, Any]) -> InputPacket:
    """Refuse malformed/missing saved bindings without native execution."""
    try:
        return _load_inputs(repository, protocol)
    except InputError:
        raise
    except (
        KeyError,
        TypeError,
        IndexError,
        StopIteration,
        OSError,
        ValueError,
    ) as error:
        raise InputError(f"Malformed saved predictive input: {error}") from error
