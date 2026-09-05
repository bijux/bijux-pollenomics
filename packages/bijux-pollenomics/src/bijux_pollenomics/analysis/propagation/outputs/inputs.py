"""Safe identity-file, schema, and output-record validation."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any, cast

from .codec import _refuse
from .models import (
    PropagationOutputRefusalError,
    _CANDIDATE_SCHEMA_NAME,
    _EVENT_SCHEMA_NAME,
    _EXPECTED_SCHEMA_IDS,
)


def _read_identity_file(
    path: Path,
    *,
    parent: Path,
    reason_code: str,
    allow_descendant: bool = False,
) -> bytes:
    try:
        resolved_parent = parent.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
    except OSError as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"identity file cannot be resolved: {path.name}",
        ) from error
    direct_parent_matches = (
        path.parent == parent and resolved_path.parent == resolved_parent
    )
    descendant_matches = resolved_path.is_relative_to(resolved_parent)
    if (
        path.is_symlink()
        or not path.is_file()
        or not (descendant_matches if allow_descendant else direct_parent_matches)
    ):
        _refuse(reason_code, f"identity file is unsafe: {path.name}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"identity file cannot be read: {path.name}",
        ) from error


def _path_has_symlink_component(path: Path) -> bool:
    """Return whether any existing component in an absolute path is a symlink."""
    if not path.is_absolute():
        return True
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return True
    return False


def _json_object(value: bytes, *, reason_code: str, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PropagationOutputRefusalError(
            reason_code,
            f"{label} is not valid JSON",
        ) from error
    if not isinstance(payload, dict):
        _refuse(reason_code, f"{label} must be an object")
    return cast(dict[str, Any], payload)


def _load_and_check_schemas(schema_root: Path) -> dict[str, dict[str, Any]]:
    if (
        not schema_root.is_absolute()
        or _path_has_symlink_component(schema_root)
        or not schema_root.is_dir()
    ):
        _refuse(
            "unsafe_schema_root",
            "schema_root must be an existing absolute directory",
        )
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
        from jsonschema.exceptions import SchemaError  # type: ignore[import-untyped]
    except ImportError as error:
        raise PropagationOutputRefusalError(
            "schema_validator_unavailable",
            "jsonschema is required to validate propagation materializations",
        ) from error

    schemas: dict[str, dict[str, Any]] = {}
    for schema_name in (_EVENT_SCHEMA_NAME, _CANDIDATE_SCHEMA_NAME):
        schema_path = schema_root / schema_name
        if (
            schema_path.parent != schema_root
            or _path_has_symlink_component(schema_path)
            or not schema_path.is_file()
        ):
            _refuse(
                "missing_control_schema",
                f"required control schema is missing: {schema_name}",
            )
        try:
            raw_schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PropagationOutputRefusalError(
                "invalid_control_schema",
                f"control schema cannot be read: {schema_name}",
            ) from error
        if not isinstance(raw_schema, dict):
            _refuse(
                "invalid_control_schema",
                f"control schema must be a JSON object: {schema_name}",
            )
        if raw_schema.get("$id") != _EXPECTED_SCHEMA_IDS[schema_name]:
            _refuse(
                "invalid_control_schema",
                f"control schema identity is not governed: {schema_name}",
            )
        try:
            Draft202012Validator.check_schema(raw_schema)
        except SchemaError as error:
            raise PropagationOutputRefusalError(
                "invalid_control_schema",
                f"control schema is invalid: {schema_name}: {error.message}",
            ) from error
        schemas[schema_name] = raw_schema
    return schemas


def _validate_records(
    records: Sequence[Mapping[str, object]],
    schema: Mapping[str, Any],
    *,
    record_kind: str,
) -> None:
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    for index, record in enumerate(records):
        errors = sorted(
            validator.iter_errors(record),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            error = errors[0]
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            _refuse(
                "schema_validation_failed",
                f"{record_kind} {index} fails at {path}: {error.message}",
            )
