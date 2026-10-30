"""Authenticate retained panel/window sources without inventing observations."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import stat
from typing import Any, cast

PROTOCOL = (
    "docs/report/pollen-reconstruction/matched-pollen-forward/assumptions/protocol.json"
)
PROTOCOL_SHA256 = "22355c28b91af19e23240ce8060761fc0f1f45d6be212d04f5432127eb2e7249"
Window = tuple[float, float]


@dataclass(frozen=True)
class Cell:
    window: Window
    counts: tuple[int, ...]
    source_support_sha256: str


@dataclass(frozen=True)
class Core:
    id: str
    country: str
    site: int
    dataset: int
    collection_unit: int
    axis: tuple[str, ...]
    ppe: tuple[float, ...]
    sd: tuple[float, ...]
    kernels: tuple[float, ...]
    cells: tuple[Cell, ...]


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def physical(path: Path) -> None:
    require(
        path.is_absolute() and ".." not in path.parts, "Absolute lexical path required"
    )
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "Source/output alias refused",
    )


def buffer(path: Path, checksum: str, size: int) -> bytes:
    physical(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= 4194304,
            "Bounded single-link regular source required",
        )
        raw = stream.read(4194305)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    require(
        all(
            getattr(before, k) == getattr(after, k) == getattr(final, k)
            for k in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ),
        "Source changed during read",
    )
    require(
        len(raw) == size and digest(raw) == checksum,
        "Exact input buffer identity differs",
    )
    return raw


def decode(raw: bytes) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            require(key not in out, "Duplicate JSON key")
            out[key] = value
        return out

    def refuse(value: str) -> Any:
        raise ValueError("Nonfinite JSON token: " + value)

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=refuse)
    require(isinstance(result, dict), "Source JSON must be an object")
    return cast(dict[str, Any], result)


def numbers(values: Any, length: int, *, positive: bool) -> tuple[float, ...]:
    require(
        type(values) is list and len(values) == length, "Numerical source axis differs"
    )
    require(
        all(
            type(v) in (int, float)
            and math.isfinite(v)
            and (v > 0 if positive else v >= 0)
            for v in values
        ),
        "Finite source parameter required",
    )
    return tuple(float(v) for v in values)


def window(row: dict[str, Any]) -> Window:
    bounds = numbers(
        [row["younger_cal_bp"], row["older_cal_bp_exclusive"]], 2, positive=False
    )
    require(bounds[1] > bounds[0], "Strict ordered calendar-BP window required")
    return bounds[0], bounds[1]


def normalize(
    swedish: dict[str, Any], nordic: dict[str, Any], protocol: dict[str, Any]
) -> tuple[Core, ...]:
    """Interpret the two actual saved schemas and exact frozen populations."""
    require(
        protocol["schema_version"] == "matched-pollen-forward.protocol.v1",
        "Matched protocol schema differs",
    )
    require(
        swedish["schema_version"] == "swedish-static-basin-maintained-producer.v1",
        "Swedish source schema differs",
    )
    require(
        swedish["producer_candidate"] == protocol["source_epochs"]["swedish"]
        and nordic["candidate"] == protocol["source_epochs"]["nordic"],
        "Original saved source epochs differ",
    )
    require(
        len(swedish["cores"]) == 4 and len(nordic["cases"]) == 9,
        "Original source core/geometry membership differs",
    )
    actual = {core["metadata_code"]: core for core in swedish["cores"]}
    require(len(actual) == 4, "Duplicate Swedish core")
    for core in nordic["cases"]:
        if core["static_geometry"]["id"] == "metadata_static_radius":
            require(
                core["source_handle"] not in actual, "Duplicate Nordic baseline core"
            )
            actual[core["source_handle"]] = core
    require(
        set(actual) == {c["id"] for c in protocol["source_cores"]} and len(actual) == 8,
        "Complete8core baseline population required",
    )
    output = []
    for expected in protocol["source_cores"]:
        row = actual[expected["id"]]
        is_swedish = expected["country"] == "SE"
        require(
            all(
                type(row[k]) is int and row[k] == expected[k]
                for k in (
                    "native_site_id",
                    "native_dataset_id",
                    "native_collection_unit_id",
                )
            ),
            "Native physical core/place identity differs",
        )
        axis = row["parameter_taxa"]
        require(
            axis == expected["axis"] and len(axis) == len(set(axis)),
            "Literal source panel differs",
        )
        size = len(axis)
        ppe = numbers(row["ppe" if is_swedish else "PPE"], size, positive=True)
        sd = numbers(
            row["ppe_standard_deviation" if is_swedish else "PPE_SD"],
            size,
            positive=False,
        )
        if is_swedish:
            kernels = [
                x for x in row["quadrature"] if x["profile"] == "metadata_radius_wind_3"
            ]
            require(len(kernels) == 1, "Exactly one Swedish baseline kernel required")
            factors = kernels[0]["factors"]
            results = [
                x for x in row["results"] if x["profile"] == "metadata_radius_wind_3"
            ]
        else:
            require(
                row["case_id"] == expected["source_profile"],
                "Nordic geometry case differs",
            )
            factors, results = row["physical_response"]["factors"], row["results"]
        require(
            type(factors) is list and len(factors) == 1, "Saved kernel row axis differs"
        )
        factors_flat = numbers(factors[0], size, positive=True)
        require(all(k <= 1 for k in factors_flat), "Receiver probabilities exceed one")
        cells = []
        for result in results:
            values = result["counts"]
            require(
                type(values) is list
                and len(values) == 1
                and type(values[0]) is list
                and len(values[0]) == size,
                "Explicit source count axis differs",
            )
            counts = values[0]
            require(
                all(type(n) is int and 0 <= n < 2**53 for n in counts)
                and 0 < sum(counts) < 2**53
                and type(result["panel_count_denominator"]) is int
                and sum(counts) == result["panel_count_denominator"],
                "Exact reported panel counts required",
            )
            if not is_swedish:
                require(
                    result["actual_source_panel_presence"] is True
                    and result["assumed_zero_cells"] == 0,
                    "Unmeasured source taxon cannot become zero",
                )
            support = result[
                "local_native_sample_support_sha256"
                if is_swedish
                else "local_actual_source_support_sha256"
            ]
            require(
                type(support) is str
                and len(support) == 64
                and all(c in "0123456789abcdef" for c in support),
                "Source window support hash differs",
            )
            cells.append(Cell(window(result), tuple(counts), support))
        require(
            [list(c.window) for c in cells] == expected["windows"]
            and len({c.window for c in cells}) == len(cells),
            "Exact ordered source window population differs",
        )
        output.append(
            Core(
                expected["id"],
                expected["country"],
                row["native_site_id"],
                row["native_dataset_id"],
                row["native_collection_unit_id"],
                tuple(axis),
                ppe,
                sd,
                factors_flat,
                tuple(cells),
            )
        )
    require(
        len({c.site for c in output}) == 7,
        "Solsoe cores must remain one physical place",
    )
    require(
        sum(len(c.cells) for c in output if c.country == "SE") == 77,
        "Exactly77Swedish baseline windows required",
    )
    return tuple(output)


def load(
    repository: Path,
) -> tuple[tuple[Core, ...], dict[str, Any], list[dict[str, Any]]]:
    path = repository / PROTOCOL
    raw = buffer(path, PROTOCOL_SHA256, path.stat().st_size)
    protocol = decode(raw)
    pins = [{"path": str(path), "sha256": digest(raw), "bytes": len(raw)}]
    values = {}
    for name, row in protocol["inputs"].items():
        relative = Path(row["path"])
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "Relative source locator required",
        )
        body = buffer(repository / relative, row["sha256"], row["bytes"])
        values[name] = decode(body)
        pins.append({**row, "path": str(repository / relative)})
    require(
        values["swedish_report"]["protocol_sha256"]
        == protocol["inputs"]["swedish_protocol"]["sha256"]
        and values["swedish_report"]["source_identity_declaration_sha256"]
        == protocol["inputs"]["swedish_identity"]["sha256"],
        "Swedish source declaration authority differs",
    )
    require(
        values["nordic_report"]["protocol"] == values["nordic_protocol"],
        "Nordic protocol authority differs",
    )
    return (
        normalize(values["swedish_report"], values["nordic_report"], protocol),
        protocol,
        pins,
    )
