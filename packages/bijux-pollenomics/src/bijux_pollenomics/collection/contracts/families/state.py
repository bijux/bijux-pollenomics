from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path

from ....config import DEFAULT_AADR_VERSION
from ..capabilities import build_source_capability_audit_payload
from .authority import _source_authority_state
from .metrics import _coverage_metrics
from .models import SourceFamilyLayerContract, SourceFamilyStateRow
from .registry import build_source_family_contracts


def build_source_family_state_rows(
    output_root: Path,
    *,
    counts: Mapping[str, int],
    version: str = DEFAULT_AADR_VERSION,
) -> tuple[SourceFamilyStateRow, ...]:
    """Build one durable state row per tracked source family."""
    output_root = Path(output_root)
    states: list[SourceFamilyStateRow] = []
    for contract in build_source_family_contracts(version):
        authority = _source_authority_state(
            output_root, contract.source_key, version=version
        )
        raw_status = _layer_status(output_root, contract.raw_layer)
        normalized_status = _layer_status(output_root, contract.normalized_layer)
        reviewed_status = _layer_status(output_root, contract.reviewed_layer)
        published_layer_status = _layer_status(output_root, contract.published_layer)
        published_status = (
            "refused"
            if contract.source_key == "raa" and authority.status == "refused"
            else published_layer_status
        )
        coverage_metrics = _coverage_metrics(
            output_root,
            counts,
            contract.source_key,
            governed_metrics=authority.governed_metrics,
        )
        states.append(
            SourceFamilyStateRow(
                source_key=contract.source_key,
                display_name=contract.display_name,
                domain_group=contract.domain_group,
                evidence_role=contract.evidence_role,
                primary_question=contract.primary_question,
                raw_status=raw_status,
                normalized_status=normalized_status,
                reviewed_status=reviewed_status,
                published_status=published_status,
                provenance_depth=_provenance_depth(
                    raw_status=raw_status,
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                ),
                publication_posture=_publication_posture(
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                    published_status=published_status,
                    authority_status=authority.status,
                ),
                authority_status=authority.status,
                authority_reasons=authority.reason_codes,
                coverage_metrics=coverage_metrics,
                blocking_reasons=_blocking_reasons(
                    raw_status=raw_status,
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                    published_status=published_status,
                    coverage_metrics=coverage_metrics,
                    authority_status=authority.status,
                    authority_reasons=authority.reason_codes,
                ),
            )
        )
    return tuple(states)


def build_source_family_state_matrix_payload(
    output_root: Path,
    *,
    counts: Mapping[str, int],
    version: str = DEFAULT_AADR_VERSION,
) -> dict[str, object]:
    """Build a machine-readable evidence-stage matrix across tracked source families."""
    state_rows = build_source_family_state_rows(
        output_root, counts=counts, version=version
    )
    rows = [asdict(row) for row in state_rows]
    return {
        "schema_version": "source-family-evidence-stage-matrix.v2",
        "row_count": len(rows),
        "rows": rows,
        "capability_materialization_audit": build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={
                row.source_key: row.coverage_metrics for row in state_rows
            },
            source_blockers={
                row.source_key: row.blocking_reasons for row in state_rows
            },
        ),
    }


def _layer_status(output_root: Path, contract: SourceFamilyLayerContract) -> str:
    has_evidence = all(
        _path_has_governed_content(_resolve_repository_path(output_root, artifact_path))
        for artifact_path in contract.example_artifacts
    )
    if not contract.required and not has_evidence:
        return "optional_absent"
    return "present" if has_evidence else "missing"


def _resolve_repository_path(output_root: Path, repository_path: str) -> Path:
    if repository_path == "data":
        return output_root
    if repository_path.startswith("data/"):
        return output_root / repository_path.removeprefix("data/")
    return output_root.parent / repository_path


def _path_has_governed_content(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return not path.name.startswith(".") and path.stat().st_size > 0
    if path.is_dir():
        return any(
            child.is_file()
            and not child.name.startswith(".")
            and child.stat().st_size > 0
            for child in path.rglob("*")
        )
    return False


def _provenance_depth(
    *, raw_status: str, normalized_status: str, reviewed_status: str
) -> str:
    if (
        raw_status == "present"
        and normalized_status == "present"
        and reviewed_status == "present"
    ):
        return "review_ready"
    if raw_status == "present" and normalized_status == "present":
        return "normalized_without_review_layer"
    if raw_status == "present":
        return "captured_only"
    return "missing_source_capture"


def _publication_posture(
    *,
    normalized_status: str,
    reviewed_status: str,
    published_status: str,
    authority_status: str,
) -> str:
    if authority_status == "refused":
        return "refused_not_publication_ready"
    if authority_status == "review_required":
        return "review_required_not_publication_ready"
    if (
        normalized_status == "present"
        and reviewed_status == "present"
        and published_status == "present"
    ):
        return "published_with_review_support"
    if normalized_status == "present" and reviewed_status == "present":
        return "review_ready_not_yet_published"
    if normalized_status == "present":
        return "normalized_but_thin"
    return "not_publication_ready"


def _blocking_reasons(
    *,
    raw_status: str,
    normalized_status: str,
    reviewed_status: str,
    published_status: str,
    coverage_metrics: Mapping[str, int | None],
    authority_status: str,
    authority_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if raw_status == "missing":
        reasons.append("missing_raw_capture")
    if normalized_status == "missing":
        reasons.append("missing_normalized_outputs")
    if reviewed_status == "missing":
        reasons.append("missing_review_surface")
    if published_status == "missing":
        reasons.append("missing_published_surface")
    if authority_status == "refused":
        reasons.append("source_authority_refused")
    elif authority_status == "review_required":
        reasons.append("source_authority_review_required")
    reasons.extend(authority_reasons)
    governed_values = [
        value for value in coverage_metrics.values() if value is not None
    ]
    if coverage_metrics and not governed_values:
        reasons.append("unavailable_governed_coverage_metrics")
    elif not coverage_metrics or not any(value > 0 for value in governed_values):
        reasons.append("zero_coverage_metrics")
    return tuple(dict.fromkeys(reasons))
