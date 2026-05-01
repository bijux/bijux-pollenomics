"""Ensure maintainer tooling stays isolated from runtime scientific logic."""

from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SRC = REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "src"
FORBIDDEN_RUNTIME_IMPORTS = (
    "bijux_pollenomics.analysis",
    "bijux_pollenomics.reporting",
    "bijux_pollenomics.data_downloader",
    "bijux_pollenomics.command_line",
)


def test_dev_package_does_not_import_runtime_scientific_logic() -> None:
    failures: list[str] = []

    for path in DEV_SRC.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_RUNTIME_IMPORTS:
            pattern = rf"(^|\n)\s*(from|import)\s+{re.escape(forbidden)}(\.|\s|$)"
            if re.search(pattern, text):
                failures.append(f"{path.relative_to(REPO_ROOT)} imports {forbidden}")

    assert not failures, "dev package runtime-isolation violations:\n" + "\n".join(
        failures
    )
