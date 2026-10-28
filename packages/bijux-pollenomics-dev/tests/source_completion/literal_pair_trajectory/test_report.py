"""Keep original-family allocation and refused source support in the actual writer."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.literal_pair_trajectory import report
from bijux_pollenomics_dev.source_completion.literal_pair_trajectory.source import (
    decode_sample,
)


@dataclass
class SavedInterval:
    """Source-free injected interval used to exercise writer coverage boundaries."""

    cover_lower: tuple[float, float] = (0.0, 0.0)
    cover_upper: tuple[float, float] = (1.0, 1.0)


def test_writer_allocates_all_native_objects_before_count_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()

    def raw(age: int, measured: bool = True) -> dict[str, Any]:
        return {
            "ages": [{"agetype": "Calibrated radiocarbon years BP", "age": age}],
            "datum": [
                {
                    "variablename": name,
                    "units": "NISP",
                    "elementtype": "pollen",
                    "value": value,
                }
                for name, value in [("Alnus", 1), ("Plantago lanceolata", 3)]
                if measured or name != "Alnus"
            ],
        }

    rows = [
        decode_sample(raw(1), "53995", "/a"),
        decode_sample(raw(6000), "53995", "/b"),
        decode_sample(raw(1, False), "54001", "/c"),
    ]
    monkeypatch.setattr(report, "read_population", lambda _: rows)
    confidences: list[float] = []

    def interval(*args: Any, **kwargs: Any) -> SavedInterval:
        confidences.append(kwargs["confidence_level"])
        return SavedInterval()

    monkeypatch.setattr(report, "fixed_two_taxon_counting_interval", interval)
    output = repository / "artifacts/result"
    report.produce(repository, output)
    result = json.loads((output / "report.json").read_bytes())
    assert result["family_native_sample_population"] == 3 and len(confidences) == 1
    assert 3 * (1 - Fraction.from_float(confidences[0])) <= Fraction(1, 20)
    assert result["coverage"][0]["all_native_samples"] == 2
    assert result["coverage"][0]["outside_declared_bins"] == 1
    assert result["coverage"][1]["admitted_samples"] == 0
    assert len(result["bins"]) == 26 and len(result["transitions"]) == 24
    assert not any(result["admissions"].values())
    journal = [
        json.loads(line)
        for line in (output / "interval-requests.jsonl").read_text().splitlines()
    ]
    assert (
        len(journal) == 2
        and journal[0]["request"]["family_native_sample_population"] == 3
    )
    with pytest.raises(ReportRebuildError, match="absent"):
        report.produce(repository, output)


def test_writer_refuses_artifact_escape_before_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "artifacts").mkdir()

    def forbidden(_: Path) -> list[dict[str, Any]]:
        raise AssertionError("Source must not be read")

    monkeypatch.setattr(report, "read_population", forbidden)
    with pytest.raises(ReportRebuildError, match="canonical"):
        report.produce(repository, repository / "artifacts/../outside")
