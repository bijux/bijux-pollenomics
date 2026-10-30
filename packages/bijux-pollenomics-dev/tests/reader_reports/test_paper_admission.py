"""Download papers through their original rendered-source and PDF owner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "qualified_paper_downloads", ROOT / "configs/docs/science_downloads.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


def test_real_nine_papers_retain_original_compiled_identities() -> None:
    qualified = HOOK._paper_sources(ROOT)
    manifest = json.loads((ROOT / HOOK.MANIFEST).read_bytes())
    rows = [
        r for r in manifest["files"] if r["path"].startswith("reports/exports/papers/")
    ]
    assert len(qualified) == len(rows) == 9
    assert all(
        qualified[row["path"]]
        == {
            key: row[key]
            for key in ("canonical_source", "source_sha256", "sha256", "bytes")
        }
        for row in rows
    )
    frozen = HOOK.download_bytes(ROOT)
    assert len(frozen) == 12
    assert all(
        frozen[row["site_uri"]] == (ROOT / row["path"]).read_bytes() for row in rows
    )


@pytest.mark.parametrize(
    "path",
    [
        "reports/science/landclim-paper.md",
        "reports/exports/papers/landclim-regional-reconstruction.pdf",
    ],
)
def test_actual_owner_refuses_body_or_pdf_changes_without_mutating_sources(
    monkeypatch: pytest.MonkeyPatch, path: str
) -> None:
    original = Path.read_bytes
    target = ROOT / path

    def changed(value: Path) -> bytes:
        raw = original(value)
        return (
            raw + b"\nUnqualified scientific content change\n"
            if value == target
            else raw
        )

    monkeypatch.setattr(Path, "read_bytes", changed)
    with pytest.raises(
        ValueError, match="Canonical report changed|Retained PDF changed"
    ):
        HOOK.download_bytes(ROOT)


@pytest.mark.parametrize(
    "key", ["source_sha256", "sha256", "bytes", "canonical_source"]
)
def test_download_row_cannot_crosswire_qualified_paper_identity(
    monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    original = HOOK._read
    manifest = json.loads((ROOT / HOOK.MANIFEST).read_bytes())
    manifest["files"][0][key] = manifest["files"][1][key]

    def changed(root: Path, relative: str) -> bytes:
        if relative == HOOK.MANIFEST:
            return json.dumps(manifest).encode()
        return bytes(original(root, relative))

    monkeypatch.setattr(HOOK, "_read", changed)
    with pytest.raises(
        ValueError, match="qualified paper export|canonical source differs"
    ):
        HOOK.download_bytes(ROOT)


def test_paper_owner_failure_is_not_bypassed(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: Any, **kwargs: Any) -> None:
        raise ValueError("Controlled historical source admission refusal")

    monkeypatch.setattr(HOOK.runpy, "run_path", refuse)
    with pytest.raises(ValueError, match="historical source admission refusal"):
        HOOK.download_bytes(ROOT)
