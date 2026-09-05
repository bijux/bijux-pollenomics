"""Exact-identity safeguards for animal point-evidence joins."""

from __future__ import annotations

from bijux_pollenomics.reporting.adna.foundation_outputs.repository import (
    _build_exact_evidence_lookup,
)


def test_exact_evidence_lookup_preserves_unique_sites_and_refuses_collisions() -> None:
    unique = {
        "project_accession": "single-site-project",
        "site_label": "Only Site",
        "political_entity": "Denmark",
        "source_locator": "unique-source",
    }
    duplicate_a = {
        "project_accession": "multi-site-project",
        "site_label": "Repeated Site",
        "political_entity": "Denmark",
        "source_locator": "first-source",
    }
    duplicate_b = {
        **duplicate_a,
        "source_locator": "second-source",
    }

    lookup = _build_exact_evidence_lookup([unique, duplicate_a, duplicate_b])

    assert lookup == {
        ("single-site-project", "Only Site", "Denmark"): unique,
    }
    assert ("multi-site-project", "Repeated Site", "Denmark") not in lookup
    assert ("multi-site-project", "Missing Site", "Denmark") not in lookup
