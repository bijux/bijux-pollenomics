"""Challenge semantic accounting, immutable identity and non-admitting review returns."""

import csv
import io
import json
from pathlib import Path
from typing import IO, Any, cast

import pytest

from bijux_pollenomics_dev.taxa_review.decisions import validate_decisions
from bijux_pollenomics_dev.taxa_review.rows import Occurrences, review_row
from bijux_pollenomics_dev.taxa_review.workflow import assemble, csv_bytes, write_review


def bundle() -> dict[str, Any]:
    row = review_row(
        row_id="native:1",
        source="fixture",
        native_id=1,
        label="Poaceae-type",
        domain="pollen",
        evidence={"source_unit": "count"},
    )
    contract = {
        "hierarchy": {
            "groups": [
                {"group_id": "open_ground", "subgroups": [{"subgroup_id": "grassland"}]}
            ]
        },
        "role_vocabulary": {
            "ecological_roles": ["open_ground"],
            "crop_evidence_roles": [],
        },
    }
    return assemble(
        [row],
        inputs=[{"path": "source.json", "sha256": "fixture"}],
        contract=contract,
        summaries={},
    )


def decision(payload: dict[str, Any]) -> dict[str, Any]:
    row = payload["rows"][0]
    return {
        "bundle_sha256": payload["bundle_sha256"],
        "decisions": [
            {
                "review_row_id": row["review_row_id"],
                "source_identity_sha256": row["source_identity_sha256"],
                "review_state": "accepted",
                "reviewer_id": "fixture-reviewer",
                "decision_date": "2026-09-12",
                "rationale": "Synthetic shape test, not actual scientific review",
                "evidence_reference_ids": ["fixture:1"],
                "proposed_primary_group_id": "open_ground",
                "proposed_primary_subgroup_id": "grassland",
                "proposed_role_ids": ["open_ground"],
            }
        ],
    }


def test_exact_unit_totals_keep_missing_zero_and_countries_distinct() -> None:
    counts = Occurrences()
    for index, (unit, value, country) in enumerate(
        [
            ("count", 0, "SE"),
            ("count", None, "SE"),
            ("count", 2, "DK"),
            ("percent", 25, "SE"),
            (None, 100, None),
            ("count", True, "SE"),
        ]
    ):
        counts.add("taxon", str(index), unit=unit, value=value, country=country)
    row: dict[str, Any] = {}
    counts.annotate(row, "taxon")
    assert row["observation_count"] == 6
    assert row["country_counts"] == {"DK": 1, "SE": 4, "UNASSIGNED": 1}
    assert [
        (value["source_unit"], value["country_code"], value["reported_value_sum"])
        for value in row["value_totals_by_exact_unit"]
    ] == [("count", "DK", "2"), ("count", "SE", "0"), ("percent", "SE", "25")]
    with pytest.raises(ValueError, match="Duplicate observation"):
        counts.add("other", "0", unit="count", value=7, country="FI")


def test_projection_is_deterministic_and_preserves_csv_null_and_qualifier(
    tmp_path: Path,
) -> None:
    payload = bundle()
    assert bundle() == payload
    assert not payload["scientific_admission_allowed"]
    parsed = list(csv.DictReader(io.StringIO(csv_bytes(payload["rows"]).decode())))[0]
    assert json.loads(parsed["source_reported_name"]) == "Poaceae-type"
    assert json.loads(parsed["proposed_primary_group_id"]) is None
    write_review(payload, tmp_path / "review")
    assert (
        json.loads((tmp_path / "review/completion.json").read_text())["bundle_sha256"]
        == payload["bundle_sha256"]
    )
    with pytest.raises(FileExistsError):
        write_review(payload, tmp_path / "review")


def test_duplicate_projection_rows_are_refused() -> None:
    payload = bundle()
    with pytest.raises(ValueError, match="Duplicate review"):
        assemble(payload["rows"] * 2, inputs=[], contract={}, summaries={})


def test_documented_acceptance_is_only_non_admitting_intent() -> None:
    payload = bundle()
    result = validate_decisions(payload, decision(payload))
    assert result["decision_count"] == 1
    assert not result["canonical_import_allowed"]
    assert not result["decisions"][0]["scientific_acceptance_verified"]
    assert payload["rows"][0]["review_state"] == "needs_discussion"


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_identity_sha256", "stale"),
        ("review_row_id", "unknown"),
        ("reviewer_id", None),
        ("decision_date", "2026-02-30"),
        ("evidence_reference_ids", []),
        ("proposed_primary_subgroup_id", "cereals"),
        ("proposed_role_ids", ["made-up"]),
        ("review_state", "admitted_public"),
    ],
)
def test_invalid_decision_is_refused(field: str, value: Any) -> None:
    payload = bundle()
    returned = decision(payload)
    returned["decisions"][0][field] = value
    with pytest.raises(ValueError):
        validate_decisions(payload, returned)


def test_tampered_bundle_and_duplicate_decisions_are_refused() -> None:
    payload = bundle()
    returned = decision(payload)
    returned["decisions"] *= 2
    with pytest.raises(ValueError, match="duplicate"):
        validate_decisions(payload, returned)
    payload["rows"][0]["source_reported_name"] = "Changed"
    with pytest.raises(ValueError, match="digest"):
        validate_decisions(payload, returned)


def test_exact_accounting_does_not_round_large_source_counts() -> None:
    counts = Occurrences()
    counts.add("taxon", "1", country="SE", unit="count", value=10**40)
    counts.add("taxon", "2", country="SE", unit="count", value=1)
    row: dict[str, Any] = {}
    counts.annotate(row, "taxon")
    assert row["value_totals_by_exact_unit"][0]["reported_value_sum"] == str(10**40 + 1)


def test_quarantine_retains_all_candidates_and_refuses_permission_promotion(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics_dev.source_completion.evidence import EvidenceReader
    from bijux_pollenomics_dev.taxa_review.quarantine import rootsi_rows

    payload = {
        "schema_version": "quarantined-rootsi-header-review.v1",
        "archive_sha256": "fixture",
        "publication_allowed": False,
        "derived_analysis_allowed": False,
        "workbooks": [{}],
        "headers": [
            {
                "archive_member": "source.xls",
                "sheet": "sheet",
                "column_index": 4,
                "source_header_candidates": [
                    {"row_index": 0, "value": "Site"},
                    {"row_index": 3, "value": "Poaceae-type"},
                ],
            }
        ],
    }
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(payload))
    rows, _ = rootsi_rows(EvidenceReader(tmp_path), "inventory.json")
    assert len(rows) == 1
    assert rows[0]["source_reported_name"] is None
    assert len(rows[0]["source_header_candidates"]) == 2
    assert rows[0]["observation_count"] is None
    assert not rows[0]["publication_allowed"]
    payload["publication_allowed"] = True
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="restrictions"):
        rootsi_rows(EvidenceReader(tmp_path), "inventory.json")


def test_occurrence_closure_refuses_omitted_source_or_country_rows() -> None:
    payload = bundle()
    rows = payload["rows"]
    rows[0].update(source_family="sead", observation_count=3, country_counts={"SE": 2})
    with pytest.raises(ValueError, match="Country occurrence"):
        assemble(
            rows, inputs=[], contract={}, summaries={"sead": {"observation_count": 3}}
        )
    rows[0]["country_counts"] = {"SE": 3}
    with pytest.raises(ValueError, match="source authority"):
        assemble(
            rows, inputs=[], contract={}, summaries={"sead": {"observation_count": 4}}
        )


def test_malformed_review_state_is_refused() -> None:
    payload = bundle()
    returned = decision(payload)
    returned["decisions"][0]["review_state"] = []
    with pytest.raises(ValueError, match="review state"):
        validate_decisions(payload, returned)


def test_publication_race_refuses_without_touching_other_owner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "review"
    original = Path.mkdir

    def competing(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == target:
            original(path)
            (path / "other-owner").write_text("keep")
        original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", competing)
    with pytest.raises(FileExistsError):
        write_review(bundle(), target)
    assert (target / "other-owner").read_text() == "keep"
    assert not (target / "completion.json").exists()


def test_partial_write_cannot_be_consumed_as_complete_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.taxa_review import read_review

    target = tmp_path / "review"
    original = Path.open

    def failed(path: Path, *args: Any, **kwargs: Any) -> IO[Any]:
        if path.name == "taxa-review.csv":
            raise OSError("fixture disk failure")
        return cast(IO[Any], original(path, *args, **kwargs))

    monkeypatch.setattr(Path, "open", failed)
    with pytest.raises(OSError, match="disk failure"):
        write_review(bundle(), target)
    assert target.is_dir()
    assert not (target / "completion.json").exists()
    with pytest.raises(ValueError, match="completion"):
        read_review(target)


def test_completed_reader_rejects_tampered_member(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.taxa_review import read_review

    target = tmp_path / "review"
    payload = bundle()
    write_review(payload, target)
    assert read_review(target) == payload
    (target / "taxa-review.csv").write_text("changed")
    with pytest.raises(ValueError, match="digest"):
        read_review(target)


def test_duplicate_return_keys_are_refused() -> None:
    from bijux_pollenomics_dev.taxa_review.decisions import load_review_json

    with pytest.raises(ValueError, match="Duplicate JSON"):
        load_review_json(b'{"decisions": [], "decisions": []}')


def test_missing_reference_directory_and_declared_file_refuse(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.evidence import EvidenceReader
    from bijux_pollenomics_dev.taxa_review.context import parameter_rows

    with pytest.raises(ValueError, match="missing"):
        parameter_rows(EvidenceReader(tmp_path))
    resources = (
        tmp_path / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources"
    )
    (resources / "data").mkdir(parents=True)
    (resources / "examples.py").write_text('DATASETS: tuple[str, ...] = ("one", "two")')
    (resources / "data/upstream_data_manifest.json").write_text(
        '{"one.rda": {}, "two.rda": {}}'
    )
    (resources / "data/one.json").write_text("{}")
    with pytest.raises(ValueError, match="inventory"):
        parameter_rows(EvidenceReader(tmp_path))


def test_null_empty_and_literal_unprovided_units_never_collide() -> None:
    counts = Occurrences()
    for i, unit in enumerate([None, "", "not_provided_by_source"]):
        counts.add("taxon", str(i), country="SE", unit=unit, value=5)
    row: dict[str, Any] = {}
    counts.annotate(row, "taxon")
    assert len(row["source_value_state_counts"]) == 3
    assert len(row["value_totals_by_exact_unit"]) == 1
    assert (
        row["value_totals_by_exact_unit"][0]["source_unit"] == "not_provided_by_source"
    )
