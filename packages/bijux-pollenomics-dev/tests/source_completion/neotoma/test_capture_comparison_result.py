"""Check the captured ABBO result against exact rational JSON source values."""

from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.generated_artifacts


def _unique(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(items)
    if len(result) != len(items):
        raise ValueError("Repeated source JSON member")
    return result


def _reject(token: str) -> Any:
    raise ValueError(f"Nonfinite source token: {token}")


def _rational_json(payload: bytes) -> dict[str, Any]:
    decoded = json.loads(
        payload,
        object_pairs_hook=_unique,
        parse_int=lambda token: ("integer", int(token)),
        parse_float=lambda token: ("fraction", Fraction(token)),
        parse_constant=_reject,
    )
    if not isinstance(decoded, dict):
        raise ValueError("An object source document is required")
    return decoded


def test_exact_rational_decoder_preserves_number_kind_and_sub_float_change() -> None:
    assert _rational_json(b'{"x":1.000000000000000001}') != _rational_json(b'{"x":1.0}')
    assert _rational_json(b'{"x":1}') != _rational_json(b'{"x":1.0}')
    assert _rational_json(b'{"x":1.00}') == _rational_json(b'{"x":1.0}')
    assert _rational_json(b'{"x":true}') != _rational_json(b'{"x":1}')
    assert _rational_json(b'{"x":[1,2]}') != _rational_json(b'{"x":[2,1]}')
    assert _rational_json(b'{"x":null}') != _rational_json(b'{"x":0}')
    with pytest.raises(ValueError, match="Repeated"):
        _rational_json(b'{"x":1,"x":2}')
    with pytest.raises(ValueError, match="object source"):
        _rational_json(b"[1]")
    with pytest.raises(ValueError, match="Nonfinite"):
        _rational_json(b'{"x":NaN}')


def test_saved_abbo_comparison_matches_raw_rational_values_and_entity_counts() -> None:
    repository = Path(__file__).resolve().parents[5]
    capture = (
        repository.parent
        / "-bijux-pollenomics-data/neotoma/dataset-19913/2026-10-26T185139Z"
    )
    output = repository / "artifacts/neotoma-capture-comparison/current-abbo"
    if not capture.is_dir() or not (output / "report.json").is_file():
        pytest.skip("The declared canonical ABBO capture and saved result are absent")
    manifest = (capture / "capture-manifest.json").read_bytes()
    assert sha256(manifest).hexdigest() == (
        "906f7e38d5c32d03f00094136ee89213ea39ea99eb422db233e723b8f4e79269"
    )
    raw = (capture / "dataset-19913.download.json").read_bytes()
    assert len(raw) == 632600
    assert sha256(raw).hexdigest() == (
        "1317496c2e1d04c7f69a2048ee49647350f5abfc0f8e23360211e01f5eb5dd8a"
    )
    prior = (
        repository / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json"
    ).read_bytes()
    assert sha256(prior).hexdigest() == (
        "d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435"
    )
    old_rows = [
        row
        for row in _rational_json(prior)["rows"]
        if row["site"]["collectionunit"]["dataset"]["datasetid"] == ("integer", 19913)
    ]
    current = _rational_json(raw)
    assert current["status"] == "success" and len(current["data"]) == 1
    assert len(old_rows) == 1 and old_rows[0] == current["data"][0]
    site = current["data"][0]["site"]
    unit = site["collectionunit"]
    dataset = unit["dataset"]
    assert site["siteid"] == ("integer", 13338)
    assert unit["collectionunitid"] == ("integer", 14910)
    assert unit["handle"] == "ABBO"
    samples = dataset["samples"]
    chronologies = unit["chronologies"]
    observations = [row for sample in samples for row in sample["datum"]]
    counts = {
        "sites": 1,
        "collection_units": 1,
        "datasets": 1,
        "samples": len(samples),
        "age_claims": sum(len(sample["ages"]) for sample in samples),
        "chronologies": len(chronologies),
        "chronology_controls": sum(
            len(row["chronology"]["chroncontrols"]) for row in chronologies
        ),
        "observations": len(observations),
    }
    assert counts == {
        "sites": 1,
        "collection_units": 1,
        "datasets": 1,
        "samples": 107,
        "age_claims": 107,
        "chronologies": 1,
        "chronology_controls": 7,
        "observations": 2892,
    }
    assert len({row["taxonid"] for row in observations}) == 94
    assert {row["units"] for row in observations} == {"NISP"}
    report = json.loads((output / "report.json").read_bytes())
    assert report["source_value_equal"] is True and report["changed_paths"] == 0
    assert json.loads((output / "changes.json").read_bytes()) == []
    for label in ("retained", "current"):
        result = report["captures"][label]
        assert result["conflicts"] == result["orphans"] == []
        assert result["native_preservation"]["match"] is True
        surfaces = result["native_preservation"]["surfaces"]
        assert set(surfaces) == set(counts)
        for name, count in counts.items():
            assert surfaces[name]["match"] is True
            assert (
                surfaces[name]["raw_rows"] == surfaces[name]["accepted_rows"] == count
            )
            assert (
                surfaces[name]["missing_rows"] == surfaces[name]["unexpected_rows"] == 0
            )
            assert surfaces[name]["conflict_variant_rows"] == 0
    assert report["historical_http_custody_recovered"] is False
    assert report["scientific_admission"] is False
