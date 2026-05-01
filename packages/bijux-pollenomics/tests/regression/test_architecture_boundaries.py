from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_SRC = REPO_ROOT / "packages" / "bijux-pollenomics" / "src" / "bijux_pollenomics"
DATA_DOWNLOADER_SRC = RUNTIME_SRC / "data_downloader"
REPORTING_SRC = RUNTIME_SRC / "reporting"


def _python_files(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.py") if path.name != "__init__.py"]


def _find_forbidden_imports(paths: list[Path], forbidden_pattern: str) -> list[str]:
    failures: list[str] = []
    pattern = re.compile(forbidden_pattern)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            failures.append(f"{path.relative_to(REPO_ROOT)}")
    return failures


def test_collection_and_publication_import_boundaries_are_separate() -> None:
    data_failures = _find_forbidden_imports(
        _python_files(DATA_DOWNLOADER_SRC),
        r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.reporting(\.|\s|$)",
    )
    report_failures = _find_forbidden_imports(
        _python_files(REPORTING_SRC),
        r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.data_downloader(\.|\s|$)",
    )

    failures = data_failures + report_failures
    assert not failures, "collection/publication boundary violations:\n" + "\n".join(
        failures
    )
