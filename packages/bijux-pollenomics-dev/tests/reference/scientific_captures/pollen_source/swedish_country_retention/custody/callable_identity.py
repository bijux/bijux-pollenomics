"""Compare complete typed CPython code graphs without marshal identity encodings."""

from __future__ import annotations

import hashlib
import json
import struct
from types import CodeType
from typing import Any

CODE_FIELDS = (
    "co_argcount",
    "co_posonlyargcount",
    "co_kwonlyargcount",
    "co_nlocals",
    "co_stacksize",
    "co_flags",
    "co_code",
    "co_consts",
    "co_names",
    "co_varnames",
    "co_filename",
    "co_name",
    "co_qualname",
    "co_firstlineno",
    "co_linetable",
    "co_exceptiontable",
    "co_freevars",
    "co_cellvars",
)


def code_graph(code: CodeType) -> list[Any]:
    """Preserve all code fields and constant types, including IEEE bit patterns."""
    if type(code) is not CodeType:
        raise ValueError("An actual CPython code object is required")
    nodes = 0

    def encode(value: object, depth: int) -> list[Any]:
        nonlocal nodes
        nodes += 1
        if nodes > 200000 or depth > 128:
            raise ValueError("Bounded code graph exceeded")
        kind = type(value)
        if value is None:
            return ["NoneType"]
        if value is Ellipsis:
            return ["ellipsis"]
        if kind is bool:
            return ["bool", value]
        if kind is int:
            return ["int", str(value)]
        if kind is str:
            return ["str", value]
        if kind is bytes:
            assert isinstance(value, bytes)
            return ["bytes", value.hex()]
        if kind is float:
            assert isinstance(value, float)
            return ["float64", struct.pack("!d", value).hex()]
        if kind is complex:
            assert isinstance(value, complex)
            return ["complex128", struct.pack("!dd", value.real, value.imag).hex()]
        if kind is tuple:
            assert isinstance(value, tuple)
            return ["tuple", [encode(item, depth + 1) for item in value]]
        if kind is frozenset:
            assert isinstance(value, frozenset)
            children = [encode(item, depth + 1) for item in value]
            children.sort(
                key=lambda item: json.dumps(
                    item, ensure_ascii=True, separators=(",", ":")
                )
            )
            return ["frozenset", children]
        if kind is CodeType:
            assert isinstance(value, CodeType)
            return [
                "code",
                [
                    [name, encode(getattr(value, name), depth + 1)]
                    for name in CODE_FIELDS
                ],
            ]
        raise ValueError("Unqualified code constant type: " + kind.__name__)

    return encode(code, 0)


def graph_sha256(graph: list[Any]) -> str:
    raw = json.dumps(
        graph, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    if len(raw) > 8 * 1024**2:
        raise ValueError("Code graph byte ceiling exceeded")
    return hashlib.sha256(raw).hexdigest()


def code_correspondence(expected: CodeType, actual: CodeType) -> dict[str, Any]:
    expected_graph = code_graph(expected)
    actual_graph = code_graph(actual)
    differences = [
        field
        for field, left, right in zip(
            CODE_FIELDS, expected_graph[1], actual_graph[1], strict=True
        )
        if left != right
    ]
    return {
        "schema_version": "cpython-complete-typed-code-correspondence.v1",
        "all_code_fields": list(CODE_FIELDS),
        "expected_code_graph_sha256": graph_sha256(expected_graph),
        "actual_code_graph_sha256": graph_sha256(actual_graph),
        "differing_code_fields": differences,
        "complete_typed_graphs_equal": expected_graph == actual_graph,
        "marshal_reference_or_intern_identity_compared": False,
        "bytecode_filename_lines_flags_exception_tables_or_constant_types_ignored": False,
    }
