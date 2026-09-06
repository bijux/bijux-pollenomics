"""Safe filesystem access and strict admission value decoding."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath

from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    NORDIC_COUNTRY_CODES,
)

from .models import _SHA256, _SHA256_ID


def _row_identity(row: Mapping[str, object], index: int, primary_key: str) -> str:
    value = row.get(primary_key)
    return f"{primary_key}:{value}" if value is not None else f"row:{index}"


def _validated_source_directory(path: Path) -> Path:
    root = Path(path)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD acquisition source must be a safe absolute path")
    if root.is_symlink():
        raise ValueError(f"SEAD acquisition source cannot be a symlink: {root}")
    if not root.is_dir():
        raise ValueError(f"SEAD acquisition source is not a directory: {root}")
    _reject_symlink_ancestors(root)
    return root


def _validated_source_file(path: Path) -> Path:
    source = Path(path)
    if not source.is_absolute() or source == Path(source.anchor):
        raise ValueError("SEAD country decisions must use a safe absolute path")
    _reject_symlink_ancestors(source)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"SEAD country decisions are not a regular file: {source}")
    return source


def _validated_output_parent(path: Path) -> Path:
    parent = Path(path)
    if (
        not parent.is_absolute()
        or parent == Path(parent.anchor)
        or ".." in parent.parts
    ):
        raise ValueError("SEAD admission output must be a safe absolute path")
    _reject_symlink_ancestors(parent)
    if parent.exists() and (parent.is_symlink() or not parent.is_dir()):
        raise ValueError(f"SEAD admission parent is unsafe: {parent}")
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise ValueError("SEAD admission parent cannot be a symlink")
    return parent


def _reject_output_overlap(
    output_root: Path, *, source_root: Path, decisions_path: Path
) -> None:
    output = Path(output_root)
    if not output.is_absolute():
        raise ValueError("SEAD admission output must be a safe absolute path")
    resolved_output = output.resolve(strict=False)
    resolved_source = source_root.resolve(strict=True)
    resolved_decisions = decisions_path.resolve(strict=True)
    if resolved_output.is_relative_to(
        resolved_source
    ) or resolved_source.is_relative_to(resolved_output):
        raise ValueError("SEAD admission output overlaps acquisition source")
    if resolved_decisions.is_relative_to(
        resolved_output
    ) or resolved_output.is_relative_to(resolved_decisions):
        raise ValueError("SEAD admission output overlaps country decisions")


def _reject_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError(f"SEAD acquisition path traverses a symlink: {ancestor}")


def _directory_bytes(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise FileExistsError(f"Symlink in SEAD admission output: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def _read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Required SEAD acquisition file is not regular: {path}")
    return path.read_bytes()


def _json_object(content: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid SEAD JSON object: {label}") from exc
    if not isinstance(value, dict):
        raise TypeError(f"SEAD JSON value must be an object: {label}")
    return value


def _safe_relative_path(value: object) -> str:
    text = _required_text(value, "manifest file path")
    path = PurePosixPath(text)
    if (
        path.is_absolute()
        or text != path.as_posix()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError(f"Unsafe SEAD manifest file path: {text}")
    return text


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a string list")
    return list(value)


def _positive_int_list(value: object, label: str) -> list[int]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a positive integer list")
    return [_positive_int(item, label) for item in value]


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"SEAD {label} must be an object")
    return value


def _bbox(value: object, label: str) -> tuple[float, float, float, float]:
    if not isinstance(value, list) or len(value) != 4:
        raise ValueError(f"SEAD {label} must have four coordinates")
    coordinates = tuple(
        _coordinate(
            item, label, -180 if index % 2 == 0 else -90, 180 if index % 2 == 0 else 90
        )
        for index, item in enumerate(value)
    )
    minimum_longitude, minimum_latitude, maximum_longitude, maximum_latitude = (
        coordinates
    )
    if minimum_longitude >= maximum_longitude or minimum_latitude >= maximum_latitude:
        raise ValueError(f"SEAD {label} is reversed or empty")
    return (
        minimum_longitude,
        minimum_latitude,
        maximum_longitude,
        maximum_latitude,
    )


def _coordinate(value: object, label: str, minimum: float, maximum: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or not minimum <= float(value) <= maximum
    ):
        raise ValueError(f"SEAD {label} is not a valid coordinate")
    return float(value)


def _country_counts(value: object, label: str) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != set(NORDIC_COUNTRY_CODES):
        raise ValueError(f"{label} must partition SE, DK, NO, FI, and UNASSIGNED")
    return {
        code: _non_negative_int(value.get(code), f"{label} {code}")
        for code in NORDIC_COUNTRY_CODES
    }


def _common_text(rows: Iterable[Mapping[str, object]], field: str) -> str:
    values = {_required_text(row.get(field), f"receipt {field}") for row in rows}
    if len(values) != 1:
        raise ValueError(f"SEAD receipts disagree on {field}")
    return next(iter(values))


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be non-empty canonical text")
    return value


def _positive_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _non_negative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"Invalid SHA-256 for {label}")
    return value


def _sha256_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_ID.fullmatch(value):
        raise ValueError(f"Invalid SHA-256 identity for {label}")
    return value


def _expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"SEAD {label} mismatch: {actual!r} != {expected!r}")


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _observed_schema(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
    fields = sorted({field for row in rows for field in row})
    return {
        "row_count": len(rows),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in rows),
                "null_count": sum(
                    row.get(field) is None for row in rows if field in row
                ),
                "json_types": sorted(
                    {_json_type(row[field]) for row in rows if field in row}
                ),
            }
            for field in fields
        ],
    }


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _file_set_digest(records: Sequence[Mapping[str, object]]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(list(records))).hexdigest()
