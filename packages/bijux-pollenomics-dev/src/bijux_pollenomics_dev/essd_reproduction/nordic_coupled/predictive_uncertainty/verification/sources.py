"""Independent joins to immutable materialized sources and pre-score products."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any

from .algebra import compare, finite, require

AXIS = ("Betula", "Ulmus")


class _Sources:
    def __init__(self, repository: Path) -> None:
        self.root = repository.resolve(strict=True)
        self.refs: dict[str, dict[str, Any]] = {}
        self.raw: dict[str, bytes] = {}
        self.total = 0

    def path(self, locator: str, base: Path | None = None) -> Path:
        require(isinstance(locator, str) and bool(locator), "source locator")
        relative = Path(locator)
        require(".." not in relative.parts, "source parent traversal")
        path = relative if relative.is_absolute() else (base or self.root) / relative
        require(path.is_relative_to(self.root), "source outside repository")
        require(
            not any(part.is_symlink() for part in (path, *path.parents)),
            "source symlink",
        )
        return path

    def read(
        self, pin: dict[str, Any], base: Path | None = None, *, decode: bool = True
    ) -> Any:
        path = self.path(pin["path"], base)
        key = path.relative_to(self.root).as_posix()
        require(
            isinstance(pin["sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
            "source SHA256",
        )
        if key not in self.raw:
            before = path.stat()
            require(
                path.is_file() and before.st_size <= 4 * 1024 * 1024,
                "bounded source file",
            )
            raw = path.read_bytes()
            after = path.stat()
            require(
                all(
                    getattr(before, field) == getattr(after, field)
                    for field in (
                        "st_dev",
                        "st_ino",
                        "st_size",
                        "st_mtime_ns",
                        "st_ctime_ns",
                    )
                )
                and len(raw) == before.st_size,
                "source changed during read",
            )
            self.total += len(raw)
            require(self.total <= 64 * 1024 * 1024, "source read ceiling")
            self.raw[key] = raw
            self.refs[key] = {
                "path": key,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        require(self.refs[key]["sha256"] == pin["sha256"], "source digest mismatch")
        if "bytes" in pin:
            require(
                type(pin["bytes"]) is int and pin["bytes"] == len(self.raw[key]),
                "source byte size",
            )
        if not decode:
            return self.raw[key]

        def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for name, item in pairs:
                require(name not in value, "duplicate source JSON field")
                value[name] = item
            return value

        def invalid(value: str) -> Any:
            raise ValueError("Nonfinite source JSON: " + value)

        return json.loads(
            self.raw[key], object_pairs_hook=unique, parse_constant=invalid
        )

    def member(
        self,
        base: Path,
        manifest: dict[str, Any],
        filename: str,
        *,
        decode: bool = True,
    ) -> Any:
        return self.read(
            {"path": filename, "sha256": manifest["files"][filename]},
            base,
            decode=decode,
        )

    def actual_pin(self, path: Path) -> dict[str, Any]:
        return self.refs[path.relative_to(self.root).as_posix()]


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode()


def _matrix(raw: bytes, rings: list[dict[str, Any]]) -> list[list[float]]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    require(reader.fieldnames == ["index", *AXIS], "kernel CSV axis")
    rows = list(reader)
    require(len(rows) == len(rings) == 2, "two source inversion rings")
    result = []
    for row, ring in zip(rows, rings, strict=True):
        require(
            finite(float(row["index"])) == finite(ring["mean_m"]),
            "source kernel ring order",
        )
        values = [finite(float(row[taxon])) for taxon in AXIS]
        require(min(values) > 0, "positive source inversion kernels")
        result.append(values)
    return result


def _regional(raw: bytes) -> list[float]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    require(reader.fieldnames == ["index", "K"], "regional kernel CSV axis")
    rows = list(reader)
    require([row["index"] for row in rows] == list(AXIS), "regional kernel taxon order")
    result = [finite(float(row["K"])) for row in rows]
    require(min(result) > 0, "positive source regional kernels")
    return result


def bind_sources(repository: Path, input_packet: dict[str, Any]) -> dict[str, Any]:
    """Certify the observed reader against its closed authorities, without that reader."""
    reader = _Sources(repository)
    declared = input_packet["protocol"]["sources"]
    require(
        set(declared) == {"coupled_protocol", "input_index", "prediction_batch"},
        "three source authorities",
    )
    coupled = reader.read(declared["coupled_protocol"])
    index, batch = (
        reader.read(declared["input_index"]),
        reader.read(declared["prediction_batch"]),
    )
    for pin, authority in (
        (index["protocol"], "coupled_protocol"),
        (batch["protocol"], "coupled_protocol"),
        (batch["input_index"], "input_index"),
    ):
        require(
            reader.path(pin["path"]) == reader.path(declared[authority]["path"])
            and pin["sha256"] == declared[authority]["sha256"],
            "authority locator/identity disagreement",
        )
    require(
        batch["operation"] == "prepare" and batch["all_bins_accounted"] is True,
        "closed pre-score authority",
    )
    compare(input_packet["dispositions"], batch["method_dispositions"], tolerance=0)
    compare(coupled["axis"], list(AXIS))
    inputs_root = reader.path(declared["input_index"]["path"]).parent
    pins = {row["path"]: row for row in index["members"]}
    require(
        len(pins) == len(index["members"]) == 90,
        "90 unique original materialization members",
    )
    materialized = {name: reader.read(pin, inputs_root) for name, pin in pins.items()}
    for pin in [*index["qualified_source_inputs"], index["krag_audit"]]:
        reader.read(pin, decode=False)
    counts, lineage = {}, input_packet["accounting"]["owner_lineage"]
    owners = {row["owner_id"]: row for row in input_packet["owners"]}
    require(len(owners) == len(lineage) == 24, "24 original count owners")
    for owner_id, proof in lineage.items():
        raw_path = reader.path(proof["raw"]["path"])
        name = raw_path.relative_to(inputs_root).as_posix()
        require(
            name in pins and name.endswith("-raw.json"), "owner raw member authority"
        )
        require(
            raw_path.name == proof["core"] + "-raw.json", "source core/projection owner"
        )
        compare(proof["raw"], reader.actual_pin(raw_path), tolerance=0)
        raw = materialized[name]
        require(
            raw["data_kind"] == "source_observations"
            and raw["taxa"] == list(AXIS)
            and raw["sample"]["sample_id"] == owner_id,
            "raw owner/axis",
        )
        values = raw["sample"]["counts"]
        require(
            type(values) is list
            and len(values) == 2
            and all(type(value) is int and value >= 0 for value in values)
            and sum(values) > 0,
            "literal source count pair",
        )
        compare(owners[owner_id]["counts"], values, tolerance=0)
        require(
            type(proof["panel_N"]) is int and proof["panel_N"] == sum(values),
            "source panel N",
        )
        projections = materialized[str(Path(name).parent / "projection.json")]
        matches = [row for row in projections if row["core"] == proof["core"]]
        require(len(matches) == 1, "unique source projection owner")
        compare(proof["projection"], matches[0], tolerance=0)
        counts[owner_id] = values
    folds = {row["case_id"]: row for row in input_packet["folds"]}
    cases = {row["case_id"]: row for row in input_packet["cases"]}
    nominal = []
    bound_cases = set()
    for bin_row in batch["bins"]:
        descriptor = bin_row["prediction"]
        require(descriptor["interrupted"] is False, "closed prediction product")
        directory = reader.path(descriptor["directory"])
        manifest = reader.read(
            {
                "path": str(directory / "manifest.json"),
                "sha256": descriptor["manifest_sha256"],
            }
        )
        require(
            manifest["scientific_content_sha256"]
            == descriptor["scientific_content_sha256"],
            "prediction content identity",
        )
        tables = {
            filename: reader.member(directory, manifest, filename)
            for filename in ("preparations.json", "operations.json", "predictions.json")
        }
        for filename in tables:
            require(
                descriptor["retained_tables"][filename] == manifest["files"][filename],
                "pre-score table identity",
            )
        for original_fold in bin_row["folds"]:
            case_id = bin_row["bin"] + ":" + original_fold["fold_id"]
            fold = folds[case_id]
            require(
                fold["fold_id"] == original_fold["fold_id"]
                and original_fold["test_record_ids"] == [fold["target_id"]]
                and set(original_fold["train_record_ids"])
                == {fold["regional_owner_id"], *fold["local_owner_ids"]},
                "original heldout source partition",
            )
            core = lineage[fold["target_id"]]["core"]
            for key, filename in (
                ("target_geometry_ref", core + "-geometry.json"),
                ("parameter_ref", "parameters.json"),
            ):
                member = f"{bin_row['bin']}/{filename}"
                compare(fold[key], reader.actual_pin(inputs_root / member), tolerance=0)
            if case_id not in cases:
                require(
                    fold["kernel_refs"] == [], "no kernels for nominally refused fold"
                )
                continue
            bound_cases.add(case_id)
            case = cases[case_id]
            preparation = next(
                row
                for row in tables["preparations.json"]
                if row["fold_id"] == fold["fold_id"]
            )
            compare(preparation["outer_fold"], original_fold, tolerance=0)
            full, fractions = (
                preparation["full_k"],
                preparation["full_terrestrial_fraction"],
            )
            require(len(full) == len(fractions) == 4, "four saved forward rings")
            compare(case["forward_local_k"], full[:2], tolerance=0)
            compare(case["terrestrial_fraction"], fractions[:2], tolerance=0)
            compare(
                case["forward_regional_k"],
                [
                    sum(
                        finite(full[ring][taxon]) * finite(fractions[ring])
                        for ring in (2, 3)
                    )
                    for taxon in range(2)
                ],
                tolerance=0,
            )
            training = reader.member(directory, manifest, "training.json")
            mapping = {
                row["record_id"]: row["group_id"]
                for row in next(
                    row for row in training if row["fold_id"] == fold["fold_id"]
                )["training_products"]
            }
            local_ids = [row["owner_id"] for row in case["local_owners"]]
            require(set(mapping) == set(local_ids), "saved local predictor mapping")
            compare(
                case["distances_km"],
                [preparation["distances_km"][mapping[owner]] for owner in local_ids],
                tolerance=0,
            )
            operation = next(
                row
                for row in tables["operations.json"]
                if row["fold_id"] == fold["fold_id"]
            )
            items = operation["batch"]["items"]
            require(
                len(items) == 2 and {row["item_id"] for row in items} == set(local_ids),
                "two permitted native owners",
            )
            kernel_refs = []
            for local in case["local_owners"]:
                item = next(row for row in items if row["item_id"] == local["owner_id"])
                require(item["item_status"] == "completed", "closed native item")
                native_dir = reader.path(item["product"]["directory"])
                native = reader.read(
                    {
                        "path": str(native_dir / "manifest.json"),
                        "sha256": item["product"]["manifest_sha256"],
                    }
                )
                require(
                    native["schema_version"] == "lra-product.v1"
                    and native["scientific_content_sha256"]
                    == item["product"]["scientific_content_sha256"]
                    and native["retained_taxa"] == list(AXIS),
                    "native product source identity",
                )
                request = reader.member(native_dir, native, "request.json")
                require(
                    hashlib.sha256(_canonical(request)).hexdigest()
                    == item["request_sha256"]
                    == native["request_sha256"],
                    "native request identity",
                )
                require(
                    request["taxa"] == list(AXIS)
                    and request["parameters"] == coupled["parameters"],
                    "native parameter/axis source",
                )
                for role, owner_id in (
                    ("local", local["owner_id"]),
                    ("regional", case["regional_owner_id"]),
                ):
                    sample = request[role]["samples"]
                    require(
                        len(sample) == 1 and sample[0]["sample_id"] == owner_id,
                        "native request owner",
                    )
                    compare(sample[0]["counts"], counts[owner_id], tolerance=0)
                for filename, field in (
                    ("numerical/local_love/aux_Kloc.csv", "local_k"),
                    ("numerical/local_love/aux_Kreg.csv", "regional_k"),
                    (
                        "numerical/regional_reveals/deposition_factors.csv",
                        "regional_deposition",
                    ),
                ):
                    raw = reader.member(native_dir, native, filename, decode=False)
                    expected = (
                        _regional(raw)
                        if field == "regional_deposition"
                        else _matrix(raw, request["rings"])
                    )
                    compare(
                        case[field] if field == "regional_deposition" else local[field],
                        expected,
                        tolerance=0,
                    )
                    kernel_refs.append(
                        {
                            "local_owner_id": local["owner_id"],
                            **reader.actual_pin(native_dir / filename),
                        }
                    )
            compare(fold["kernel_refs"], kernel_refs, tolerance=0)
            for row in tables["predictions.json"]:
                if row["fold_id"] == fold["fold_id"]:
                    require(
                        row["record_id"] == case["target_id"]
                        and row["bin_id"] == bin_row["bin"]
                        and hashlib.sha256(
                            _canonical(row["prediction_manifest"])
                        ).hexdigest()
                        == row["prediction_manifest_sha256"],
                        "nominal source target/identity",
                    )
                    nominal.append(
                        {
                            "case_id": case_id,
                            "method": row["baseline"],
                            "pollen_fraction": [
                                row["pollen_fraction"][taxon] for taxon in AXIS
                            ],
                            "vegetation_fraction": [
                                row["vegetation_fraction"][taxon] for taxon in AXIS
                            ],
                            "regional_cover": preparation["regional_cover"],
                            "prediction_manifest_sha256": row[
                                "prediction_manifest_sha256"
                            ],
                        }
                    )
    require(
        bound_cases == set(cases) and len(bound_cases) == 3 and len(nominal) == 9,
        "complete source-bound active population",
    )
    compare(input_packet["nominal_predictions"], nominal, tolerance=0)
    declarations = input_packet["source_files"]
    require(
        len(declarations) == len({row["path"] for row in declarations}),
        "unique source accounting inventory",
    )
    require(
        {row["path"] for row in declarations} == set(reader.refs),
        "complete discovered source closure",
    )
    for pin in declarations:
        require(
            not Path(pin["path"]).is_absolute() and pin["path"] in reader.refs,
            "source outside discovered authority closure",
        )
        compare(pin, reader.refs[pin["path"]], tolerance=0)
    return {
        "status": "passed",
        "source_files_verified": len(declarations),
        "owners_verified": 24,
        "active_fold_kernels_verified": len(bound_cases),
        "nominal_predictions_verified": len(nominal),
        "source_bytes_read": reader.total,
        "scope": "Qualified saved inputs and pre-score products; no new native-source census or model execution",
    }
