"""Execute report partition operations across the runtime package boundary."""

from __future__ import annotations

from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
from typing import TypedDict, cast

from ....config import (
    DEFAULT_AADR_VERSION,
    DEFAULT_ATLAS_SLUG,
    DEFAULT_ATLAS_TITLE,
    DEFAULT_PUBLISHED_COUNTRIES,
)
from . import (
    assemble_report_partitions,
    build_report_partition_plan,
    generate_report_partition,
)

_REQUEST_SCHEMA = "published-report-partition-command.v1"
_RESPONSE_SCHEMA = "published-report-partition-response.v1"


class _CommonArguments(TypedDict):
    version_dir: Path
    countries: tuple[str, ...]
    output_root: Path
    published_output_root: Path
    title: str
    slug: str
    context_root: Path
    country_group_size: int


_COMMON_FIELDS = frozenset(_CommonArguments.__annotations__)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON value: {value}")


def _mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _strings(value: object, label: str) -> tuple[str, ...]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise ValueError(f"{label} must be a non-empty string list")
    items = cast(list[str], value)
    if len(items) != len(set(items)):
        raise ValueError(f"{label} must contain unique values")
    return tuple(items)


def _integer(value: object, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _path(value: object, label: str, *, absolute: bool = True) -> Path:
    path = Path(_string(value, label))
    if absolute and not path.is_absolute():
        raise ValueError(f"{label} must be an absolute path")
    return path


def _published_root(value: object) -> Path:
    path = _path(value, "published_output_root", absolute=False)
    if path.is_absolute():
        raise ValueError("published_output_root must be relative")
    return path


def _common(request: dict[str, object]) -> _CommonArguments:
    return {
        "version_dir": _path(request["version_dir"], "version_dir"),
        "countries": _strings(request["countries"], "countries"),
        "output_root": _path(request["output_root"], "output_root"),
        "published_output_root": _published_root(request["published_output_root"]),
        "title": _string(request["title"], "title"),
        "slug": _string(request["slug"], "slug"),
        "context_root": _path(request["context_root"], "context_root"),
        "country_group_size": _integer(
            request["country_group_size"], "country_group_size"
        ),
    }


def _plan(request: dict[str, object]) -> dict[str, object]:
    if set(request) != {"schema_version", "operation", "country_group_size"}:
        raise ValueError("plan request fields are not exact")
    group_size = _integer(request["country_group_size"], "country_group_size")
    countries = tuple(DEFAULT_PUBLISHED_COUNTRIES)
    plan = build_report_partition_plan(
        countries,
        title=DEFAULT_ATLAS_TITLE,
        slug=DEFAULT_ATLAS_SLUG,
        country_group_size=group_size,
    )
    dependent = tuple(
        item.identity for item in plan.partitions if item.required_partition_ids
    )
    scope = tuple(item for item in plan.partition_ids if item not in dependent)
    return {
        "countries": list(countries),
        "dependent_partition_ids": list(dependent),
        "partition_ids": list(plan.partition_ids),
        "scope_partition_ids": list(scope),
        "slug": DEFAULT_ATLAS_SLUG,
        "title": DEFAULT_ATLAS_TITLE,
        "version": DEFAULT_AADR_VERSION,
    }


def _generate(request: dict[str, object]) -> dict[str, object]:
    expected = _COMMON_FIELDS | {
        "schema_version",
        "operation",
        "partition_id",
        "scope_input_root",
    }
    if set(request) != expected:
        raise ValueError("generate request fields are not exact")
    common = _common(request)
    raw_scope = request["scope_input_root"]
    scope = None if raw_scope is None else _path(raw_scope, "scope_input_root")
    result = generate_report_partition(
        _string(request["partition_id"], "partition_id"),
        **common,
        scope_input_root=scope,
    )
    return {
        "partition_id": result.partition.identity,
        "relative_paths": list(result.relative_paths),
    }


def _assemble(request: dict[str, object]) -> dict[str, object]:
    expected = _COMMON_FIELDS | {"schema_version", "operation", "partition_roots"}
    if set(request) != expected:
        raise ValueError("assemble request fields are not exact")
    roots = _mapping(request["partition_roots"], "partition_roots")
    if not roots:
        raise ValueError("partition_roots must be non-empty")
    partition_roots = {
        _string(key, "partition identity"): _path(value, f"partition_roots.{key}")
        for key, value in roots.items()
    }
    common = _common(request)
    assemble_report_partitions(**common, partition_roots=partition_roots)
    return {"output_root": str(common["output_root"])}


def _dispatch(request: dict[str, object]) -> tuple[str, dict[str, object]]:
    if request.get("schema_version") != _REQUEST_SCHEMA:
        raise ValueError("unsupported report partition command schema")
    operation = _string(request.get("operation"), "operation")
    handlers = {"plan": _plan, "generate": _generate, "assemble": _assemble}
    if operation not in handlers:
        raise ValueError(f"unsupported report partition operation: {operation}")
    return operation, handlers[operation](request)


def main(argv: list[str] | None = None) -> int:
    """Read one strict request and emit one strict response."""
    try:
        arguments = sys.argv[1:] if argv is None else argv
        if len(arguments) != 1:
            raise ValueError("exactly one JSON request argument is required")
        request = _mapping(
            json.loads(
                arguments[0],
                object_pairs_hook=_unique_object,
                parse_constant=_reject_constant,
            ),
            "report partition request",
        )
        with redirect_stdout(sys.stderr):
            operation, result = _dispatch(request)
        response = {
            "schema_version": _RESPONSE_SCHEMA,
            "operation": operation,
            "result": result,
        }
        sys.stdout.write(json.dumps(response, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0
    except Exception as error:  # noqa: BLE001 - CLI converts failures to exit status.
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
