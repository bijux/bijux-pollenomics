"""Country-coverage governed-input refusal tests."""

from __future__ import annotations

from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import cast
import pytest
from bijux_pollenomics.governance.country_coverage import (
    build_country_dimension_coverage_ledger,
)
from .fixtures import (
    _CELL_SCHEMA_PATH,
    _READ_BYTES,
    _REPOSITORY_ROOT,
    _SEAD_ADMISSION_PATH,
    _SEAD_DECISIONS_PATH,
    _SEAD_SITES_PATH,
    _build,
    _document_bytes,
    _replace_input_document,
    _replace_input_documents,
    _set_nested,
)


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
