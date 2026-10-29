"""Confine a fresh outcome-blind EMPD2–NFI source refusal replay."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
PRIVATE = Path("/Users/bijan/bijux/-bijux-pollenomics-data")
OWNER = "validation/empd2-nfi-pairing/report-products"
PRODUCER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/empd2_nfi_pairing.py"
REPORT = "docs/report/validation/empd2-nfi-pairing"
POLICY = "configs/ci/report-ownership.json"
MODULES = {
    "contracts.py",
    "metadata.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
INPUTS = {
    "sqlite": (
        PRIVATE / "reference-sources/empd2-nfi/empd2/source.sqlite3",
        "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2",
        21327872,
    ),
    "workbook": (
        PRIVATE / "reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx",
        "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294",
        14381338,
    ),
    "dossier": (
        PRIVATE / "reference-sources/empd2-nfi/pairing/source-provenance.json",
        "bcab3834980f6934143f3a2bf4e2a0155bf3c7024850989de4f0f28f89584c31",
        28945,
    ),
    "spatial": (
        PRIVATE / "reference-sources/empd2-nfi/pairing/spatial-feasibility.json",
        "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
        81363,
    ),
    "guide": (
        ROOT / REPORT / "inputs/slu-calibration-guide.pdf",
        "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8",
        136339,
    ),
}
PACKAGE_ROOTS = [
    ROOT / "packages" / name / "src"
    for name in (
        "bijux-pollenomics",
        "bijux-pollenomics-dev",
        "bijux-pollenomics-lra",
        "pollenomics",
    )
]
LOCATION_FIELDS = frozenset(
    {
        "nfi_tract",
        "nfi_plot",
        "nfi_year",
        "nfi_inventory_date_source_native",
        "nfi_easting_sweref99tm",
        "nfi_northing_sweref99tm",
        "nfi_longitude_wgs84",
        "nfi_latitude_wgs84",
    }
)
FIELDS = (
    "candidate_id",
    "empd2_sample",
    "empd2_source_sha256",
    "empd2_source_agebp",
    "empd2_source_age_code",
    "empd2_collection_time_status",
    "empd2_longitude_wgs84",
    "empd2_latitude_wgs84",
    "nfi_tract",
    "nfi_plot",
    "nfi_year",
    "nfi_inventory_date_source_native",
    "nfi_easting_sweref99tm",
    "nfi_northing_sweref99tm",
    "nfi_longitude_wgs84",
    "nfi_latitude_wgs84",
    "nfi_source_sha256",
    "distance_m_wgs84",
    "coordinate_comparability",
    "time_comparability",
    "measurement_comparability",
    "footprint_comparability",
    "source_identity_status",
    "missing_or_unreviewed_fields",
    "current_benchmark_decision",
    "scientific_admission",
)
PUBLIC_FIELDS = (
    "candidate_id",
    "nfi_row_identity_sha256",
    *(x for x in FIELDS if x not in LOCATION_FIELDS and x != "candidate_id"),
)
GAPS = (
    "authenticated_pollen_collection_date",
    "nfi_tree_measurement_values_and_units",
    "nfi_plot_effective_area_and_vegetation_denominator",
    "pollen_taxon_count_denominator_and_tree_taxon_crosswalk",
    "pollen_basin_or_local_vegetation_footprint",
    "plot_to_reconstruction_support_rule",
    "independent_source_and_leakage_review",
    "reviewed_nonnull_benchmark_minimum_and_thresholds",
)


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file() and (not path.is_symlink()),
        "Physical regular input required: " + str(path),
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            (exact(x, y) for x, y in zip(a, b, strict=True))
        )
    return bool(a == b)


def load(path: Path) -> Any:

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(rows) == len({k for k, _ in rows}), "Duplicate JSON key")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant
    )


def dump(path: Path, value: Any) -> None:
    require(
        not path.exists() and (not path.is_symlink()),
        "No receipt replacement: " + str(path),
    )
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def output_root(path: Path, *, absent: bool = False) -> Path:
    require(
        path.is_absolute()
        and path == path.resolve()
        and path.is_relative_to(ROOT / "artifacts")
        and (not any(p.is_symlink() for p in (path, *path.parents))),
        "Physical normalized artifact output required",
    )
    if absent:
        require(not path.exists() and (not path.is_symlink()), "Absent output required")
    return path


def namespace() -> None:
    for p in SOURCE.iterdir():
        require(
            not p.is_symlink() and (p.is_dir() or p.is_file()),
            "Alias/special controller entry",
        )
        require(
            not p.is_dir() or p.name == "preflight", "Unexpected controller directory"
        )
        if p.suffix in {".py", ".pyc", ".so"}:
            require(p.name in MODULES, "Unexpected importable controller")


def identity() -> dict[str, str]:

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def union(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for group in groups:
        for row in group:
            require(
                set(row) == {"path", "sha256", "bytes"} and type(row["bytes"]) is int,
                "Malformed expected pin",
            )
            name = row["path"]
            require(
                name not in rows or exact(rows[name], row),
                "Conflicting original input pin: " + name,
            )
            rows[name] = dict(row)
    return [rows[k] for k in sorted(rows)]


def first_party_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from runtime_contracts import namespace_snapshot

    trees = []
    files: list[dict[str, Any]] = []
    for root in PACKAGE_ROOTS:
        tree = namespace_snapshot(root, [])
        require(
            all(v["kind"] != "symlink" for v in tree["entries"].values()),
            "First-party source alias is not declared",
        )
        trees.append(tree)
        files.extend(
            (
                pin(root / name)
                for name, v in tree["entries"].items()
                if v["kind"] == "file"
            )
        )
    return (trees, files)


def verify_inputs(plan: dict[str, Any]) -> None:
    from runtime_contracts import verify_absences, verify_base_namespaces, verify_pin

    namespace()
    for row in plan["input_pins"]:
        verify_pin(row)
    verify_base_namespaces(plan["first_party_namespaces"])
    verify_absences(plan["absent_input_paths"])


def csv_wire(rows: list[dict[str, object]], fields: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def read_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == list(fields), "CSV field order changed")
        result = list(reader)
    require(
        all(set(x) == set(fields) and None not in x.values() for x in result),
        "Ragged CSV",
    )
    return result


def public_projection(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    public = []
    for row in rows:
        identity_value = {
            "nfi_source_sha256": INPUTS["workbook"][1],
            "row": [row[k] for k in sorted(LOCATION_FIELDS)],
        }
        token = hashlib.sha256(
            json.dumps(identity_value, separators=(",", ":")).encode()
        ).hexdigest()
        item = {
            k: row[k]
            for k in PUBLIC_FIELDS
            if k not in {"candidate_id", "nfi_row_identity_sha256"}
        }
        item.update(
            candidate_id=f"empd2-nfi:{row['empd2_sample']}:{token[:16]}",
            nfi_row_identity_sha256=token,
        )
        require(LOCATION_FIELDS.isdisjoint(item), "Private plot key leaked")
        public.append(item)
    require(
        len(public) == len({x["candidate_id"] for x in public}),
        "Public identity collision",
    )
    return public


def finite(value: object) -> float:
    require(type(value) in (int, float), "Actual numeric value required")
    assert isinstance(value, (int, float))
    result = float(value)
    require(math.isfinite(result), "Finite value required")
    return result
