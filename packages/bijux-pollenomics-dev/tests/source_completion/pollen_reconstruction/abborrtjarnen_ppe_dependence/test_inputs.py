"""Native missingness, point-age and exact parameter-label safeguards."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.inputs import (
    native_counts,
    panel_inputs,
    source_age,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    bound_files,
    parameter_rows,
)


def _sample(number: int, age: float, counts: list[int] | None = None) -> dict[str, Any]:
    return {
        "sampleid": number,
        "depth": number,
        "ages": [
            {
                "age": age,
                "chronologyid": 11516,
                "agetype": "Calibrated radiocarbon years BP",
                "ageyounger": None,
                "ageolder": None,
            }
        ],
        "datum": [
            {
                "variablename": name,
                "taxonid": taxon,
                "value": value,
                "units": "NISP",
                "element": "pollen",
                "elementtype": "pollen",
            }
            for name, taxon, value in zip(
                TAXA, TAXON_IDS, [1] * 5 if counts is None else counts, strict=True
            )
        ],
    }


def test_literal_zero_is_present_and_missing_is_not_zero() -> None:
    sample = _sample(1, -52, [1, 0, 2, 3, 4])
    assert native_counts(sample)["vector"] == [1, 0, 2, 3, 4]
    sample["datum"].pop(1)
    result = native_counts(sample)
    assert result["vector"] is None and result["missing"] == ["Cyperaceae"]
    assert result["panel_subtotal"] == result["all_nisp"] == 10


@pytest.mark.parametrize("value", [True, 1.5, -1, "1"])
def test_noninteger_or_signed_count_is_refused(value: Any) -> None:
    sample = _sample(1, 100)
    sample["datum"][0]["value"] = value
    with pytest.raises(ValueError, match="nonnegative integer"):
        native_counts(sample)


def test_duplicate_or_renamed_native_concept_requires_a_decision() -> None:
    sample = _sample(1, 100)
    sample["datum"].append(dict(sample["datum"][0]))
    with pytest.raises(ValueError, match="Duplicate"):
        native_counts(sample)
    sample = _sample(1, 100)
    sample["datum"][0]["taxonid"] = 999
    with pytest.raises(ValueError, match="concept pairing"):
        native_counts(sample)


def test_signed_source_age_is_retained_and_wrong_basis_is_refused() -> None:
    sample = _sample(1, -52)
    assert source_age(sample) == sample["ages"][0]
    sample["ages"][0]["agetype"] = "Radiocarbon years BP"
    assert source_age(sample) is None
    sample["ages"][0]["agetype"] = "Calibrated radiocarbon years BP"
    sample["ages"].append(dict(sample["ages"][0]))
    assert source_age(sample) is None


def test_four_frozen_windows_preserve_every_source_sample_and_omitted_mass() -> None:
    ages = (
        [-52.0]
        + [1501.0] * 7
        + [2001.0] * 9
        + [2501.0] * 8
        + [4501.0] * 5
        + [9000.0] * 77
    )
    samples = [_sample(i, age) for i, age in enumerate(ages)]
    samples[1]["datum"].append(
        {
            "variablename": "Other pollen",
            "taxonid": 999,
            "value": 3,
            "units": "NISP",
            "element": "pollen",
            "elementtype": "pollen",
        }
    )
    unit = {
        "dataset": {"samples": samples},
        "chronologies": [
            {
                "chronology": {
                    "chronologyid": 11516,
                    "chronology": {"modelagetype": "Calibrated radiocarbon years BP"},
                }
            }
        ],
    }
    sources = {"site": {"collectionunit": unit}, "parameter_labels": set(TAXA)}
    result = panel_inputs(sources)
    assert len(result["sample_account"]) == 107
    assert [len(w["sample_ids"]) for w in result["windows"]] == [7, 9, 8, 5]
    assert result["windows"][0]["omitted_reported_pollen_nisp"] == 3
    assert result["sample_account"][0]["source_age_bp"] == -52
    assert result["sample_account"][0]["status"] == "outside_requested_windows"
    samples[1]["datum"].pop(0)
    with pytest.raises(ValueError, match="population differs"):
        panel_inputs(sources)


def _parameter_csv() -> bytes:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Plant taxa/Pollen-morphological types", "PPE (SD)", "FSP (m/s)"])
    for name in [*TAXA[:-1], *[f"other {i}" for i in range(26)], TAXA[-1]]:
        writer.writerow([name, "1 (0)" if name == "Poaceae" else "2 (0.1)", "0.02"])
    return stream.getvalue().encode()


def test_public_sd_tokens_are_not_rescaled_and_reference_sd_stays_zero() -> None:
    parameters, labels = parameter_rows(_parameter_csv())
    assert len(labels) == 31 and [p["published_sd"] for p in parameters] == [
        0.1
    ] * 4 + [0]
    with pytest.raises(ValueError, match="uncertainty header"):
        parameter_rows(_parameter_csv().replace(b"PPE (SD)", b"PPE (SEM)"))
    with pytest.raises(ValueError, match="Literal source parameter"):
        parameter_rows(_parameter_csv().replace(b"Betula,", b"Betula-type,"))


def test_external_source_byte_changes_and_escape_are_refused(tmp_path: Path) -> None:
    body = b"original"
    (tmp_path / "source").write_bytes(body)
    declaration = {
        "source": {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
    }
    assert bound_files(tmp_path, declaration) == {"source": body}
    (tmp_path / "source").write_bytes(b"changed!")
    with pytest.raises(ValueError, match="Changed source"):
        bound_files(tmp_path, declaration)
    with pytest.raises(ValueError, match="Invalid source locator"):
        bound_files(tmp_path, {"../source": declaration["source"]})
