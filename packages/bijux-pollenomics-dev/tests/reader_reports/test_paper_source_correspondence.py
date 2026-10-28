"""Guard exact sealed paper sources and owner-bound download admission."""

import ast
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]


def extracted(path: str, names: set[str], values: dict[str, Any]) -> dict[str, Any]:
    tree = ast.parse((ROOT / path).read_text())
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    exec(compile(tree, path, "exec"), values)
    return values


def test_only_renderer_suppressed_hash_comments_are_removed() -> None:
    api = extracted(
        "reports/exports/papers/verify.py", {"exported_content"}, {"re": re}
    )
    original = (
        b"# Scientific source\n\nExact 12/13 denominator and 0.25 factor.\n"
        b"<!-- scientific-claim-semantic-sha256: " + b"a" * 64 + b" -->\n"
        b"<!-- scientific-authored-source-sha256: " + b"b" * 64 + b" -->\n"
        b"<!-- source-data-sha256: retained -->\n"
    )
    result = api["exported_content"](original)
    assert result == (
        b"# Scientific source\n\nExact 12/13 denominator and 0.25 factor.\n"
        b"<!-- source-data-sha256: retained -->\n"
    )
    assert b"12/13" in result and b"0.25" in result
    damaged = original.replace(
        b"scientific-authored-source-sha256:", b"unknown-source-sha256:"
    )
    assert b"unknown-source-sha256" in api["exported_content"](damaged)


@pytest.mark.parametrize("damage", [None, "population", "owner_mutation"])
def test_paper_downloads_bind_exact_owner_rows(damage: str | None) -> None:
    rows = [
        {
            "pdf": f"paper-{i}.pdf",
            "canonical_report": f"reports/science/paper-{i}.md",
            "source_sha256": "a" * 64,
            "pdf_sha256": "b" * 64,
            "pdf_bytes": 13,
        }
        for i in range(9)
    ]
    if damage == "population":
        rows.pop()
    raw = json.dumps({"papers": rows}).encode()
    state = {"mutated": False}

    def read(_root: Path, path: str) -> bytes:
        if path.endswith("manifest.json"):
            return raw + (b" " if state["mutated"] else b"")
        return b'{"review":"unchanged"}'

    def owner(*_args: object, **_kwargs: object) -> None:
        state["mutated"] = damage == "owner_mutation"

    api = extracted(
        "configs/docs/science_downloads.py",
        {"_paper_sources"},
        {
            "Path": Path,
            "_read": read,
            "json": json,
            "_json_object": lambda pairs: dict(pairs),
            "runpy": SimpleNamespace(run_path=owner),
        },
    )
    if damage:
        with pytest.raises(ValueError):
            api["_paper_sources"](Path("repository"))
    else:
        result = api["_paper_sources"](Path("repository"))
        assert len(result) == 9
        assert result["reports/exports/papers/paper-0.pdf"] == {
            "canonical_source": "reports/science/paper-0.md",
            "source_sha256": "a" * 64,
            "sha256": "b" * 64,
            "bytes": 13,
        }
