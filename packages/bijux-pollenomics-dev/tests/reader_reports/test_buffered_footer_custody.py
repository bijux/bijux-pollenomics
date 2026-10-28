"""A managed reader footer cannot replace or conceal sealed domain output."""

import ast
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    Account,
    Route,
    authored_reader,
    render_route,
)

ROOT = Path(__file__).resolve().parents[4]


def helper(root: Path, routes: dict[str, Route]) -> dict[str, Any]:
    path = ROOT / "docs/report/pollen-reconstruction/verify_report.py"
    tree = ast.parse(path.read_text())
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_buffered_reader_content", "_buffered_reader_markdown"}
    ]
    namespace: dict[str, Any] = {
        "Path": Path,
        "REPOSITORY_ROOT": root,
        "load_routes": lambda: routes,
        "authored_reader": authored_reader,
        "render_route": render_route,
    }
    exec(compile(tree, str(path), "exec"), namespace)
    return namespace


@pytest.mark.parametrize(
    "damage", [None, "managed_claim", "trailing", "malformed", "undeclared", "absent"]
)
def test_exact_route_is_validated_before_peeling(
    tmp_path: Path, damage: str | None
) -> None:
    relative = "docs/report/pollen-reconstruction/author-buffered-pollen/README.md"
    route = Route(
        relative,
        (Account("reports/science/conditional.md"),),
        "Only 12/13 source cells qualify.",
    )
    source = b"# Original source\n\nExact 12/13 domain cells.\n"
    raw = render_route(source, route)
    routes = {relative: route}
    if damage == "managed_claim":
        raw = raw.replace(b"12/13 source", b"13/13 source")
    elif damage == "trailing":
        raw += b"<script>unqualified</script>"
    elif damage == "malformed":
        raw = raw.replace(b"route:end", b"route:missing")
    elif damage == "undeclared":
        routes = {}
    elif damage == "absent":
        raw = source
    api = helper(tmp_path, routes)
    if damage:
        with pytest.raises(ValueError):
            api["_buffered_reader_content"](tmp_path / relative, raw)
    else:
        assert api["_buffered_reader_content"](tmp_path / relative, raw) == source
        assert (
            api["_buffered_reader_content"](tmp_path / "result.json", b'{"value":12}')
            == b'{"value":12}'
        )


def test_readme_alias_is_applied_only_after_route_admission(tmp_path: Path) -> None:
    relative = "docs/report/pollen-reconstruction/author-buffered-pollen/README.md"
    route = Route(
        relative,
        (Account("reports/science/conditional.md"),),
        "Conditional source scope.",
    )
    link = (
        b"[family replay](https://github.com/bijux/bijux-pollenomics/blob/"
        b"6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/"
        b"pollen-reconstruction/author-buffered-pollen/replay.py)"
    )
    api = helper(tmp_path, {relative: route})
    raw = render_route(b"# Source\n\n" + link + b"\n", route)
    peeled = api["_buffered_reader_content"](tmp_path / relative, raw)
    assert (
        api["_buffered_reader_markdown"](peeled)
        == b"# Source\n\n[family replay](replay.py)\n"
    )
    with pytest.raises(ValueError, match="ambiguous"):
        api["_buffered_reader_markdown"](link + link)
