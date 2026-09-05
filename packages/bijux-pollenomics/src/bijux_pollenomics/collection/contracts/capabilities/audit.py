from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from .constants import (
    CAPABILITY_DIMENSIONS,
    _MATERIALIZATION_STATUSES,
    _SUPPORT_STATUSES,
)
from .evidence import _path_has_content, _resolve_path
from .models import _CapabilityAuditRow
from .primitives import _materialization_status
from .profiles import build_source_capability_profiles


def build_source_capability_audit_payload(
    output_root: Path,
    *,
    coverage_metrics_by_source: Mapping[str, Mapping[str, int | None]],
    source_blockers: Mapping[str, tuple[str, ...]],
) -> dict[str, object]:
    """Observe repository materialization without changing source capability."""
    output_root = Path(output_root)
    rows: list[_CapabilityAuditRow] = []
    evidence_validity: dict[tuple[Path, str], bool] = {}
    for profile in build_source_capability_profiles():
        for dimension in CAPABILITY_DIMENSIONS:
            support = profile.support_by_dimension[dimension]
            evidence_paths = profile.evidence_paths_by_dimension[dimension]
            present_paths: list[str] = []
            for repository_path in evidence_paths:
                resolved_path = _resolve_path(output_root, repository_path)
                cache_key = (resolved_path, repository_path)
                if cache_key not in evidence_validity:
                    evidence_validity[cache_key] = _path_has_content(
                        resolved_path, repository_path
                    )
                if evidence_validity[cache_key]:
                    present_paths.append(repository_path)
            present = tuple(present_paths)
            missing = tuple(path for path in evidence_paths if path not in present)
            materialization = _materialization_status(
                support=support,
                evidence_paths=evidence_paths,
                present_evidence_paths=present,
            )
            reasons: list[str] = []
            if materialization == "not_applicable":
                reasons.append("source_dimension_unsupported")
            elif materialization == "missing":
                reasons.append("governed_dimension_evidence_missing")
            elif materialization == "complete":
                reasons.append("governed_dimension_evidence_complete")
            else:
                reasons.append("governed_dimension_evidence_incomplete")
            if materialization != "not_applicable":
                reasons.extend(source_blockers.get(profile.source_key, ()))
                if profile.human_review_required and profile.human_review_reason:
                    reasons.append(profile.human_review_reason)
            rows.append(
                _CapabilityAuditRow(
                    source_key=profile.source_key,
                    dimension=dimension,
                    support=support,
                    materialization=materialization,
                    evidence_paths=evidence_paths,
                    present_evidence_paths=present,
                    missing_evidence_paths=missing,
                    evidence_file_count=len(present),
                    required_evidence_count=len(evidence_paths),
                    coverage_metrics=dict(
                        coverage_metrics_by_source.get(profile.source_key, {})
                    ),
                    human_review_required=(
                        profile.human_review_required
                        and materialization != "not_applicable"
                    ),
                    reason_codes=tuple(dict.fromkeys(reasons)),
                )
            )
    return {
        "schema_version": "source-capability-materialization-audit.v1",
        "dimension_count": len(CAPABILITY_DIMENSIONS),
        "source_count": len(build_source_capability_profiles()),
        "row_count": len(rows),
        "support_vocabulary": sorted(_SUPPORT_STATUSES),
        "materialization_vocabulary": sorted(_MATERIALIZATION_STATUSES),
        "rows": [asdict(row) for row in rows],
    }
