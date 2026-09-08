"""Governed classification-audit vocabularies and output names."""

from __future__ import annotations

import re

COUNTRY_PARTITION = ("SE", "DK", "NO", "FI", "UNASSIGNED")
MAPPING_STATUSES = (
    "accepted",
    "accepted_qualified",
    "unmapped",
    "contested",
    "not_applicable",
    "refused",
)
ACCEPTED_STATUSES = frozenset({"accepted", "accepted_qualified"})
REVIEW_STATUSES = frozenset({"unmapped", "contested", "refused"})
ZERO_ACCEPTED_REASON_CODES = (
    "accepted_mapping_not_available",
    "mapping_evidence_not_available",
    "human_review_not_available",
)
OUTPUT_NAMES = (
    "accepted_mapping_queue.json",
    "concept_denominators.json",
    "country_partitions.json",
    "not_applicable_mapping_queue.json",
    "observation_memberships.json",
    "observation_denominators.json",
    "release_metadata.json",
    "review_queue.json",
    "unmapped_mapping_queue.json",
)
MANIFEST_NAME = "manifest.json"
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
