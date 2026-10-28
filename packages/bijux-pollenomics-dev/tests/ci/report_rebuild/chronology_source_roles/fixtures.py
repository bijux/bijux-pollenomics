"""Own source strings for exact logical-role and documentation correspondence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

ROOT_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/"
PORTAL = frozenset(
    ROOT_SOURCE + "reporting/presentation/report_portal/" + name + ".py"
    for name in (
        "markdown",
        "narrative_quality",
        "publication",
        "scientific_accounts",
        "scientific_qualifications",
        "surfaces",
    )
)
DOCS = {
    ROOT_SOURCE + "adna/domain/locality.py": ("<module>",),
    ROOT_SOURCE + "adna/domain/models/localities.py": tuple(
        "AdnaLocalitySummary." + name
        for name in (
            "latitude",
            "longitude",
            "latitude_text",
            "longitude_text",
            "coordinate_confidence",
            "locality_namespace",
            "locality_token",
            "time_start_bp",
            "time_end_bp",
            "time_mean_bp",
            "time_label",
            "dating_basis",
            "as_dict",
        )
    ),
    ROOT_SOURCE + "adna/domain/models/occurrence_support.py": (
        "AdnaSampleChronologySupport.as_dict",
    ),
    ROOT_SOURCE + "analysis/classification/events/authority.py": ("<module>",),
    ROOT_SOURCE + "analysis/fieldwork/land_use/context.py": (
        "<module>",
        "overlapping_geojson_context",
        "overlapping_human_context",
        "overlapping_animal_context",
    ),
    ROOT_SOURCE + "analysis/propagation/outputs/models.py": (
        "PropagationOutputRefusalError.__init__",
    ),
    ROOT_SOURCE + "analysis/propagation/projection/selection.py": (
        "PropagationSelection.__post_init__",
        "PropagationSelection.as_dict",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": (
        "main",
    ),
}
MULTI_DOC_PATH = ROOT_SOURCE + "analysis/fieldwork/land_use/context.py"
DOCUMENTATION = '"""Own named documentation."""'


def sha(raw: bytes) -> str:
    """Return the SHA256 identity of a synthetic source body."""
    return hashlib.sha256(raw).hexdigest()


def source_pair(name: str, *, adjacent_blank: bool = False) -> tuple[bytes, bytes]:
    """Generate complete named scopes with fixed own executable values, never package copies."""
    definitions = DOCS[name]

    def body(documented: bool) -> bytes:
        lines = []
        if documented and "<module>" in definitions:
            lines.extend([DOCUMENTATION, ""])
        lines.extend(
            [
                "from __future__ import annotations",
                "",
                "VALUE = 7",
                "LABEL = 'own stable'",
                "",
            ]
        )
        classes: dict[str, list[str]] = {}
        for definition in definitions:
            if definition == "<module>":
                continue
            if "." in definition:
                owner, method = definition.split(".", 1)
                classes.setdefault(owner, []).append(method)
            else:
                lines.append("def " + definition + "():")
                if documented:
                    lines.append("    " + DOCUMENTATION)
                    if adjacent_blank:
                        lines.append("")
                lines.extend(["    return VALUE", "", ""])
        for owner, methods in classes.items():
            lines.append("class " + owner + ":")
            for method in methods:
                lines.append("    def " + method + "(self):")
                if documented:
                    lines.append("        " + DOCUMENTATION)
                    if adjacent_blank:
                        lines.append("")
                lines.append(
                    "        self.value = VALUE"
                    if method == "__init__"
                    else "        return VALUE"
                )
                lines.append("")
            lines.append("")
        lines.extend(["def untouched():", "    return LABEL", ""])
        return "\n".join(lines).encode()

    return body(False), body(True)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Create an isolated directory for source-role controls."""
    root = tmp_path / "repository"
    root.mkdir()
    return root


def current_file(repository: Path, name: str, raw: bytes) -> Path:
    """Write the declared current-source fixture with exact bytes."""
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


@pytest.fixture(autouse=True)
def literal_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bind own doc literals within the exact named source-role authority."""
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        sample_chronology_capture as capture,
    )

    monkeypatch.setattr(
        capture,
        "DOCUMENTED_CAPTURE_STRINGS",
        {
            path: dict.fromkeys(names, "Own named documentation.")
            for path, names in DOCS.items()
        },
    )
