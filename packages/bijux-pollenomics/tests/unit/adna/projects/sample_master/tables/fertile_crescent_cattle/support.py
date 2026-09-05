"""Governed PRJEB31621 inputs shared by cattle adapter tests."""

from __future__ import annotations

from hashlib import sha256

from tests.support.repository import REPOSITORY_ROOT

from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_bytes,
    read_source_artifact_text,
)


DATA_ROOT = REPOSITORY_ROOT / "data"
ARCHIVE_PATH = (
    DATA_ROOT
    / "adna/governance/source_library/projects/PRJEB31621/archive_metadata.html"
)
SUPPLEMENT_PATH = (
    DATA_ROOT / "adna/governance/source_library/papers/10.1126-science.aav1002/"
    "supplementary/aav1002_verdugo_sm.pdf"
)


def governed_inputs() -> tuple[str, str]:
    """Return the logical archive text and physical supplement digest."""
    archive_text = read_source_artifact_text(ARCHIVE_PATH)
    supplement_digest = sha256(read_source_artifact_bytes(SUPPLEMENT_PATH)).hexdigest()
    return archive_text, supplement_digest
