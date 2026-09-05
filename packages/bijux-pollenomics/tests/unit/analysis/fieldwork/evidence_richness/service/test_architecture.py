from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.fieldwork.evidence_richness import service


def test_service_implementation_is_bounded_by_intent() -> None:
    package_root = Path(service.__file__).parent
    modules = {
        path.stem: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert {
        "context",
        "orchestration",
        "policies",
        "pollen_report",
        "ranking",
        "signals",
        "svar_report",
    } <= modules.keys()
    assert max(modules.values()) <= 150
    assert not package_root.with_suffix(".py").exists()
