"""Recognize the declared spatial exports without changing historical bindings."""

from __future__ import annotations

import ast

SPATIAL_EXPORT_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/"
    "lra_validation/spatial/__init__.py"
)
_EXPORT_NAMES = (
    "JointSpatialDraw",
    "UnavailableSpatialDraw",
    "propagate_withheld_spatial_draws",
    "spatial_identifiability",
)
_IMPORT_BLOCKS = (
    "from .identifiability import spatial_identifiability\n",
    "from .uncertainty import (\n"
    "    JointSpatialDraw,\n"
    "    UnavailableSpatialDraw,\n"
    "    propagate_withheld_spatial_draws,\n"
    ")\n",
)


def spatial_export_extension_matches(historical: bytes, current: bytes) -> bool:
    """Require exact old bytes after removing only the declared import/export lines.

    The caller authenticates the historical member and confines the current file.
    This recognizes an export boundary; it gives no numerical execution claim to
    the newly exposed functions and permits no change to existing bindings.
    """
    if (
        type(historical) is not bytes
        or type(current) is not bytes
        or not 0 < len(historical) <= 4096
        or not 0 < len(current) <= 4096
    ):
        return False
    try:
        text = current.decode("utf-8")
        tree = ast.parse(text)
    except (UnicodeError, SyntaxError, ValueError, RecursionError):
        return False
    lines = text.splitlines(keepends=True)
    removed: set[int] = set()
    for block in _IMPORT_BLOCKS:
        expected = ast.dump(ast.parse(block).body[0], include_attributes=False)
        matches = [
            node
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and ast.dump(node, include_attributes=False) == expected
        ]
        if len(matches) != 1:
            return False
        statement = matches[0]
        if statement.end_lineno is None:
            return False
        start, end = statement.lineno - 1, statement.end_lineno
        if "".join(lines[start:end]) != block:
            return False
        removed.update(range(start, end))
    bindings = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "__all__"
    ]
    if len(bindings) != 1 or not isinstance(bindings[0].value, ast.List):
        return False
    for name in _EXPORT_NAMES:
        entries = [
            node
            for node in bindings[0].value.elts
            if isinstance(node, ast.Constant)
            and type(node.value) is str
            and node.value == name
        ]
        if len(entries) != 1:
            return False
        entry = entries[0]
        if entry.lineno != entry.end_lineno:
            return False
        if lines[entry.lineno - 1] != f'    "{name}",\n':
            return False
        removed.add(entry.lineno - 1)
    original = "".join(line for i, line in enumerate(lines) if i not in removed)
    return original.encode("utf-8") == historical
