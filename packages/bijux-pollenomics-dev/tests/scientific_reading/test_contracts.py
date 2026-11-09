"""Reject incomplete reader observations and altered owning download identities."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.scientific_reading import runner
from bijux_pollenomics_dev.ci.scientific_reading.contracts import (
    DATA,
    ENTRY,
    PREFIX,
    PUBLICATION_RECEIPT,
    ROUTES,
    download_records,
    read_publication_receipt,
    read_regular,
    verify_receipt,
)

ROOT = Path(__file__).resolve().parents[4]


def observation() -> tuple[dict[str, Any], dict[str, Any]]:
    paths = [f"assets/science/papers/{number}.pdf" for number in range(9)]
    paths += [f"assets/science/presentations/{number}.pdf" for number in range(3)]
    paths += list(DATA)
    plan: dict[str, Any] = {
        "candidate": {"sha": "a" * 40},
        "downloads": [
            {"path": path, "bytes": index + 1, "sha256": f"{index:064x}"}
            for index, path in enumerate(paths)
        ],
    }
    origin = "http://127.0.0.1:12345"
    receipt: dict[str, Any] = {
        "status": "PASS",
        "candidate": plan["candidate"],
        "errors": [],
        "browser": {"product": "Chrome/test"},
        "local_origin": origin,
        "viewports": [],
    }
    for width in [1440, 390]:
        receipt["viewports"].append(
            {
                "width": width,
                "entry": ENTRY,
                "entry_heading": "Scientific evidence",
                "entry_overflow": False,
                "routes": [
                    {
                        "path": path,
                        "heading": "Reader question",
                        "clicked": True,
                        "overflow": False,
                        "url": origin + PREFIX + path,
                    }
                    for path in ROUTES
                ],
                "downloads": [
                    {
                        **row,
                        "status": 200,
                        "from_rendered_anchor": True,
                        "clickable": True,
                        "url": origin + PREFIX + row["path"],
                    }
                    for row in plan["downloads"]
                ],
            }
        )
    return plan, receipt


def test_complete_desktop_and_mobile_observations_are_admitted() -> None:
    verify_receipt(*observation())


@pytest.mark.parametrize(
    "change",
    [
        "candidate",
        "console",
        "viewport",
        "entry",
        "entry_overflow",
        "route",
        "click",
        "overflow",
        "heading",
        "download",
        "duplicate",
        "hash",
        "bytes",
        "status",
        "anchor",
        "clickability",
        "escaped_route",
        "escaped_download",
        "external_origin",
    ],
)
def test_incomplete_or_changed_browser_proof_is_refused(change: str) -> None:
    plan, receipt = observation()
    row = receipt["viewports"][1]
    if change == "candidate":
        receipt["candidate"] = {"sha": "b" * 40}
    elif change == "console":
        receipt["errors"] = ["console error"]
    elif change == "viewport":
        receipt["viewports"].pop()
    elif change == "entry":
        row["entry"] = "public/pollenomics/"
    elif change == "entry_overflow":
        row["entry_overflow"] = True
    elif change == "route":
        row["routes"].pop()
    elif change == "click":
        row["routes"][0]["clicked"] = False
    elif change == "overflow":
        row["routes"][0]["overflow"] = True
    elif change == "heading":
        row["routes"][0]["heading"] = ""
    elif change == "download":
        row["downloads"].pop()
    elif change == "duplicate":
        row["downloads"][-1] = copy.deepcopy(row["downloads"][0])
    elif change == "hash":
        row["downloads"][0]["sha256"] = "f" * 64
    elif change == "bytes":
        row["downloads"][0]["bytes"] += 1
    elif change == "status":
        row["downloads"][0]["status"] = 404
    elif change == "anchor":
        row["downloads"][0]["from_rendered_anchor"] = False
    elif change == "clickability":
        row["downloads"][0]["clickable"] = False
    elif change == "escaped_route":
        row["routes"][0]["url"] = "file:///checkout/index.html"
    elif change == "escaped_download":
        row["downloads"][0]["url"] = receipt["local_origin"] + "/outside.pdf"
    elif change == "external_origin":
        receipt["local_origin"] = "https://bijux.io"
    with pytest.raises(ValueError):
        verify_receipt(plan, receipt)


def test_existing_pdf_owner_is_consumed_without_a_copied_registry() -> None:
    raw = subprocess.check_output(
        ("git", "-C", str(ROOT), "show", "HEAD:reports/exports/site-downloads.json")
    )
    manifest = json.loads(raw)
    assert len(download_records(manifest)) == 12
    manifest["files"][-1] = manifest["files"][0]
    with pytest.raises(ValueError, match="duplicated"):
        download_records(manifest)


@pytest.mark.parametrize(
    "relative", ["../outside", "/outside", "a//b", "a/./b", "a\\b", "a?query"]
)
def test_reader_files_are_confined(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError):
        read_regular(tmp_path, relative)


def test_symbolic_reader_roots_and_members_are_refused(tmp_path: Path) -> None:
    (tmp_path / "body").write_bytes(b"owned")
    (tmp_path / "alias").symlink_to(tmp_path / "body")
    with pytest.raises(ValueError, match="symbolic"):
        read_regular(tmp_path, "alias")
    (tmp_path / "root-alias").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic"):
        read_regular(tmp_path / "root-alias", "body")


def test_only_the_publication_receipt_has_the_larger_metadata_budget(
    tmp_path: Path,
) -> None:
    receipt = tmp_path / PUBLICATION_RECEIPT
    receipt.parent.mkdir(parents=True)
    payload = b" " * 20_182_989
    receipt.write_bytes(payload)
    assert read_publication_receipt(tmp_path) == payload
    with pytest.raises(ValueError, match="oversized"):
        read_regular(tmp_path, PUBLICATION_RECEIPT)
    ordinary = tmp_path / "public.json"
    ordinary.write_bytes(payload)
    with pytest.raises(ValueError, match="oversized"):
        read_regular(tmp_path, "public.json")
    with receipt.open("wb") as stream:
        stream.truncate(32 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match="oversized"):
        read_publication_receipt(tmp_path)


def test_failed_source_admission_preserves_a_failed_terminal_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    output = root / "artifacts/evidence"
    with pytest.raises(ValueError, match="exact accepted"):
        runner.run(root, "not-a-commit", Path("/missing-browser"), output)
    result = json.loads((output / "result.json").read_text())
    assert result["status"] == "FAIL" and "exact accepted" in result["error"]
    assert not (output / "browser.json").exists()


def test_failed_source_admission_never_writes_outside_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    output = tmp_path / "outside"
    with pytest.raises(ValueError, match="owned artifact"):
        runner.run(root, "a" * 40, Path("/missing-browser"), output)
    assert not output.exists()
