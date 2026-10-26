"""A captured source never silently becomes an admitted country value."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

import bijux_pollenomics_dev.source_completion.source_capability as capability
from bijux_pollenomics_dev.source_completion.source_capability import (
    _validate_status_counts,
    derive,
)

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture(scope="module")
def ledgers() -> tuple[dict[str, object], dict[str, object]]:
    stage = json.loads(
        (ROOT / "data/source_family_evidence_stage_matrix.json").read_text()
    )
    coverage = json.loads((ROOT / "data/country_dimension_coverage.json").read_text())
    return stage, coverage


def test_complete_cube_preserves_country_dimensions_and_null_counts(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = ledgers
    report = derive(stage, coverage)
    assert report["source_families"] == 11
    assert report["country_entries"] and len(report["country_entries"]) == 66
    assert report["country_cells"] == 198
    entries = {
        (row["source_family"], row["country_code"]): row
        for row in report["country_entries"]
    }
    hyde = entries["hyde", "SE"]["dimensions"]
    assert {value["availability_status"] for value in hyde.values()} == {"blocked"}
    assert all(
        all(number is None for number in value["counts"].values())
        for value in hyde.values()
    )
    sead = entries["sead", "SE"]["dimensions"]
    assert sead["source_reported"]["counts"]["sites"] == 0
    assert sead["publication"]["counts"]["sites"] == 1925
    assert sead["source_reported"]["availability_status"] == "zero_observations"


def native_profile() -> dict[str, object]:
    return {
        "source_id": "raa/lamningar-v1",
        "status": "admitted_source_context",
        "evidence_role": "source_context_only",
        "source_record_count": 764383,
        "scientific_admission": False,
        "chronology_admission": False,
        "event_admission": False,
        "legacy_density_admission": False,
        "publication_admission": False,
        "archaeological_interpretation_admission": False,
    }


def test_native_context_profile_survives_without_changing_country_or_legacy_fields(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    baseline = derive(stage, coverage)
    rows = stage["rows"]
    assert isinstance(rows, list)
    source = next(row for row in rows if row["source_key"] == "raa")
    source["source_context_profile"] = native_profile()
    result = derive(stage, coverage)
    assert result["country_entries"] == baseline["country_entries"]
    native = next(
        row for row in result["source_stages"] if row["source_family"] == "raa"
    )
    profile = native.pop("source_context_profile")
    assert profile == native_profile()
    previous = next(
        row for row in baseline["source_stages"] if row["source_family"] == "raa"
    )
    previous.pop("source_context_profile", None)
    assert native == previous
    profile["source_record_count"] = 0
    assert source["source_context_profile"]["source_record_count"] == 764383


@pytest.mark.parametrize(
    "field,value",
    [
        ("scientific_admission", True),
        ("chronology_admission", True),
        ("publication_admission", True),
        ("legacy_density_admission", True),
        ("evidence_role", "pollen_observation"),
        ("source_id", "raa/unknown"),
        ("source_record_count", True),
    ],
)
def test_native_context_profile_cannot_promote_interpretation_or_false_count(
    ledgers: tuple[dict[str, object], dict[str, object]], field: str, value: object
) -> None:
    stage, coverage = deepcopy(ledgers)
    rows = stage["rows"]
    assert isinstance(rows, list)
    profile = native_profile()
    profile[field] = value
    next(row for row in rows if row["source_key"] == "raa")[
        "source_context_profile"
    ] = profile
    with pytest.raises(ValueError, match="native source context"):
        derive(stage, coverage)


def test_duplicate_country_cell_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    cells[-1] = cells[0]
    with pytest.raises(ValueError, match="Cartesian"):
        derive(stage, coverage)


def test_negative_count_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    cells[0]["counts"]["sites"] = -1
    with pytest.raises(ValueError, match="counts invalid"):
        derive(stage, coverage)


def test_missing_source_stage_refuses(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    rows = stage["rows"]
    assert isinstance(rows, list)
    rows.pop()
    with pytest.raises(ValueError, match="denominator"):
        derive(stage, coverage)


def test_country_consumer_rejects_numeric_zero_in_blocked_cell(
    ledgers: tuple[dict[str, object], dict[str, object]],
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    blocked = next(cell for cell in cells if cell["availability_status"] == "blocked")
    blocked["counts"]["sites"] = 0
    with pytest.raises(ValueError, match="blocked country coverage"):
        derive(stage, coverage)


@pytest.mark.parametrize(
    ("family", "incorrect_role"),
    [
        ("landclim", "observation"),
        ("sead", "pollen_observation"),
        ("raa", "pollen_observation"),
        ("hyde", "observed_vegetation"),
    ],
)
def test_context_and_model_roles_cannot_become_observations(
    ledgers: tuple[dict[str, object], dict[str, object]],
    family: str,
    incorrect_role: str,
) -> None:
    stage, coverage = deepcopy(ledgers)
    rows = stage["rows"]
    assert isinstance(rows, list)
    next(row for row in rows if row["source_key"] == family)["evidence_role"] = (
        incorrect_role
    )
    with pytest.raises(ValueError, match=f"Source evidence role changed: {family}"):
        derive(stage, coverage)


@pytest.mark.parametrize("country", ["DK", "NO", "FI"])
def test_national_raa_cannot_become_nordic_publication(
    ledgers: tuple[dict[str, object], dict[str, object]], country: str
) -> None:
    stage, coverage = deepcopy(ledgers)
    cells = coverage["cells"]
    assert isinstance(cells, list)
    cell = next(
        item
        for item in cells
        if item["source_family"] == "raa"
        and item["country_code"] == country
        and item["country_dimension"] == "publication"
    )
    cell["availability_status"] = "zero_observations"
    cell["counts"]["sites"] = 0
    with pytest.raises(
        ValueError, match=f"National RAÄ country scope changed: {country}"
    ):
        derive(stage, coverage)


@pytest.mark.parametrize(
    ("status", "counts", "reason"),
    [
        ("zero_observations", {"sites": None}, "requires only observed zeros"),
        ("zero_observations", {"sites": 1}, "requires only observed zeros"),
        ("blocked", {"sites": 0}, "must not carry numeric counts"),
        ("not_available_from_source", {"sites": 0}, "must not carry numeric counts"),
        ("not_applicable", {"sites": 0}, "must not carry numeric counts"),
        ("available_not_collected", {"sites": 0}, "must not carry numeric counts"),
        ("unresolved", {"sites": None}, "requires source counts"),
        ("unknown", {"sites": None}, "Unknown country coverage"),
    ],
)
def test_availability_status_refuses_false_numeric_claims(
    status: str, counts: dict[str, int | None], reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        _validate_status_counts(status, counts)


@pytest.mark.parametrize(
    ("status", "counts"),
    [
        ("zero_observations", {"sites": 0, "observations": None}),
        ("blocked", {"sites": None}),
        ("available_not_collected", {"sites": None}),
        ("unresolved", {"sites": 7, "accepted_records": 0}),
    ],
)
def test_availability_status_preserves_distinct_valid_states(
    status: str, counts: dict[str, int | None]
) -> None:
    _validate_status_counts(status, counts)


def test_changed_country_parent_refuses_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    data = repository / "data"
    data.mkdir(parents=True)
    (repository / "artifacts").mkdir()
    (data / "source_family_evidence_stage_matrix.json").write_text("{}\n")
    parent = data / "source.json"
    original = b'{"claim":"present"}\n'
    parent.write_bytes(original)
    (data / "country_dimension_coverage.json").write_text(
        json.dumps(
            {
                "input_artifacts": [
                    {
                        "path": "data/source.json",
                        "byte_count": len(original),
                        "sha256": hashlib.sha256(original).hexdigest(),
                    }
                ]
            }
        )
    )

    def change_parent_during_derivation(
        _stage: dict[str, object], _coverage: dict[str, object]
    ) -> dict[str, object]:
        parent.write_text('{"claim":"altered"}\n')
        return {"source_families": 11}

    monkeypatch.setattr(capability, "derive", change_parent_during_derivation)
    output = repository / "artifacts" / "source-capability"
    with pytest.raises(ValueError, match="Country coverage parent changed"):
        capability.run(repository, output)
    assert not output.exists()


def test_country_parent_cannot_escape_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    data = repository / "data"
    data.mkdir(parents=True)
    (repository / "artifacts").mkdir()
    (data / "source_family_evidence_stage_matrix.json").write_text("{}\n")
    external = tmp_path / "external.json"
    external.write_text("{}\n")
    (data / "country_dimension_coverage.json").write_text(
        json.dumps(
            {
                "input_artifacts": [
                    {
                        "path": "../../external.json",
                        "byte_count": external.stat().st_size,
                        "sha256": hashlib.sha256(external.read_bytes()).hexdigest(),
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(capability, "derive", lambda *_: {"source_families": 11})
    output = repository / "artifacts" / "source-capability"
    with pytest.raises(ValueError, match="Country coverage parent identity invalid"):
        capability.run(repository, output)
    assert not output.exists()
