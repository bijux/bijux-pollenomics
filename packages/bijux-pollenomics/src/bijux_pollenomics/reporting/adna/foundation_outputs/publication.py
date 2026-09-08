"""Animal foundation publication responsibilities."""

from __future__ import annotations

import json
from pathlib import Path

from .chronology import (
    build_animal_sample_chronology_review,
    build_animal_temporal_comparison_review,
)
from .drift import build_animal_cross_surface_drift_report
from .recovery import (
    build_animal_intake_recovery_review,
    build_animal_sample_database_review,
)
from .release import build_animal_publication_release_gate
from .rendering import (
    render_animal_cross_surface_drift_markdown,
    render_animal_foundation_review_markdown,
    render_animal_foundation_validation_markdown,
    render_animal_intake_recovery_review_markdown,
    render_animal_point_evidence_review_markdown,
    render_animal_project_publication_gap_review_markdown,
    render_animal_publication_release_gate_markdown,
    render_animal_sample_chronology_review_markdown,
    render_animal_sample_database_review_markdown,
    render_animal_scientific_caveat_ledger_markdown,
    render_animal_temporal_comparison_review_markdown,
)
from .review import (
    build_animal_foundation_review_packet,
    build_animal_point_evidence_review,
    build_animal_project_publication_gap_review,
    build_animal_scientific_caveat_ledger,
)
from .validation import build_animal_foundation_validation_report


def publish_animal_foundation_outputs(
    output_root: Path,
    *,
    data_root: Path,
    docs_root: Path,
) -> dict[str, str]:
    """Publish outsider-facing scientific foundation artifacts for animal aDNA outputs."""
    output_root = Path(output_root)
    data_root = Path(data_root)
    docs_root = Path(docs_root)

    validation_payload = build_animal_foundation_validation_report(
        data_root=data_root,
        report_root=output_root,
    )
    drift_payload = build_animal_cross_surface_drift_report(
        data_root=data_root,
        report_root=output_root,
    )
    caveat_payload = build_animal_scientific_caveat_ledger(data_root)
    point_payload = build_animal_point_evidence_review(
        data_root=data_root,
        report_root=output_root,
    )
    absence_payload = build_animal_project_publication_gap_review(
        data_root=data_root,
        report_root=output_root,
    )
    review_payload = build_animal_foundation_review_packet(
        data_root=data_root,
        report_root=output_root,
        validation_payload=validation_payload,
        drift_payload=drift_payload,
        caveat_payload=caveat_payload,
        point_payload=point_payload,
        absence_payload=absence_payload,
    )
    chronology_review_payload = build_animal_sample_chronology_review(
        data_root=data_root
    )
    temporal_comparison_payload = build_animal_temporal_comparison_review(
        data_root=data_root,
        report_root=output_root,
    )
    intake_recovery_payload = build_animal_intake_recovery_review(data_root=data_root)
    sample_database_review_payload = build_animal_sample_database_review(
        data_root=data_root,
        report_root=output_root,
        point_payload=point_payload,
        review_payload=review_payload,
        intake_recovery_payload=intake_recovery_payload,
    )
    release_gate_payload = build_animal_publication_release_gate(
        data_root=data_root,
        report_root=output_root,
        docs_root=docs_root,
        point_payload=point_payload,
        review_payload=review_payload,
        sample_database_review_payload=sample_database_review_payload,
        intake_recovery_payload=intake_recovery_payload,
        temporal_comparison_payload=temporal_comparison_payload,
    )

    payloads = {
        "animal_foundation_validation": (
            validation_payload,
            render_animal_foundation_validation_markdown(validation_payload),
        ),
        "animal_cross_surface_drift": (
            drift_payload,
            render_animal_cross_surface_drift_markdown(drift_payload),
        ),
        "animal_scientific_caveat_ledger": (
            caveat_payload,
            render_animal_scientific_caveat_ledger_markdown(caveat_payload),
        ),
        "animal_point_evidence_review": (
            point_payload,
            render_animal_point_evidence_review_markdown(point_payload),
        ),
        "animal_project_publication_gap_review": (
            absence_payload,
            render_animal_project_publication_gap_review_markdown(absence_payload),
        ),
        "animal_foundation_review": (
            review_payload,
            render_animal_foundation_review_markdown(review_payload),
        ),
        "animal_sample_chronology_review": (
            chronology_review_payload,
            render_animal_sample_chronology_review_markdown(chronology_review_payload),
        ),
        "animal_temporal_comparison_review": (
            temporal_comparison_payload,
            render_animal_temporal_comparison_review_markdown(
                temporal_comparison_payload
            ),
        ),
        "animal_intake_recovery_review": (
            intake_recovery_payload,
            render_animal_intake_recovery_review_markdown(intake_recovery_payload),
        ),
        "animal_sample_database_review": (
            sample_database_review_payload,
            render_animal_sample_database_review_markdown(
                sample_database_review_payload
            ),
        ),
        "animal_publication_release_gate": (
            release_gate_payload,
            render_animal_publication_release_gate_markdown(release_gate_payload),
        ),
    }
    for stem, (payload, markdown) in payloads.items():
        (output_root / f"{stem}.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
        (output_root / f"{stem}.md").write_text(markdown, encoding="utf-8")
    return {f"{stem}_json": f"{stem}.json" for stem in payloads} | {
        f"{stem}_markdown": f"{stem}.md" for stem in payloads
    }
