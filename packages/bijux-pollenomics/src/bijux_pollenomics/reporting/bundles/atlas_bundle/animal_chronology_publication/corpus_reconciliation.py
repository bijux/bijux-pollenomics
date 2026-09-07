"""Corpus and refusal denominator reconciliation for chronology publication."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from ....adna.sample_chronology_context.integrity import refusal_rows_sha256
from .contract_values import mapping, mapping_rows, nonblank_text, nonnegative_integer

REFUSAL_REASONS = (
    "sequencing_experiment_identity",
    "sample_identity_not_final",
    "source_chronology_not_comparable",
    "source_coordinate_not_mappable",
    "sample_provenance_unavailable",
    "chronology_provenance_unavailable",
    "site_provenance_unavailable",
)


def validate_refusals(
    accountability: Mapping[str, object], refusals: list[dict[str, object]]
) -> None:
    """Validate refusal vocabulary, identities, counts, and content identity."""
    identities: set[tuple[str, str]] = set()
    reasons: Counter[str] = Counter()
    for row in refusals:
        if set(row) != {"project_accession", "repo_stable_sample_id", "reason_code"}:
            raise ValueError("animal chronology refusal fields differ")
        identity = (
            nonblank_text(row.get("project_accession"), "refusal project"),
            nonblank_text(row.get("repo_stable_sample_id"), "refusal sample"),
        )
        reason = nonblank_text(row.get("reason_code"), "refusal reason")
        if reason not in REFUSAL_REASONS:
            raise ValueError("animal chronology refusal reason differs")
        if identity in identities:
            raise ValueError("animal chronology refusal identity is duplicated")
        identities.add(identity)
        reasons[reason] += 1
    expected_counts = {reason: reasons[reason] for reason in REFUSAL_REASONS}
    if accountability.get("refusal_counts") != expected_counts:
        raise ValueError("animal chronology refusal reason counts differ")
    if accountability.get("refusal_count") != len(refusals):
        raise ValueError("animal chronology accountability refusal count differs")
    if accountability.get("refusal_rows_sha256") != refusal_rows_sha256(refusals):
        raise ValueError("animal chronology refusal content identity differs")


def validate_counts(
    accountability: Mapping[str, object],
    refusals: list[dict[str, object]],
    layers: list[dict[str, object]],
) -> None:
    """Reconcile master, companion, artifact, and layer denominators."""
    source_counts = mapping(accountability.get("source_counts"), "source counts")
    global_count = nonnegative_integer(
        accountability.get("global_admitted_node_count"), "global admitted count"
    )
    projected_count = nonnegative_integer(
        accountability.get("projected_node_count"), "projected count"
    )
    excluded_count = nonnegative_integer(
        accountability.get("excluded_by_scope_count"), "excluded count"
    )
    if global_count != projected_count + excluded_count:
        raise ValueError("animal chronology projected count does not reconcile")
    if (
        nonnegative_integer(
            source_counts.get("admitted_node_count"), "source admitted count"
        )
        != global_count
    ):
        raise ValueError("animal chronology source admitted count differs")
    if nonnegative_integer(
        source_counts.get("refused_master_row_count"), "source refusal count"
    ) != len(refusals):
        raise ValueError("animal chronology source refusal count differs")
    master_count = nonnegative_integer(
        source_counts.get("sample_master_row_count"), "master count"
    )
    if master_count != global_count + len(refusals):
        raise ValueError("animal chronology master dispositions do not reconcile")
    refusal_counts = mapping(accountability.get("refusal_counts"), "refusal counts")
    experiment_count = nonnegative_integer(
        refusal_counts.get("sequencing_experiment_identity"),
        "sequencing experiment refusal count",
    )
    biological_count = master_count - experiment_count
    for field in ("sample_chronology_row_count", "sample_site_row_count"):
        if nonnegative_integer(source_counts.get(field), field) != biological_count:
            raise ValueError("animal chronology companion row counts do not reconcile")
    project_count = nonnegative_integer(
        source_counts.get("project_count"), "source project count"
    )
    input_identity = mapping(accountability.get("input_identity"), "input identity")
    artifact_count = nonnegative_integer(
        input_identity.get("artifact_count"), "input artifact count"
    )
    if artifact_count != 1 + (project_count * 3):
        raise ValueError("animal chronology project input inventory does not reconcile")
    if len(layers) != 6:
        raise ValueError("animal chronology publication requires six species layers")
    layer_keys = {nonblank_text(layer.get("key"), "layer key") for layer in layers}
    if len(layer_keys) != len(layers):
        raise ValueError("animal chronology layer identity is duplicated")
    layer_count = 0
    for layer in layers:
        features = mapping_rows(layer.get("features"), "layer features")
        declared = nonnegative_integer(layer.get("count"), "layer count")
        if declared != len(features):
            raise ValueError("animal chronology layer count differs from features")
        layer_count += declared
    if layer_count != projected_count:
        raise ValueError("animal chronology layer counts differ from projection")
