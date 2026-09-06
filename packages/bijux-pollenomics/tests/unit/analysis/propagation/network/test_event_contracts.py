"""Event identity, publication, and admission contracts."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.propagation.network import EventValidationError
from bijux_pollenomics.analysis.propagation.network.codec import _event_manifest_digest

from .support import event


def test_source_native_event_id_is_stable_and_preserves_zero() -> None:
    first = event("zero", younger_bp=0, older_bp=0)
    second = event("zero", younger_bp=0, older_bp=0)

    assert first.event_id == second.event_id
    assert first.interval is not None
    assert first.interval.younger_bp == 0
    assert first.as_dict()["observation_ids"] == ["observation-zero"]


def test_publication_schema_excludes_internal_identity_fields() -> None:
    baseline = event("identity")
    changed = replace(baseline, measurement_semantics_id="abundance.v1")

    assert baseline.as_dict() == changed.as_dict()
    assert _event_manifest_digest((baseline,)) != _event_manifest_digest((changed,))


@pytest.mark.parametrize(
    "overrides",
    (
        {"younger_bp": 100, "older_bp": 50},
        {"younger_bp": 100, "older_bp": None},
        {"younger_bp": -1, "older_bp": 50},
        {"subject_granularity": "site_midpoint"},
        {"feature_key": "taxon:"},
    ),
)
def test_invalid_or_presentation_level_events_are_refused(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(EventValidationError) as refusal:
        event("invalid", **overrides)  # type: ignore[arg-type]

    assert refusal.value.reason_code == "invalid_event_schema"
