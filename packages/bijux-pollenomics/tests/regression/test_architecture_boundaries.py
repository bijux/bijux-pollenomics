from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[4]
RUNTIME_SRC = REPO_ROOT / "packages" / "bijux-pollenomics" / "src" / "bijux_pollenomics"
DATA_DOWNLOADER_SRC = RUNTIME_SRC / "data_downloader"
REPORTING_SRC = RUNTIME_SRC / "reporting"
ADNA_SRC = RUNTIME_SRC / "adna"
EVIDENCE_SRC = RUNTIME_SRC / "evidence"


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


def test_harmonization_logic_stays_out_of_map_rendering_layers() -> None:
    map_rendering_roots = [
        REPORTING_SRC / "map_document",
        REPORTING_SRC / "rendering",
    ]
    failures: list[str] = []
    forbidden_pattern = (
        r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.analysis\.harmonization(\.|\s|$)"
    )

    for root in map_rendering_roots:
        failures.extend(_find_forbidden_imports(_python_files(root), forbidden_pattern))

    assert not failures, (
        "map rendering imports harmonization logic directly:\n" + "\n".join(failures)
    )


def test_ranking_logic_stays_out_of_publication_modules() -> None:
    failures = _find_forbidden_imports(
        _python_files(REPORTING_SRC),
        r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.analysis\.(ranking|site_candidates|reporting)(\.|\s|$)",
    )

    assert not failures, (
        "publication modules import ranking logic directly:\n" + "\n".join(failures)
    )


def test_runtime_package_does_not_import_dev_tooling_modules() -> None:
    failures = _find_forbidden_imports(
        _python_files(RUNTIME_SRC),
        r"(^|\n)\s*(from|import)\s+bijux_pollenomics_dev(\.|\s|$)",
    )

    assert not failures, "runtime package imports dev tooling modules:\n" + "\n".join(
        failures
    )


def test_adna_domain_stays_out_of_reporting_and_command_line_layers() -> None:
    failures: list[str] = []
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.reporting(\.|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.command_line(\.|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.foundation(\.|\s|$)",
        )
    )

    assert not failures, "adna domain imports higher-level runtime layers:\n" + "\n".join(
        failures
    )


def test_reporting_api_routes_through_reporting_adna_not_reporting_aadr() -> None:
    reporting_api = (REPORTING_SRC / "api.py").read_text(encoding="utf-8")

    assert "from .adna import" in reporting_api
    assert "from .aadr import" not in reporting_api


def test_adna_domain_does_not_import_publication_or_rendering_policy_modules() -> None:
    failures: list[str] = []
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.publication_policy(\.|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.reporting\.rendering(\.|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(ADNA_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.reporting\.bundles(\.|\s|$)",
        )
    )

    assert not failures, "adna domain imports publication-facing policy or rendering modules:\n" + "\n".join(
        failures
    )


def test_release_readiness_gate_stays_outside_adna_domain() -> None:
    release_gate = (
        RUNTIME_SRC / "foundation" / "release_readiness.py"
    ).read_text(encoding="utf-8")
    release_bar = (RUNTIME_SRC / "foundation" / "release_bar.py").read_text(encoding="utf-8")
    adna_modules = "\n".join(
        path.read_text(encoding="utf-8") for path in _python_files(ADNA_SRC)
    )

    assert "build_release_readiness_report" in release_gate
    assert "build_release_readiness_report" not in adna_modules
    assert "build_release_bar" in release_bar
    assert "build_release_bar" not in adna_modules


def test_evidence_domain_does_not_import_rendering_cli_or_foundation_layers() -> None:
    failures: list[str] = []
    failures.extend(
        _find_forbidden_imports(
            _python_files(EVIDENCE_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.reporting(\.rendering|\.map_document|\.bundles|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(EVIDENCE_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.command_line(\.|\s|$)",
        )
    )
    failures.extend(
        _find_forbidden_imports(
            _python_files(EVIDENCE_SRC),
            r"(^|\n)\s*(from|import)\s+bijux_pollenomics\.foundation(\.|\s|$)",
        )
    )

    assert not failures, "evidence domain imports higher-level runtime layers:\n" + "\n".join(
        failures
    )
