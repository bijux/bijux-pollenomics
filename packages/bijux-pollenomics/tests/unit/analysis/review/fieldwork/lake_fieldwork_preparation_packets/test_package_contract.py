"""Compatibility and topology contract for the packet package."""

from __future__ import annotations

import inspect
from pathlib import Path

from bijux_pollenomics.analysis.review.fieldwork import (
    lake_fieldwork_preparation_packets as packets,
)

EXPECTED_SIGNATURES = {
    "build_lake_fieldwork_preparation_payload": "(report: 'LakeEvidenceRichnessReport', *, top_n: 'int' = 20) -> 'dict[str, Any]'",
    "write_lake_fieldwork_preparation_json": "(path: 'Path', report: 'LakeEvidenceRichnessReport', *, top_n: 'int' = 20) -> 'None'",
    "write_lake_fieldwork_preparation_csv": "(path: 'Path', report: 'LakeEvidenceRichnessReport', *, top_n: 'int' = 20) -> 'None'",
    "render_lake_fieldwork_preparation_markdown": "(payload: 'dict[str, Any]') -> 'str'",
    "render_lake_fieldwork_preparation_section": "(*, json_name: 'str', csv_name: 'str', markdown_name: 'str') -> 'str'",
    "_build_fieldwork_preparation_row": "(assessment: 'LakeEvidenceRichnessAssessment', *, fieldwork_rank: 'int') -> 'dict[str, object]'",
    "_identity_posture": "(ambiguity_flags: 'tuple[str, ...]') -> 'str'",
    "_sead_context_posture": "(sead_site_count: 'int') -> 'str'",
    "_palaeopen_alignment_posture": "(*, direct_pollen_source_count: 'int', evidence_family_count: 'int') -> 'str'",
    "_preparation_posture": "(*, ambiguity_flags: 'tuple[str, ...]', sampling_posture: 'str', sampling_fit: 'float', human_context_posture: 'str', direct_pollen_source_count: 'int', evidence_family_count: 'int', sead_site_count: 'int', human_locality_count: 'int', scenario_consistency_posture: 'str') -> 'str'",
    "_required_actions": "(*, ambiguity_flags: 'tuple[str, ...]', sampling_posture: 'str', human_context_posture: 'str', scenario_consistency_posture: 'str', sead_context_posture: 'str', palaeopen_alignment_posture: 'str', preparation_posture: 'str') -> 'list[str]'",
    "_scenario_top20_presence_count": "(*, aggregate_rank: 'int', scenario_ranks: 'dict[str, int]') -> 'int'",
    "_scenario_consistency_posture": "(top20_presence_count: 'int') -> 'str'",
    "_google_maps_url": "(latitude: 'float', longitude: 'float') -> 'str'",
}


def test_compatibility_surface_preserves_every_signature_and_export() -> None:
    assert packets.__all__ == [
        "build_lake_fieldwork_preparation_payload",
        "render_lake_fieldwork_preparation_markdown",
        "render_lake_fieldwork_preparation_section",
        "write_lake_fieldwork_preparation_csv",
        "write_lake_fieldwork_preparation_json",
    ]
    assert {
        name: str(inspect.signature(getattr(packets, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES
    assert all(
        getattr(packets, name).__module__ == packets.__name__
        for name in EXPECTED_SIGNATURES
    )


def test_package_has_only_intent_owned_small_modules() -> None:
    package_root = Path(packets.__file__).parent
    source_files = sorted(path.name for path in package_root.glob("*.py"))
    assert source_files == [
        "__init__.py",
        "candidate_row.py",
        "csv_output.py",
        "json_output.py",
        "markdown_output.py",
        "operations_api.py",
        "payloads.py",
        "postures.py",
    ]
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )
