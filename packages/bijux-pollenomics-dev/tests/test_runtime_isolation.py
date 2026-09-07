"""Ensure maintainer tooling stays isolated from runtime scientific logic."""

from __future__ import annotations

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SRC = REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "src"
FORBIDDEN_RUNTIME_IMPORTS = (
    "bijux_pollenomics.adna",
    "bijux_pollenomics.analysis",
    "bijux_pollenomics.command_line",
    "bijux_pollenomics.collection",
    "bijux_pollenomics.evidence",
    "bijux_pollenomics.foundation",
    "bijux_pollenomics.reporting",
)
ALLOWED_RUNTIME_CONTRACT_IMPORTS = {
    "bijux_pollenomics.reporting.source_chronology.source_label_presets",
}
ALLOWED_RUNTIME_INTEGRATION_IMPORTS = {
    Path("bijux_pollenomics_dev/ci/scientific_evidence.py"): {
        "bijux_pollenomics.analysis.propagation.outputs",
        "bijux_pollenomics.analysis.propagation.outputs.models",
        "bijux_pollenomics.evidence.classification.audit_outputs",
        "bijux_pollenomics.evidence.classification.audit_outputs.constants",
        "bijux_pollenomics.evidence.classification.neotoma",
        "bijux_pollenomics.evidence.sources.neotoma",
    }
}


def test_dev_package_does_not_import_runtime_scientific_logic() -> None:
    failures: list[str] = []

    for path in DEV_SRC.rglob("*.py"):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        allowed_imports = ALLOWED_RUNTIME_CONTRACT_IMPORTS | (
            ALLOWED_RUNTIME_INTEGRATION_IMPORTS.get(path.relative_to(DEV_SRC), set())
        )
        contract_imports = {
            imported
            for imported in allowed_imports
            if re.search(
                rf"(^|\n)\s*(from|import)\s+{re.escape(imported)}(\s|$)",
                text,
            )
        }
        contract_only_text = text
        for imported in contract_imports:
            contract_only_text = re.sub(
                rf"(^|\n)(\s*(?:from|import)\s+){re.escape(imported)}(?=\s|$)",
                r"\1\2allowed_runtime_contract",
                contract_only_text,
            )
        for forbidden in FORBIDDEN_RUNTIME_IMPORTS:
            pattern = rf"(^|\n)\s*(from|import)\s+{re.escape(forbidden)}(\.|\s|$)"
            if re.search(pattern, contract_only_text):
                failures.append(f"{path.relative_to(REPO_ROOT)} imports {forbidden}")

    assert not failures, "dev package runtime-isolation violations:\n" + "\n".join(
        failures
    )
