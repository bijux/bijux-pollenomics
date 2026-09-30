"""Check the root research library and its selected governed source identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
LOCK = REPORTS / "source-lock.json"
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
LOCAL_RUN_PATH = re.compile(r"(?:/Users|/home)/[^/\s]+/|artifacts/v\d+/")
HUMAN_SURFACES = (
    REPORTS,
    ROOT / "docs/report",
    ROOT / "docs/public",
    ROOT / "presentation",
)


def verify_reader_paths() -> None:
    """Keep disposable run directories and personal checkouts out of reader text."""
    for surface in HUMAN_SURFACES:
        for suffix in ("*.md", "*.tex"):
            for page in sorted(surface.rglob(suffix)):
                for number, line in enumerate(
                    page.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if LOCAL_RUN_PATH.search(line):
                        relative = page.relative_to(ROOT)
                        raise ValueError(
                            f"Local run path in reader text: {relative}:{number}"
                        )


def main() -> None:
    verify_reader_paths()
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "research-report-source-lock.v1":
        raise ValueError("Unexpected research report source lock")
    reports = sorted(
        path.relative_to(ROOT).as_posix() for path in REPORTS.rglob("*.md")
    )
    if reports != lock["reports"]:
        raise ValueError("Research report inventory changed; review its source lock")
    for relative, expected in lock["sources"].items():
        path = ROOT / relative
        if (
            not path.is_file()
            or not path.resolve().is_relative_to(ROOT)
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError(
                f"Review changed research source before publishing: {relative}"
            )
    checked = 0
    for relative in reports:
        page = ROOT / relative
        for target in LINK.findall(page.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "mailto:", "#")):
                continue
            local = target.split("#", 1)[0]
            if not (page.parent / local).exists():
                raise ValueError(f"Broken research link: {relative} -> {target}")
            checked += 1
    print(
        f"verified {len(reports)} research pages, {len(lock['sources'])} "
        f"locked sources and {checked} local links"
    )


if __name__ == "__main__":
    main()
