"""Stable JSON serialization for lake preparation packets."""

from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from types import ModuleType
from typing import Any

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)


def write_json(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int,
    build_payload: Callable[..., dict[str, Any]],
    json_module: ModuleType = json,
) -> None:
    path.write_text(
        json_module.dumps(build_payload(report, top_n=top_n), indent=2),
        encoding="utf-8",
    )
