from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import cast

import pytest

from bijux_pollenomics.data_downloader.sources.sead.evidence_reader import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
import bijux_pollenomics.governance.country_coverage as country_coverage_module
from bijux_pollenomics.governance.country_coverage import (
    CELL_SCHEMA_ID,
    COUNT_FIELDS,
    COUNTRIES,
    COUNTRY_DIMENSIONS,
    SOURCE_FAMILIES,
    build_country_dimension_coverage_ledger,
    write_country_dimension_coverage_ledger,
)

_READ_BYTES = Path.read_bytes

_REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
_CELL_SCHEMA_PATH = (
    _REPOSITORY_ROOT.parent
    / "bijux-pollenomics-execution-control/contracts/country-coverage.schema.json"
)
_LEDGER_PATH = _REPOSITORY_ROOT / "data/country_dimension_coverage.json"
_SEAD_ACQUISITION_ROOT = f"data/sead/raw/acquisitions/{SEAD_GOVERNED_EVIDENCE_RUN_ID}"
_SEAD_ADMISSION_PATH = f"{_SEAD_ACQUISITION_ROOT}/admission.json"
_SEAD_DECISIONS_PATH = f"{_SEAD_ACQUISITION_ROOT}/country-decisions.json"
_SEAD_SITES_PATH = f"{_SEAD_ACQUISITION_ROOT}/payloads/tbl_sites.json"
_COUNTRY_COVERAGE_ARTIFACT_ROOT = (
    _REPOSITORY_ROOT / "artifacts/execution-control/country-coverage"
)


def _build() -> dict[str, object]:
    return build_country_dimension_coverage_ledger(
        _REPOSITORY_ROOT, cell_schema_path=_CELL_SCHEMA_PATH
    )


def _replace_input_document(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    mutate: Callable[[dict[str, object]], None],
) -> bytes:
    target = (_REPOSITORY_ROOT / relative_path).resolve()
    original = _READ_BYTES(target)
    document = cast(dict[str, object], json.loads(original))
    mutate(document)
    replacement = (
        json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n"
    ).encode("utf-8")

    def read_bytes(path: Path) -> bytes:
        if path.resolve() == target:
            return replacement
        return _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    return original


def _replace_input_documents(
    monkeypatch: pytest.MonkeyPatch, replacements: Mapping[str, bytes]
) -> None:
    targets = {
        (_REPOSITORY_ROOT / relative_path).resolve(): payload
        for relative_path, payload in replacements.items()
    }

    def read_bytes(path: Path) -> bytes:
        target = path.resolve()
        return targets[target] if target in targets else _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)


def _document_bytes(document: Mapping[str, object]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n"
    ).encode("utf-8")


def _set_nested(
    document: dict[str, object], path: tuple[str, ...], value: object
) -> None:
    current = document
    for key in path[:-1]:
        current = cast(dict[str, object], current[key])
    current[path[-1]] = value


def _cells(ledger: Mapping[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], ledger["cells"])


def _cell(
    ledger: Mapping[str, object], source: str, dimension: str, country: str
) -> dict[str, object]:
    matches = [
        cell
        for cell in _cells(ledger)
        if (
            cell["source_family"],
            cell["country_dimension"],
            cell["country_code"],
        )
        == (source, dimension, country)
    ]
    assert len(matches) == 1
    return matches[0]


def _counts(cell: Mapping[str, object]) -> Mapping[str, int | None]:
    return cast(Mapping[str, int | None], cell["counts"])


def _measure_total(
    ledger: Mapping[str, object],
    source: str,
    dimension: str,
    measure: str,
    *,
    countries: tuple[str, ...] = COUNTRIES,
) -> int:
    values = [
        _counts(_cell(ledger, source, dimension, country))[measure]
        for country in countries
    ]
    assert all(value is not None for value in values)
    return sum(cast(list[int], values))


def test_ledger_has_one_schema_valid_cell_per_complete_partition() -> None:
    ledger = _build()
    cells = _cells(ledger)

    assert ledger["cell_count"] == 144
    assert len(cells) == len(SOURCE_FAMILIES) * len(COUNTRY_DIMENSIONS) * len(COUNTRIES)
    assert {
        (
            cell["source_family"],
            cell["country_dimension"],
            cell["country_code"],
        )
        for cell in cells
    } == {
        (source, dimension, country)
        for source in SOURCE_FAMILIES
        for dimension in COUNTRY_DIMENSIONS
        for country in COUNTRIES
    }
    assert all(set(_counts(cell)) == set(COUNT_FIELDS) for cell in cells)
    assert all(cell["availability_status"] != "unknown" for cell in cells)
    assert all(
        cell["country_assignment_method"] is None
        if cell["country_dimension"] == "source_reported"
        else isinstance(cell["country_assignment_method"], str)
        for cell in cells
    )
    schema_bytes = _CELL_SCHEMA_PATH.read_bytes()
    assert ledger["cell_schema_sha256"] == hashlib.sha256(schema_bytes).hexdigest()
    assert json.loads(schema_bytes)["$id"] == ledger["cell_schema_id"]


def test_landclim_keeps_reported_country_separate_from_publication() -> None:
    ledger = _build()
    reported = {
        country: _counts(_cell(ledger, "landclim", "source_reported", country))["sites"]
        for country in COUNTRIES
    }
    published = {
        country: _counts(_cell(ledger, "landclim", "publication", country))["sites"]
        for country in COUNTRIES
    }

    assert reported == {
        "SE": 163,
        "DK": 127,
        "NO": 84,
        "FI": 62,
        "UNASSIGNED": 54,
        "OUTSIDE": 0,
    }
    assert published == {
        "SE": 198,
        "DK": 127,
        "NO": 93,
        "FI": 72,
        "UNASSIGNED": 0,
        "OUTSIDE": 0,
    }
    unassigned = _cell(ledger, "landclim", "source_reported", "UNASSIGNED")
    assert unassigned["availability_status"] == "available_partial"
    assert "source_country_not_reported" in cast(list[str], unassigned["reason_codes"])
    governed = _cell(ledger, "landclim", "governed_assignment", "SE")
    assert governed["availability_status"] == "blocked"
    assert all(value is None for value in _counts(governed).values())


def test_neotoma_dimensions_reconcile_without_collapsing_country_identity() -> None:
    ledger = _build()
    observed_partitions = ("SE", "DK", "NO", "FI", "UNASSIGNED")

    assert _measure_total(ledger, "neotoma", "source_reported", "sites") == 200
    assert _measure_total(ledger, "neotoma", "governed_assignment", "sites") == 200
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "accepted_records")
        == 193
    )
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "unresolved_records")
        == 7
    )
    assert (
        _measure_total(ledger, "neotoma", "governed_assignment", "excluded_records")
        == 0
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "datasets",
            countries=observed_partitions,
        )
        == 209
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "collection_units",
            countries=observed_partitions,
        )
        == 206
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "samples",
            countries=observed_partitions,
        )
        == 12_388
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "age_claims",
            countries=observed_partitions,
        )
        == 23_281
    )
    assert (
        _measure_total(
            ledger,
            "neotoma",
            "governed_assignment",
            "observations",
            countries=observed_partitions,
        )
        == 370_936
    )
    assert _measure_total(ledger, "neotoma", "publication", "sites") == 200
    assert _counts(_cell(ledger, "neotoma", "source_reported", "SE"))["sites"] == 101
    assert _counts(_cell(ledger, "neotoma", "governed_assignment", "SE"))["sites"] == 98
    assert _counts(_cell(ledger, "neotoma", "publication", "SE"))["sites"] == 99
    unassigned = _cell(ledger, "neotoma", "governed_assignment", "UNASSIGNED")
    assert _counts(unassigned)["unresolved_records"] == 7
    assert unassigned["availability_status"] == "unresolved"
    assert unassigned["lifecycle_status"] == "review_required"


def test_sead_preserves_assigned_review_and_refused_partitions() -> None:
    ledger = _build()
    source_unassigned = _cell(ledger, "sead", "source_reported", "UNASSIGNED")
    assert _counts(source_unassigned)["received_records"] == 2_195
    assert source_unassigned["availability_status"] == "available_partial"

    expected = {
        "SE": 1_925,
        "DK": 59,
        "NO": 45,
        "FI": 40,
        "UNASSIGNED": 103,
        "OUTSIDE": 23,
    }
    assert {
        country: _counts(_cell(ledger, "sead", "governed_assignment", country))["sites"]
        for country in COUNTRIES
    } == expected
    assert sum(expected.values()) == 2_195
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "accepted_records")
        == 2_069
    )
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "unresolved_records")
        == 103
    )
    assert (
        _measure_total(ledger, "sead", "governed_assignment", "excluded_records") == 23
    )
    assert _measure_total(ledger, "sead", "governed_assignment", "age_claims") == 25_109
    review = _cell(ledger, "sead", "governed_assignment", "UNASSIGNED")
    refused = _cell(ledger, "sead", "governed_assignment", "OUTSIDE")
    assert _counts(review)["unresolved_records"] == 103
    assert review["lifecycle_status"] == "review_required"
    assert _counts(refused)["excluded_records"] == 23
    assert refused["lifecycle_status"] == "refused"
    for country, site_count, claim_count in (
        ("SE", 1_925, 22_643),
        ("DK", 59, 1_939),
        ("NO", 45, 468),
        ("FI", 40, 59),
    ):
        publication = _cell(ledger, "sead", "publication", country)
        assert publication["availability_status"] == "available_collected"
        assert publication["lifecycle_status"] == "admitted"
        assert _counts(publication)["sites"] == site_count
        assert _counts(publication)["published_records"] == site_count
        assert _counts(publication)["age_claims"] == claim_count
    for country in ("UNASSIGNED", "OUTSIDE"):
        publication = _cell(ledger, "sead", "publication", country)
        assert publication["availability_status"] == "zero_observations"
        assert publication["lifecycle_status"] == "admitted"
        assert _counts(publication)["sites"] == 0
        assert _counts(publication)["age_claims"] == 0


def test_source_specific_absence_and_review_are_not_encoded_as_zero() -> None:
    ledger = _build()

    for source in ("raa", "svar"):
        sweden = _cell(ledger, source, "publication", "SE")
        denmark = _cell(ledger, source, "publication", "DK")
        assert sweden["availability_status"] == "blocked"
        assert sweden["lifecycle_status"] == "refused"
        assert denmark["availability_status"] == "not_available_from_source"
        assert denmark["lifecycle_status"] == "unavailable"
        assert all(
            value is None
            for dimension in COUNTRY_DIMENSIONS
            for country in COUNTRIES
            for value in _counts(_cell(ledger, source, dimension, country)).values()
        )

    for dimension in COUNTRY_DIMENSIONS:
        for country in ("SE", "DK", "NO", "FI"):
            boundary = _cell(ledger, "boundaries", dimension, country)
            assert boundary["lifecycle_status"] == "review_required"
    assert _measure_total(ledger, "boundaries", "publication", "published_records") == 4

    nordic_countries = ("SE", "DK", "NO", "FI")
    assert (
        _measure_total(
            ledger,
            "aadr",
            "publication",
            "samples",
            countries=nordic_countries,
        )
        == 1_231
    )
    assert (
        _measure_total(
            ledger,
            "aadr",
            "publication",
            "sites",
            countries=nordic_countries,
        )
        == 447
    )
    assert all(
        _cell(ledger, "aadr", "publication", country)["lifecycle_status"]
        == "review_required"
        for country in COUNTRIES
    )
    assert all(
        value is None
        for dimension in ("source_reported", "governed_assignment")
        for country in COUNTRIES
        for value in _counts(_cell(ledger, "aadr", dimension, country)).values()
    )

    assert (
        _measure_total(
            ledger,
            "animal_adna",
            "publication",
            "samples",
            countries=nordic_countries,
        )
        == 3
    )
    assert _counts(_cell(ledger, "animal_adna", "publication", "NO"))["samples"] == 0
    assert _counts(_cell(ledger, "animal_adna", "publication", "FI"))["samples"] == 0


def test_duplicate_source_stage_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows.append(deepcopy(rows[0]))

    _replace_input_document(
        monkeypatch, "data/source_family_evidence_stage_matrix.json", duplicate
    )

    with pytest.raises(ValueError, match="duplicate source keys"):
        _build()


def test_duplicate_json_object_key_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    document = cast(dict[str, object], json.loads(_READ_BYTES(target)))
    replacement = (
        b'{"source_hashes":{},"source_hashes":'
        + json.dumps(document["source_hashes"]).encode("utf-8")
        + b"}"
    )

    def read_bytes(path: Path) -> bytes:
        return replacement if path.resolve() == target else _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)

    with pytest.raises(ValueError, match="duplicate JSON key: source_hashes"):
        _build()


def test_duplicate_landclim_reported_country_label_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate_label(document: dict[str, object]) -> None:
        features = cast(list[dict[str, object]], document["features"])
        for feature in features:
            properties = cast(dict[str, object], feature["properties"])
            popup_rows = cast(list[dict[str, object]], properties["popup_rows"])
            reported = next(
                (row for row in popup_rows if row.get("label") == "Reported country"),
                None,
            )
            if reported is not None:
                popup_rows.append(deepcopy(reported))
                return
        raise AssertionError("fixture has no Reported country row")

    _replace_input_document(
        monkeypatch,
        "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
        duplicate_label,
    )

    with pytest.raises(ValueError, match="duplicate Reported country labels"):
        _build()


def test_unknown_neotoma_country_partition_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def add_unknown_country(document: dict[str, object]) -> None:
        reconciliation = cast(dict[str, object], document["reconciliation"])
        attribution = cast(
            dict[str, object], reconciliation["country_attribution_counts"]
        )
        counts = cast(dict[str, object], attribution["raw_country_codes"])
        counts["XX"] = 17

    _replace_input_document(
        monkeypatch, "data/neotoma/relational/reconciliation.json", add_unknown_country
    )

    with pytest.raises(ValueError, match="unsupported country partitions"):
        _build()


def test_aadr_summary_country_must_match_its_partition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def change_country(document: dict[str, object]) -> None:
        document["country"] = "Denmark"

    _replace_input_document(
        monkeypatch,
        "docs/report/countries/sweden/sweden_aadr_v66_summary.json",
        change_country,
    )

    with pytest.raises(ValueError, match="does not match partition: SE"):
        _build()


@pytest.mark.parametrize(
    ("relative_path", "field_path"),
    (
        (
            "data/collection_summary.json",
            ("source_hashes", "landclim", "snapshot_sha256"),
        ),
        ("data/boundaries/raw/source_manifest.json", ("normalized_artifact", "sha256")),
        ("data/neotoma/relational/reconciliation.json", ("source_snapshot_id",)),
        (
            "data/collection_summary.json",
            ("source_hashes", "sead", "snapshot_sha256"),
        ),
    ),
)
def test_governed_digest_identities_require_sha256_syntax(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    field_path: tuple[str, ...],
) -> None:
    def corrupt_digest(document: dict[str, object]) -> None:
        _set_nested(document, field_path, "not-a-sha256")

    _replace_input_document(monkeypatch, relative_path, corrupt_digest)

    with pytest.raises(ValueError, match="SHA-256 digest|sha256 identity"):
        _build()


def test_boundary_manifest_digest_must_match_artifact_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def change_boundary(document: dict[str, object]) -> None:
        document["falsification_marker"] = True

    _replace_input_document(
        monkeypatch,
        "data/boundaries/normalized/nordic_country_boundaries.geojson",
        change_boundary,
    )

    with pytest.raises(ValueError, match="boundary artifact digest does not match"):
        _build()


@pytest.mark.parametrize(
    ("relative_path", "field_path", "value", "message"),
    (
        (
            _SEAD_DECISIONS_PATH,
            ("decision_status_counts", "assigned"),
            2_070,
            "decision status counts",
        ),
        (
            _SEAD_DECISIONS_PATH,
            ("country_counts", "SE"),
            1_924,
            "decision country counts",
        ),
        (
            _SEAD_DECISIONS_PATH,
            ("bbox_site_count",),
            2_194,
            "bbox site count",
        ),
        (
            _SEAD_ADMISSION_PATH,
            ("country_accounting", "admitted_site_count"),
            2_068,
            "admission identity changed",
        ),
        (
            _SEAD_ADMISSION_PATH,
            ("scope_id",),
            f"sha256:{'f' * 64}",
            "admission identity changed",
        ),
    ),
)
def test_sead_embedded_summaries_and_lineage_reconcile(
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    field_path: tuple[str, ...],
    value: object,
    message: str,
) -> None:
    def corrupt_summary(document: dict[str, object]) -> None:
        _set_nested(document, field_path, value)

    _replace_input_document(monkeypatch, relative_path, corrupt_summary)

    with pytest.raises(ValueError, match=message):
        _build()


def test_sead_decision_boundary_digest_matches_governed_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_boundary(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decision = cast(dict[str, object], decisions[0]["decision"])
        decision["boundary_artifact_digest"] = f"sha256:{'f' * 64}"

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        corrupt_boundary,
    )

    with pytest.raises(ValueError, match="governed geometry"):
        _build()


@pytest.mark.parametrize("symlink_part", ("file", "ancestor"))
def test_symlinked_governed_input_path_is_refused(
    monkeypatch: pytest.MonkeyPatch, symlink_part: str
) -> None:
    input_path = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    claimed_symlink = input_path if symlink_part == "file" else input_path.parent
    original_is_symlink = Path.is_symlink

    def is_symlink(path: Path) -> bool:
        return path == claimed_symlink or original_is_symlink(path)

    monkeypatch.setattr(Path, "is_symlink", is_symlink)

    with pytest.raises(
        ValueError, match="governed input path must not contain symlinks"
    ):
        _build()


def test_symlinked_schema_path_is_refused(tmp_path: Path) -> None:
    schema_alias = tmp_path / "country-coverage.schema.json"
    schema_alias.symlink_to(_CELL_SCHEMA_PATH)

    with pytest.raises(ValueError, match="schema path must not contain symlinks"):
        build_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT, cell_schema_path=schema_alias
        )


@pytest.mark.parametrize(
    ("status", "country_code", "refusal_reason", "message"),
    (
        ("fabricated", "SE", None, "governed geometry"),
        ("assigned", "UNASSIGNED", None, "governed country"),
        ("review", "UNASSIGNED", "outside_governed_boundaries", "governed geometry"),
        ("unassigned", "UNASSIGNED", None, "governed geometry"),
    ),
)
def test_invalid_sead_decision_state_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
    country_code: str,
    refusal_reason: str | None,
    message: str,
) -> None:
    def corrupt_decision(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = decisions[0]
        record["governed_country_code"] = country_code
        decision = cast(dict[str, object], record["decision"])
        decision["decision_status"] = status
        decision["refusal_reason"] = refusal_reason

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        corrupt_decision,
    )

    with pytest.raises(ValueError, match=message):
        _build()


@pytest.mark.parametrize("identity_field", ("site_id", "site_uuid"))
def test_duplicate_sead_decision_identity_is_refused(
    monkeypatch: pytest.MonkeyPatch, identity_field: str
) -> None:
    def duplicate_identity(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[2][identity_field] = decisions[0][identity_field]

    _replace_input_document(
        monkeypatch,
        _SEAD_DECISIONS_PATH,
        duplicate_identity,
    )

    with pytest.raises(ValueError, match="duplicate identity"):
        _build()


def test_coherent_sead_country_reassignment_is_refused_by_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reassign(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = decisions[0]
        record["governed_country_code"] = "DK"
        decision = cast(dict[str, object], record["decision"])
        decision["derived_country"] = "Denmark"
        decision["candidate_countries"] = ["Denmark"]
        country_counts = cast(dict[str, int], document["country_counts"])
        country_counts["SE"] -= 1
        country_counts["DK"] += 1

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, reassign)

    with pytest.raises(ValueError, match="governed geometry"):
        _build()


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("latitude_dd", 999),
        ("longitude_dd", -999),
    ),
)
def test_sead_decision_coordinates_are_validated(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    def corrupt_coordinate(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        decisions[0][field] = value

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_coordinate)

    with pytest.raises(ValueError, match="finite coordinate"):
        _build()


@pytest.mark.parametrize(
    ("status", "field", "value"),
    (
        ("assigned", "derived_country", "Denmark"),
        ("review", "ambiguity_reason", None),
        ("unassigned", "refusal_reason", None),
    ),
)
def test_sead_decision_detail_must_equal_geometry_result(
    monkeypatch: pytest.MonkeyPatch, status: str, field: str, value: object
) -> None:
    def corrupt_detail(document: dict[str, object]) -> None:
        decisions = cast(list[dict[str, object]], document["decisions"])
        record = next(
            row
            for row in decisions
            if cast(dict[str, object], row["decision"])["decision_status"] == status
        )
        cast(dict[str, object], record["decision"])[field] = value

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_detail)

    with pytest.raises(ValueError, match="governed geometry"):
        _build()


def test_sead_decision_method_counts_are_recomputed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_method_counts(document: dict[str, object]) -> None:
        counts = cast(dict[str, int], document["decision_method_counts"])
        counts["strict_boundary_containment"] += 1

    _replace_input_document(monkeypatch, _SEAD_DECISIONS_PATH, corrupt_method_counts)

    with pytest.raises(ValueError, match="decision method counts"):
        _build()


def test_sead_country_assignment_digest_is_recomputed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_assignment_digest(document: dict[str, object]) -> None:
        accounting = cast(dict[str, object], document["country_accounting"])
        accounting["country_assignment_sha256"] = "f" * 64

    _replace_input_document(
        monkeypatch, _SEAD_ADMISSION_PATH, corrupt_assignment_digest
    )

    with pytest.raises(ValueError, match="admission identity changed"):
        _build()


def test_sead_admitted_site_identity_is_bound_to_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_site(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["site_uuid"] = "fabricated-site-uuid"

    _replace_input_document(monkeypatch, _SEAD_SITES_PATH, corrupt_site)

    with pytest.raises(ValueError, match="site_uuid"):
        _build()


def test_sead_bundle_digest_binds_copied_file_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_bundle(document: dict[str, object]) -> None:
        document["acquisition_bundle_sha256"] = f"sha256:{'f' * 64}"

    _replace_input_document(monkeypatch, _SEAD_ADMISSION_PATH, corrupt_bundle)

    with pytest.raises(ValueError, match="admission identity changed"):
        _build()


def test_normalized_boundary_duplicate_alias_is_refused_before_indexing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_path = "data/boundaries/normalized/nordic_country_boundaries.geojson"
    manifest_path = "data/boundaries/raw/source_manifest.json"
    boundary = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / boundary_path))
    )
    features = cast(list[dict[str, object]], boundary["features"])
    properties = cast(dict[str, object], features[1]["properties"])
    properties["country"] = "SE"
    properties["name"] = "Sweden"
    boundary_bytes = _document_bytes(boundary)
    manifest = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / manifest_path))
    )
    normalized = cast(dict[str, object], manifest["normalized_artifact"])
    normalized["sha256"] = hashlib.sha256(boundary_bytes).hexdigest()
    _replace_input_documents(
        monkeypatch,
        {
            boundary_path: boundary_bytes,
            manifest_path: _document_bytes(manifest),
        },
    )

    with pytest.raises(ValueError, match="duplicate country alias"):
        _build()


def test_normalized_boundary_requires_exact_nordic_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary_path = "data/boundaries/normalized/nordic_country_boundaries.geojson"
    manifest_path = "data/boundaries/raw/source_manifest.json"
    boundary = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / boundary_path))
    )
    features = cast(list[dict[str, object]], boundary["features"])
    boundary["features"] = [
        feature
        for feature in features
        if cast(dict[str, object], feature["properties"])["country"] != "Norway"
    ]
    boundary_bytes = _document_bytes(boundary)
    manifest = cast(
        dict[str, object], json.loads(_READ_BYTES(_REPOSITORY_ROOT / manifest_path))
    )
    normalized = cast(dict[str, object], manifest["normalized_artifact"])
    normalized["sha256"] = hashlib.sha256(boundary_bytes).hexdigest()
    normalized["feature_count"] = 3
    _replace_input_documents(
        monkeypatch,
        {
            boundary_path: boundary_bytes,
            manifest_path: _document_bytes(manifest),
        },
    )

    with pytest.raises(ValueError, match="exactly SE/DK/NO/FI"):
        _build()


def test_duplicate_animal_evidence_row_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def duplicate_row(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows.append(deepcopy(rows[0]))

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", duplicate_row
    )

    with pytest.raises(ValueError, match="duplicate evidence row"):
        _build()


def test_animal_evidence_totals_must_reconcile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def corrupt_total(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["mapped_sample_count"] = 3

    _replace_input_document(
        monkeypatch, "docs/report/animal_country_species_coverage.json", corrupt_total
    )

    with pytest.raises(ValueError, match="animal sample disposition"):
        _build()


def test_source_stage_authority_vocabulary_is_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fabricate_status(document: dict[str, object]) -> None:
        rows = cast(list[dict[str, object]], document["rows"])
        rows[0]["authority_status"] = "fabricated"

    _replace_input_document(
        monkeypatch, "data/source_family_evidence_stage_matrix.json", fabricate_status
    )

    with pytest.raises(ValueError, match="unsupported authority_status"):
        _build()


def test_input_bytes_are_read_once_for_identity_and_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = (_REPOSITORY_ROOT / "data/collection_summary.json").resolve()
    original = _READ_BYTES(target)
    changed = cast(dict[str, object], json.loads(original))
    source_hashes = cast(dict[str, object], changed["source_hashes"])
    landclim = cast(dict[str, object], source_hashes["landclim"])
    landclim["snapshot_sha256"] = "d" * 64
    replacement = json.dumps(changed, sort_keys=True).encode("utf-8")
    reads = 0

    def changing_read(path: Path) -> bytes:
        nonlocal reads
        if path.resolve() == target:
            reads += 1
            return original if reads == 1 else replacement
        return _READ_BYTES(path)

    monkeypatch.setattr(Path, "read_bytes", changing_read)

    ledger = _build()

    assert reads == 1
    recorded = next(
        item
        for item in cast(list[dict[str, object]], ledger["input_artifacts"])
        if item["path"] == "data/collection_summary.json"
    )
    assert recorded["sha256"] == hashlib.sha256(original).hexdigest()
    expected_snapshot = (
        "sha256:"
        + cast(dict[str, str], json.loads(original)["source_hashes"]["landclim"])[
            "snapshot_sha256"
        ]
    )
    assert (
        _cell(ledger, "landclim", "source_reported", "SE")["source_snapshot_id"]
        == expected_snapshot
    )


def test_substituted_schema_with_governed_identity_is_refused(tmp_path: Path) -> None:
    substitute = tmp_path / "country-coverage.schema.json"
    substitute.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": CELL_SCHEMA_ID,
                "type": "object",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema content is not governed"):
        build_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT, cell_schema_path=substitute
        )


def test_atomic_writer_refuses_symlinked_or_overlapping_output() -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as temporary_directory:
        directory = Path(temporary_directory)
        schema_copy = directory / "country-coverage.schema.json"
        schema_copy.write_bytes(_CELL_SCHEMA_PATH.read_bytes())
        target = directory / "target.json"
        target.write_text("preserve\n", encoding="utf-8")
        alias = directory / "alias.json"
        alias.symlink_to(target.name)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=alias,
            )

        real_parent = directory / "real-parent"
        real_parent.mkdir()
        parent_alias = directory / "parent-alias"
        parent_alias.symlink_to(real_parent.name, target_is_directory=True)
        with pytest.raises(ValueError, match="must not contain symlinks"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=parent_alias / "ledger.json",
            )

        with pytest.raises(ValueError, match="overlaps a governed input"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=schema_copy,
            )

        hardlink = directory / "schema-hardlink.json"
        hardlink.hardlink_to(schema_copy)
        with pytest.raises(ValueError, match="overlaps a governed input"):
            write_country_dimension_coverage_ledger(
                _REPOSITORY_ROOT,
                cell_schema_path=schema_copy,
                output_path=hardlink,
            )


def test_checked_ledger_and_atomic_writer_are_fixed_point() -> None:
    first = _build()
    second = _build()
    assert first == second

    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as temporary_directory:
        output = Path(temporary_directory) / "country_dimension_coverage.json"
        first_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        second_bytes = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=output,
        )
        assert first_bytes == second_bytes == output.read_bytes()
        assert output.stat().st_mode & 0o777 == 0o644

    assert _LEDGER_PATH.read_bytes() == first_bytes


def test_atomic_writer_refuses_output_outside_repository() -> None:
    with pytest.raises(
        ValueError, match="country coverage output must remain inside the repository"
    ):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT.parent
            / "country_dimension_coverage-outside.json",
        )


def test_atomic_writer_refuses_lexical_output_alias() -> None:
    with pytest.raises(ValueError, match="must not use aliases"):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT
            / "data/../data/country_dimension_coverage.json",
        )


def test_atomic_writer_refuses_intermediate_ancestor_symlink_swap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    outside_root = _REPOSITORY_ROOT / "artifacts"
    outside_root.mkdir(exist_ok=True)
    with (
        tempfile.TemporaryDirectory(
            dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
        ) as approved_directory,
        tempfile.TemporaryDirectory(dir=outside_root) as outside_directory,
    ):
        approved_root = Path(approved_directory)
        intermediate = approved_root / "stable-ancestor"
        intermediate.mkdir()
        displaced = approved_root / "displaced-ancestor"
        outside = Path(outside_directory)
        destination = intermediate / "nested" / "country-coverage.json"

        def swap_ancestor(
            repository_root: Path, *, cell_schema_path: Path
        ) -> dict[str, object]:
            assert repository_root == _REPOSITORY_ROOT
            assert cell_schema_path == _CELL_SCHEMA_PATH
            intermediate.rename(displaced)
            intermediate.symlink_to(outside, target_is_directory=True)
            return {"probe": "ancestor-swap"}

        monkeypatch.setattr(
            country_coverage_module,
            "build_country_dimension_coverage_ledger",
            swap_ancestor,
        )
        try:
            with pytest.raises(ValueError, match="must not contain symlinks"):
                write_country_dimension_coverage_ledger(
                    _REPOSITORY_ROOT,
                    cell_schema_path=_CELL_SCHEMA_PATH,
                    output_path=destination,
                )
            assert list(outside.iterdir()) == []
            assert not (displaced / "nested").exists()
            assert list(displaced.rglob("*.writing")) == []
            assert list(outside.rglob("*.writing")) == []
        finally:
            intermediate.unlink(missing_ok=True)


def test_atomic_writer_creates_approved_nested_artifact_destination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _COUNTRY_COVERAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        dir=_COUNTRY_COVERAGE_ARTIFACT_ROOT
    ) as approved_directory:
        destination = (
            Path(approved_directory) / "nested" / "evidence" / "country-coverage.json"
        )

        def fixed_ledger(
            repository_root: Path, *, cell_schema_path: Path
        ) -> dict[str, object]:
            assert repository_root == _REPOSITORY_ROOT
            assert cell_schema_path == _CELL_SCHEMA_PATH
            return {"probe": "approved-nested-output"}

        monkeypatch.setattr(
            country_coverage_module,
            "build_country_dimension_coverage_ledger",
            fixed_ledger,
        )
        payload = write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=destination,
        )

        assert destination.read_bytes() == payload
        assert json.loads(payload) == {"probe": "approved-nested-output"}
        assert list(Path(approved_directory).rglob("*.writing")) == []


@pytest.mark.parametrize(
    "relative_output",
    (
        ".git/country-coverage.json",
        "pyproject.toml",
        "data/unrelated-country-output.json",
        "packages/bijux-pollenomics/src/bijux_pollenomics/governance/country_coverage.py",
        "packages/bijux-pollenomics/tests/unit/governance/test_country_coverage.py",
        "artifacts/unrelated-country-output.json",
    ),
)
def test_atomic_writer_refuses_unapproved_repository_paths(
    relative_output: str,
) -> None:
    with pytest.raises(ValueError, match="not an approved product or artifact path"):
        write_country_dimension_coverage_ledger(
            _REPOSITORY_ROOT,
            cell_schema_path=_CELL_SCHEMA_PATH,
            output_path=_REPOSITORY_ROOT / relative_output,
        )
