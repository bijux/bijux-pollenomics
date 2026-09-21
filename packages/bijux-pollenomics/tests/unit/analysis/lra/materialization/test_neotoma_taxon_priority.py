"""The priority join preserves source identity and refuses mismatched inputs."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization import (
    neotoma_taxon_priority as priority,
)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


class _Row:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    def payload(self) -> dict[str, Any]:
        return self.value


class _Evidence:
    manifest_bytes = b'{"build_id":"build","source_snapshot_id":"source"}'
    raw_files = (("manifest.json", "raw-manifest-digest"),)

    def __init__(self, rows: list[_Row]) -> None:
        self.source_rows = rows

    def assert_unchanged(self) -> None:
        pass

    def manifest(self) -> dict[str, str]:
        return json.loads(self.manifest_bytes)

    def rows(self, surface: str) -> list[_Row]:
        assert surface == "observations"
        return self.source_rows


def _inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[_Evidence, dict[str, Any], dict[str, Any]]:
    base = {
        "sample_id": "sample-1",
        "variable_id": "variable-1",
        "source_taxon_id": 1,
        "source_reported_name": "Named pollen type",
        "source_taxon_group": "tree",
        "source_ecological_group": "tree",
        "source_element": "pollen",
        "source_element_type": "pollen",
        "source_unit": "NISP",
        "unit_family": "count",
        "country_code": "SE",
    }
    source = {
        "source_family": "neotoma",
        "source_variable_id": "variable-1",
        **{field: base.get(field) for field in priority._IDENTITY_FIELDS[2:]},
        "classification_concept_id": "neotoma:classification-concept:one",
    }
    review = {
        "authority_role": "review_projection_not_canonical_classification",
        "scientific_admission_allowed": False,
        "source_summaries": {"neotoma": {"source_snapshot_id": "source"}},
        "row_count": 1,
        "rows": [
            {
                "source_family": "neotoma",
                "observation_count": 2,
                "review_row_id": source["classification_concept_id"],
                "source_identity_sha256": digest(source),
                "source_reported_name": "Named pollen type",
                "review_state": "needs_discussion",
                "supporting_evidence": source,
            }
        ],
    }
    review["bundle_sha256"] = digest(review)
    evidence = _Evidence([_Row(base), _Row({**base, "source_element_type": "spore"})])
    screen = {
        "schema_version": "neotoma-pollen-prerequisite-screen.v1",
        "source_snapshot_id": "source",
        "normalized_build_id": "build",
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "raw_manifest_sha256": "raw-manifest-digest",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "candidate_sample_ids": ["sample-1"],
        "candidate_sample_ids_sha256": hashlib.sha256(
            canonical_bytes(["sample-1"])
        ).hexdigest(),
        "sample_decisions": [
            {
                "sample_id": "sample-1",
                "country_code": "SE",
                "screen_status": "necessary_candidate",
                "pollen_count_observations": 1,
            }
        ],
        "screen_denominators": {"necessary_candidate_samples": 1},
    }

    class Accounting:
        selected_samples = frozenset({"sample-1"})

        @staticmethod
        def observation(row: _Row) -> dict[str, Any]:
            return {"count_status": "count_candidate"}

    monkeypatch.setattr(priority, "source_accounting", lambda *args: Accounting())
    return evidence, screen, review


def test_prioritizes_agreeing_pollen_and_never_admits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, screen, review = _inputs(monkeypatch)
    result = priority.prioritize_neotoma_candidate_taxa(evidence, screen, review)

    assert result["candidate_sample_count"] == 1
    assert result["candidate_pollen_observation_count"] == 1
    assert result["candidate_review_row_count"] == 1
    assert result["rows"][0]["candidate_country_observation_counts"] == {"SE": 1}
    assert result["rows"][0]["review_state"] == "needs_discussion"
    assert result["lra_accepted_samples"] == 0
    assert result["selected_review_state_counts"] == {"needs_discussion": 1}
    assert result["publication_allowed"] is False


def test_rejects_mismatched_screen_or_review(monkeypatch: pytest.MonkeyPatch) -> None:
    evidence, screen, review = _inputs(monkeypatch)
    changed_screen = deepcopy(screen)
    changed_screen["sample_decisions"][0]["pollen_count_observations"] += 1
    with pytest.raises(ValueError, match="Candidate pollen observations differ"):
        priority.prioritize_neotoma_candidate_taxa(evidence, changed_screen, review)
    changed_review = deepcopy(review)
    changed_review["rows"][0]["review_state"] = "accepted"
    with pytest.raises(ValueError, match="bundle digest differs"):
        priority.prioritize_neotoma_candidate_taxa(evidence, screen, changed_review)
    changed_review["bundle_sha256"] = digest(
        {key: value for key, value in changed_review.items() if key != "bundle_sha256"}
    )
    later = priority.prioritize_neotoma_candidate_taxa(evidence, screen, changed_review)
    assert later["selected_review_state_counts"] == {"accepted": 1}
    assert later["lra_accepted_samples"] == 0
    assert later["publication_allowed"] is False
    evidence.source_rows[0].value["country_code"] = "NO"
    with pytest.raises(ValueError, match="country differs from sample"):
        priority.prioritize_neotoma_candidate_taxa(evidence, screen, review)
