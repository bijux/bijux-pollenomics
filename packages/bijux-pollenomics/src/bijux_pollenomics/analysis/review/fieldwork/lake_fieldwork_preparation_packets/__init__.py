"""Review-first preparation packets for Swedish lake fieldwork."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)

from ..lake_fieldwork_priority import (
    band_score,
    fieldwork_rows,
    fieldwork_shortlist_score,
    human_context_posture,
)
from .candidate_row import build_candidate_row
from .csv_output import write_csv
from .json_output import write_json
from .markdown_output import render_markdown, render_section
from .operations_api import (
    _build_fieldwork_preparation_row as _build_fieldwork_preparation_row,
)
from .operations_api import _google_maps_url as _google_maps_url
from .operations_api import _identity_posture as _identity_posture
from .operations_api import (
    _palaeopen_alignment_posture as _palaeopen_alignment_posture,
)
from .operations_api import _preparation_posture as _preparation_posture
from .operations_api import _required_actions as _required_actions
from .operations_api import (
    _scenario_consistency_posture as _scenario_consistency_posture,
)
from .operations_api import (
    _scenario_top20_presence_count as _scenario_top20_presence_count,
)
from .operations_api import _sead_context_posture as _sead_context_posture
from .operations_api import (
    build_lake_fieldwork_preparation_payload as build_lake_fieldwork_preparation_payload,
)
from .operations_api import (
    render_lake_fieldwork_preparation_markdown as render_lake_fieldwork_preparation_markdown,
)
from .operations_api import (
    render_lake_fieldwork_preparation_section as render_lake_fieldwork_preparation_section,
)
from .operations_api import (
    write_lake_fieldwork_preparation_csv as write_lake_fieldwork_preparation_csv,
)
from .operations_api import (
    write_lake_fieldwork_preparation_json as write_lake_fieldwork_preparation_json,
)
from .payloads import build_payload
from .postures import (
    google_maps_url,
    identity_posture,
    palaeopen_alignment_posture,
    preparation_posture,
    required_actions,
    scenario_consistency_posture,
    scenario_top20_presence_count,
    sead_context_posture,
)

__all__ = [
    "build_lake_fieldwork_preparation_payload",
    "render_lake_fieldwork_preparation_markdown",
    "render_lake_fieldwork_preparation_section",
    "write_lake_fieldwork_preparation_csv",
    "write_lake_fieldwork_preparation_json",
]

for _definition in (
    build_lake_fieldwork_preparation_payload,
    write_lake_fieldwork_preparation_json,
    write_lake_fieldwork_preparation_csv,
    render_lake_fieldwork_preparation_markdown,
    render_lake_fieldwork_preparation_section,
    _build_fieldwork_preparation_row,
    _identity_posture,
    _sead_context_posture,
    _palaeopen_alignment_posture,
    _preparation_posture,
    _required_actions,
    _scenario_top20_presence_count,
    _scenario_consistency_posture,
    _google_maps_url,
):
    _definition.__module__ = __name__
