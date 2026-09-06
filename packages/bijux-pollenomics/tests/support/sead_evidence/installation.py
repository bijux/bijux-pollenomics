"""SEAD atlas projection fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    sead as sead_projection,
)

from .scenario import write_sead_projection_fixture


def install_sead_projection_fixture(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    observation_entity_id: str = "sead-analysis-entity:90",
) -> None:
    manifest_sha256, admission_sha256 = write_sead_projection_fixture(
        root, observation_entity_id=observation_entity_id
    )
    monkeypatch.setattr(
        sead_projection,
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        manifest_sha256,
    )
    monkeypatch.setattr(
        sead_projection,
        "SEAD_GOVERNED_ADMISSION_SHA256",
        admission_sha256,
    )
