from __future__ import annotations

from bijux_pollenomics.adna.workflow.normalization import (
    RECOVERED_SAMPLE_EVIDENCE_STATUSES,
    AdnaSpeciesNormalizationBundle,
)


def _validate_tracked_sample_admission(bundle: AdnaSpeciesNormalizationBundle) -> None:
    """Refuse tracked normalization when placeholder sample rows leak through."""
    violations = sorted(
        record.genetic_id
        for record in bundle.sample_records
        if record.sample_evidence_status not in RECOVERED_SAMPLE_EVIDENCE_STATUSES
        or record.sample_identity_resolution != "final"
    )
    if violations:
        raise ValueError(
            "Tracked animal aDNA samples contain non-admissible placeholders: "
            + ", ".join(violations)
        )
