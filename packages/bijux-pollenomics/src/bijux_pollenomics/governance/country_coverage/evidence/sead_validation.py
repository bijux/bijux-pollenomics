"""SEAD admission and country-accounting validation."""

from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
)

from ..constants import _CODE_TO_NAME, _NORDIC_COUNTRY_CODES, CountryCoverageError
from ..decoding import (
    _integer,
    _integer_counts,
    _object,
    _require_sha256_id,
    _required_text,
)


def _validate_sead_country_summaries(
    admission: Mapping[str, object],
    decisions: Mapping[str, object],
    *,
    decision_count: int,
    decision_statuses: Mapping[str, int],
    decision_methods: Mapping[str, int],
    decision_country_codes: Mapping[str, int],
    governed: Mapping[str, int],
    boundary_digest: str,
    boundary_version: str,
    country_assignment_sha256: str,
    boundary_counts: Mapping[str, int],
    boundary_manifest: Mapping[str, object],
    boundary_manifest_sha256: str,
) -> None:
    _validate_admission_identity(admission, decisions)
    authority = _validate_boundary_authority(
        decisions,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        boundary_manifest=boundary_manifest,
        boundary_manifest_sha256=boundary_manifest_sha256,
    )
    accounting = _object(admission.get("country_accounting"), "country accounting")
    _validate_assignment_identity(
        accounting,
        authority=authority,
        country_assignment_sha256=country_assignment_sha256,
    )
    _validate_decision_counts(
        decisions,
        decision_count=decision_count,
        decision_statuses=decision_statuses,
        decision_methods=decision_methods,
        decision_country_codes=decision_country_codes,
    )
    _validate_admission_counts(
        accounting,
        decision_count=decision_count,
        decision_statuses=decision_statuses,
        governed=governed,
        boundary_counts=boundary_counts,
    )


def _validate_admission_identity(
    admission: Mapping[str, object], decisions: Mapping[str, object]
) -> None:
    if admission.get("source_family") != "sead":
        raise CountryCoverageError("SEAD admission source family is inconsistent")
    _require_sha256_id(
        _required_text(admission, "scope_id"), "SEAD admission scope identity"
    )
    _require_sha256_id(
        _required_text(admission, "build_id"), "SEAD admission build identity"
    )
    if admission.get("scope_id") != SEAD_GOVERNED_EVIDENCE_SCOPE_ID:
        raise CountryCoverageError("SEAD admission governed scope identity changed")
    declared_scope = _object(admission.get("declared_scope"), "SEAD declared scope")
    expected_scope = {
        "scope_key": "full_evidence_relations",
        "table_count": 61,
        "join_count": 86,
    }
    if any(declared_scope.get(key) != value for key, value in expected_scope.items()):
        raise CountryCoverageError("SEAD admission is not the full evidence scope")
    if admission.get("run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID:
        raise CountryCoverageError("SEAD admission governed run identity changed")
    if admission.get("parent_run_id") != decisions.get("run_id"):
        raise CountryCoverageError(
            "SEAD admission and country decisions disagree on parent run identity"
        )


def _validate_boundary_authority(
    decisions: Mapping[str, object],
    *,
    boundary_digest: str,
    boundary_version: str,
    boundary_manifest: Mapping[str, object],
    boundary_manifest_sha256: str,
) -> Mapping[str, object]:
    authority = _object(decisions.get("boundary_authority"), "boundary authority")
    expected_identity = {
        "artifact_digest": boundary_digest,
        "normalized_artifact_sha256": boundary_digest.removeprefix("sha256:"),
        "version": boundary_version.removeprefix("natural-earth:"),
        "manifest_sha256": boundary_manifest_sha256,
    }
    for field, expected in expected_identity.items():
        if authority.get(field) != expected:
            raise CountryCoverageError(
                f"SEAD boundary authority {field} is inconsistent"
            )
    manifest_artifacts = _object(
        boundary_manifest.get("country_artifacts"), "boundary country artifacts"
    )
    expected_country_digests = {
        _CODE_TO_NAME[code]: _required_text(
            _object(manifest_artifacts[_CODE_TO_NAME[code]], "boundary artifact"),
            "sha256",
        )
        for code in _NORDIC_COUNTRY_CODES
    }
    if authority.get("country_artifact_sha256") != dict(
        sorted(expected_country_digests.items())
    ):
        raise CountryCoverageError("SEAD country boundary digests are inconsistent")
    return authority


def _validate_assignment_identity(
    accounting: Mapping[str, object],
    *,
    authority: Mapping[str, object],
    country_assignment_sha256: str,
) -> None:
    _require_sha256_id(
        _required_text(accounting, "boundary_authority_id"),
        "SEAD boundary authority identity",
    )
    if accounting.get("boundary_authority_id") != authority.get("authority_id"):
        raise CountryCoverageError("SEAD boundary authority identity is inconsistent")
    if accounting.get("country_assignment_sha256") != country_assignment_sha256:
        raise CountryCoverageError("SEAD country assignment digest does not reconcile")


def _validate_decision_counts(
    decisions: Mapping[str, object],
    *,
    decision_count: int,
    decision_statuses: Mapping[str, int],
    decision_methods: Mapping[str, int],
    decision_country_codes: Mapping[str, int],
) -> None:
    expected_counts = (
        (
            "decision_status_counts",
            "decision statuses",
            decision_statuses,
            "SEAD decision status counts do not reconcile",
        ),
        (
            "decision_method_counts",
            "decision methods",
            decision_methods,
            "SEAD decision method counts do not reconcile",
        ),
        (
            "country_counts",
            "decision countries",
            decision_country_codes,
            "SEAD decision country counts do not reconcile",
        ),
    )
    for field, label, expected, error_message in expected_counts:
        if _integer_counts(decisions.get(field), label) != dict(
            sorted(expected.items())
        ):
            raise CountryCoverageError(error_message)
    bbox_count = _integer(decisions.get("bbox_site_count"), "SEAD bbox site count")
    if bbox_count != decision_count:
        raise CountryCoverageError("SEAD bbox site count does not reconcile")


def _validate_admission_counts(
    accounting: Mapping[str, object],
    *,
    decision_count: int,
    decision_statuses: Mapping[str, int],
    governed: Mapping[str, int],
    boundary_counts: Mapping[str, int],
) -> None:
    nordic_counts = {
        country: int(governed.get(country, 0)) for country in ("SE", "DK", "NO", "FI")
    }
    expected_accounting = {
        "bbox_site_count": decision_count,
        "admitted_site_count": sum(nordic_counts.values()),
        "review_site_count": int(decision_statuses.get("review", 0)),
        "unassigned_site_count": int(decision_statuses.get("unassigned", 0)),
        "scope_excluded_count": int(decision_statuses.get("review", 0))
        + int(decision_statuses.get("unassigned", 0)),
    }
    for field, expected in expected_accounting.items():
        if _integer(accounting.get(field), f"SEAD {field}") != expected:
            raise CountryCoverageError(f"SEAD admission {field} does not reconcile")
    if (
        _integer_counts(accounting.get("country_counts"), "admitted country counts")
        != nordic_counts
    ):
        raise CountryCoverageError("SEAD admission country counts do not reconcile")
    if dict(boundary_counts) != dict.fromkeys(_NORDIC_COUNTRY_CODES, 1):
        raise CountryCoverageError("SEAD governed boundary inventory is inconsistent")
    if accounting.get("reconciles") is not True:
        raise CountryCoverageError(
            "SEAD admission country accounting is not reconciled"
        )
