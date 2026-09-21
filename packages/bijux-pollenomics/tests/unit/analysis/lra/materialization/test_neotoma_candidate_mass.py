"""Source counts retain label, unit and observed-zero boundaries."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.materialization import (
    neotoma_candidate_mass as mass,
)
from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes


class _Row:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

    def payload(self) -> dict[str, Any]:
        return self.value

    def locator(self) -> dict[str, int]:
        return {"row": 1}


class _Evidence:
    manifest_bytes = b'{"build_id":"build","source_snapshot_id":"source"}'
    raw_files = (("manifest.json", "raw-manifest"),)

    def __init__(self, rows: list[_Row]) -> None:
        self.source_rows = rows

    def assert_unchanged(self) -> None:
        pass

    def manifest(self) -> dict[str, str]:
        return json.loads(self.manifest_bytes)

    def rows(self, surface: str) -> list[_Row]:
        assert surface == "observations"
        return self.source_rows


def _inputs(monkeypatch: pytest.MonkeyPatch) -> tuple[_Evidence, dict[str, Any]]:
    def row(value: int | None, unit: str, element: str | None) -> _Row:
        return _Row(
            {
                "sample_id": "sample-1",
                "country_code": "SE",
                "source_unit": unit,
                "source_element": element,
                "source_element_type": element,
                "source_value": value,
            }
        )

    evidence = _Evidence(
        [
            row(0, "NISP", "pollen"),
            row(7, "NISP", "pollen"),
            row(3, "NISP", "spore"),
            row(5, "other count", None),
            row(1, "other count", "pollen"),
            row(None, "NISP", "pollen"),
        ]
    )
    ids = ["sample-1"]
    screen = {
        "schema_version": "neotoma-pollen-prerequisite-screen.v1",
        "source_snapshot_id": "source",
        "normalized_build_id": "build",
        "normalized_manifest_sha256": hashlib.sha256(
            evidence.manifest_bytes
        ).hexdigest(),
        "raw_manifest_sha256": "raw-manifest",
        "lra_accepted_samples": 0,
        "executable_request": None,
        "candidate_sample_ids": ids,
        "candidate_sample_ids_sha256": hashlib.sha256(canonical_bytes(ids)).hexdigest(),
        "screen_denominators": {"necessary_candidate_samples": 1},
        "sample_decisions": [
            {
                "sample_id": "sample-1",
                "country_code": "SE",
                "source_locator": {"row": 1},
                "screen_status": "necessary_candidate",
                "observation_count": 6,
                "count_candidate_observations": 5,
                "pollen_count_observations": 3,
            }
        ],
    }

    class Accounting:
        selected_samples = frozenset(ids)
        indexes = {"samples": {"sample-1": _Row({})}}

        @staticmethod
        def observation(source: _Row) -> dict[str, Any]:
            value = source.payload()["source_value"]
            return {
                "source_observation": source.payload(),
                "count_status": "refused" if value is None else "count_candidate",
                "typed_count": value,
            }

    monkeypatch.setattr(mass, "source_accounting", lambda *args: Accounting())
    return evidence, screen


def test_observed_mass_keeps_units_labels_and_zero_separate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, screen = _inputs(monkeypatch)
    result = mass.assess_neotoma_candidate_count_mass(evidence, screen)
    sample = result["sample_rows"][0]
    units = {part["source_unit"]: part for part in sample["source_unit_partitions"]}
    assert sample["observations"] == 6
    assert sample["refused_count_observations"] == 1
    assert sample["pollen_count_observations"] == 3
    assert units["NISP"]["pollen_exact_count_sum"] == 7
    assert units["NISP"]["pollen_observed_zero_observations"] == 1
    assert units["NISP"]["nonpollen_exact_count_sum"] == 3
    assert units["NISP"]["unresolved_label_exact_count_sum"] == 0
    assert units["other count"]["pollen_exact_count_sum"] == 1
    assert units["other count"]["unresolved_label_exact_count_sum"] == 5
    assert units["other count"]["nonpollen_exact_count_sum"] == 0
    assert units["other count"]["pollen_observed_zero_observations"] == 0
    assert result["country_denominators"]["SE"]["candidate_samples"] == 1
    assert result["country_denominators"]["DK"]["candidate_samples"] == 0
    assert result["country_denominators"]["DK"]["observations"] == 0
    assert result["country_denominators"]["DK"]["pollen_count_observations"] == 0
    assert sample["unresolved_label_count_observations"] == 1
    assert result["known_compatible_pollen_denominator_status"] == "not_evaluated"
    assert result["lra_accepted_samples"] == 0
    assert result["publication_allowed"] is False


def test_changed_screen_and_country_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evidence, screen = _inputs(monkeypatch)
    wrong = deepcopy(screen)
    wrong["sample_decisions"][0]["pollen_count_observations"] = 4
    with pytest.raises(ValueError, match="differs from source screen"):
        mass.assess_neotoma_candidate_count_mass(evidence, wrong)
    wrong = deepcopy(screen)
    wrong["sample_decisions"][0]["source_locator"] = {"row": 2}
    with pytest.raises(ValueError, match="locator differs from source"):
        mass.assess_neotoma_candidate_count_mass(evidence, wrong)
    evidence.source_rows[0].value["country_code"] = "NO"
    with pytest.raises(ValueError, match="country differs from sample"):
        mass.assess_neotoma_candidate_count_mass(evidence, screen)
