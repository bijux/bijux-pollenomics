"""Explicit synthetic source projection through the existing LRA request validator."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path

from ...engine.errors import LRARefusal
from ...inputs.validation import validate_request
from ..models import canonical_bytes, producer_identity
from ..reading import json_object, read_neotoma_evidence
from .inputs import evidence_files, synthetic_origin, verify_declarations
from .models import SampleChronologyBinding, SourceCellBinding, SyntheticRequestReport
from .projection import project_cells
from .publication import publish_request


def project_synthetic_neotoma_request(
    *,
    raw_root: Path,
    normalized_root: Path,
    input_root: Path,
    request_template: Mapping[str, object],
    cell_bindings: Sequence[SourceCellBinding],
    chronology_bindings: Sequence[SampleChronologyBinding],
    output_directory: Path,
) -> SyntheticRequestReport:
    """Project marked synthetic source receipts, never relabel real observations.

    The template supplies the existing request metadata without derived sample
    counts or ages. Every source cell and chronology claim needs an explicit
    binding. All selected sample observations and all unselected sample IDs must
    be accounted for. Source-native labels are matched exactly; no taxonomic
    crosswalk, count aggregation or chronology default selection is inferred.

    Real or unspecified source provenance refuses even when the template says
    synthetic. This facility does not resolve missing qualified scientific
    permissions, chronology, ecological classification, PPE or geometry review.
    """
    producer = producer_identity()
    content = canonical_bytes(dict(request_template))
    template = json_object(content)
    if template.get("data_kind") != "synthetic":
        raise LRARefusal(
            "source_projection_requires_governed_admission",
            "Only synthetic fixture projection is implemented",
        )
    evidence = read_neotoma_evidence(raw_root, normalized_root)
    fixture = synthetic_origin(evidence)
    try:
        root, files = evidence_files(template, input_root)
        verify_declarations(template, files, fixture)
        lineage = project_cells(
            template, evidence, cell_bindings, chronology_bindings, files
        )
        validate_request(template, input_root=root)
    except (KeyError, TypeError, IndexError) as exc:
        raise LRARefusal("invalid_source_projection_template", str(exc)) from exc
    lineage.update(
        {
            "data_kind": "synthetic",
            "synthetic_fixture_id": fixture,
            "input_template_sha256": hashlib.sha256(content).hexdigest(),
            "scope": "declared_synthetic_source_cells_without_empirical_admission",
        }
    )
    return publish_request(
        template=template,
        lineage=lineage,
        evidence=evidence,
        input_root=root,
        files=files,
        fixture=fixture,
        producer=producer,
        output_directory=output_directory,
    )
