from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import cast


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def _validated_output_target(output_root: Path, approved_parent: Path) -> Path:
    surface = _surface()
    return cast(
        Path,
        surface.validated_output_target(
            output_root,
            approved_parent,
            validate_directory=surface._validated_input_directory,
        ),
    )


def _validated_input_directory(path: Path, label: str) -> Path:
    return cast(Path, _surface().validated_input_directory(path, label))


def _read_regular_file(path: Path) -> bytes:
    return cast(bytes, _surface().read_regular_file(path))


def _json_object(content: bytes, path: Path) -> dict[str, object]:
    surface = _surface()
    return cast(
        dict[str, object],
        surface.json_object(content, path, json_module=surface.json),
    )


def _download_dataset_id(row: Mapping[str, object], filename: str) -> int:
    surface = _surface()
    site = surface._mapping(row.get("site"), f"{filename} row site")
    unit = surface._mapping(site.get("collectionunit"), f"{filename} collection unit")
    dataset = surface._mapping(unit.get("dataset"), f"{filename} dataset")
    return int(surface._integer(dataset.get("datasetid"), f"{filename} datasetid"))


def _mapping(value: object, label: str) -> Mapping[str, object]:
    return cast(Mapping[str, object], _surface().mapping(value, label))


def _integer(value: object, label: str) -> int:
    return int(_surface().integer(value, label))


def _positive_integer(value: object, label: str) -> int:
    surface = _surface()
    return int(surface.positive_integer(value, label, parse_integer=surface._integer))


def _non_negative_integer(value: object, label: str) -> int:
    surface = _surface()
    return int(
        surface.non_negative_integer(value, label, parse_integer=surface._integer)
    )


def _integer_list(value: object, label: str) -> list[int]:
    surface = _surface()
    return cast(
        list[int],
        surface.integer_list(value, label, parse_integer=surface._integer),
    )


def _expect_equal(actual: object, expected: object, label: str) -> None:
    _surface().expect_equal(actual, expected, label)


def _canonical_digest(payload: object) -> str:
    surface = _surface()
    return str(
        surface.canonical_digest(
            payload,
            json_module=surface.json,
            hashlib_module=surface.hashlib,
        )
    )


def _parse_alias(value: str) -> tuple[str, str]:
    return cast(tuple[str, str], _surface().parse_alias(value))
