"""Publish refusal-bounded Rootsi candidates for the ESSD input inventory."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
from typing import cast
import unicodedata

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyMetadataInventory,
    StudyMetadataRecord,
    read_landclim_study_inventory,
    reopen_landclim_study_inventory,
)
from bijux_pollenomics.collection.sources.rootsi import (
    RootsiSiteMetadataClaim,
    normalize_rootsi_site_metadata,
)
from bijux_pollenomics.collection.sources.rootsi.authority import (
    ARCHIVE_SHA256,
    METADATA_MEMBER,
    METADATA_SHA256,
)
from bijux_pollenomics.collection.sources.rootsi.cells import (
    read_rootsi_cell_review,
)
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

JsonObject = dict[str, object]

_MANIFEST = "manifest.json"
_PUBLICATION_CANDIDATES = "publication-candidates.jsonl"
_ROOTSI_CROSSWALK = "rootsi-crosswalk.csv"
_REQUIREMENT_STATUS = "requirement-status.csv"
_REPORT = "report.json"
_OUTPUT_NAMES = (
    _MANIFEST,
    _PUBLICATION_CANDIDATES,
    _ROOTSI_CROSSWALK,
    _REQUIREMENT_STATUS,
    _REPORT,
)
_CELL_REVIEW_MANIFEST_SHA256 = (
    "2e5b5a3a10cec59fc8086c0c99db56bb394e9d1f180bbd5571c1098c262c9179"
)
_MATCHING_PROFILE = (
    "normalized-sequence-label-or-normalized-site-name-plus-exact-sample-count-"
    "with-exact-SWE-to-Sweden-country-filter.v1"
)
_EXPECTED_PAIR_IDENTITY_SHA256 = (
    "ca94f04342f5c54212dc3ef9acfa0cbeea6e92419878f951ec23b2a0acf5cfd6"
)
_PUBLICATION_RECORDS = 1128
_ROOTSI_RECORDS = 81
_TYPED_WORKBOOKS = 79
_REQUIREMENTS = (
    (
        "historical_primary_pollen_counts",
        "not_authenticated",
        "metadata_candidate_does_not_authenticate_historical_counts",
    ),
    (
        "historical_selected_chronology",
        "not_authenticated",
        "selected_historical_chronology_not_recovered",
    ),
    (
        "historical_current_revision_identity",
        "not_authenticated",
        "historical_to_current_revision_not_verified",
    ),
    (
        "per_sequence_rights",
        "unresolved",
        "candidate_archive_rights_not_cleared_per_sequence",
    ),
    (
        "taxonomy_and_count_denominator",
        "unresolved",
        "taxon_mapping_and_count_denominator_not_reviewed",
    ),
    (
        "basin_and_profile_semantics",
        "unresolved",
        "basin_radius_coordinates_and_profile_semantics_not_reviewed",
    ),
)


class RootsiInputClosureError(ValueError):
    """Raised when Rootsi candidate evidence exceeds its admitted meaning."""


@dataclass(frozen=True)
class _Candidate:
    rootsi: RootsiSiteMetadataClaim
    reasons: tuple[str, ...]
    country_agrees: bool
    sample_count_agrees: bool


@dataclass(frozen=True)
class _Inputs:
    publication: LandClimStudyMetadataInventory
    rootsi: tuple[RootsiSiteMetadataClaim, ...]
    typed_manifest: JsonObject
    typed_manifest_bytes: bytes
    typed_accounting: JsonObject
    typed_workbooks: dict[str, JsonObject]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_line(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_object(content: bytes, name: str) -> JsonObject:
    value = json.loads(content)
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise RootsiInputClosureError(f"Expected a JSON object in {name}")
    return cast(JsonObject, value)


def _raw(record: StudyMetadataRecord, column: str) -> str | None:
    values = [value.raw for value in record.values if value.column == column]
    if len(values) != 1:
        raise RootsiInputClosureError(
            f"Publication row {record.worksheet_row} lacks {column!r}"
        )
    return values[0]


def _normalized(value: str | None) -> str:
    if value is None:
        return ""
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if character.isalnum()
    )


def _sequence_stem(value: str | None) -> str:
    if value is None:
        return ""
    return PurePosixPath(value).stem


def _sample_text(value: int | None) -> str | None:
    return None if value is None else str(value)


def _match(
    rootsi: RootsiSiteMetadataClaim, publication: StudyMetadataRecord
) -> _Candidate | None:
    publication_sequence = _raw(publication, "csvfilename")
    publication_site = _raw(publication, "SiteName")
    publication_samples = _raw(publication, "nPollenSamples")
    reasons: list[str] = []
    if _normalized(rootsi.site_label) == _normalized(
        _sequence_stem(publication_sequence)
    ):
        reasons.append("normalized_sequence_label")
    sample_agrees = (
        rootsi.sample_count_claim is not None
        and publication_samples is not None
        and str(rootsi.sample_count_claim) == publication_samples
    )
    if _normalized(rootsi.site_name) == _normalized(publication_site) and sample_agrees:
        reasons.append("normalized_site_name_and_exact_sample_count")
    if not reasons:
        return None
    country_agrees = (
        rootsi.country_native == "SWE" and _raw(publication, "Country") == "Sweden"
    )
    return _Candidate(rootsi, tuple(reasons), country_agrees, sample_agrees)


def _publication_matches(
    inputs: _Inputs,
) -> dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]]:
    result: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]] = {}
    for publication in inputs.publication.records:
        observed = tuple(
            candidate
            for rootsi in inputs.rootsi
            if (candidate := _match(rootsi, publication)) is not None
        )
        accepted_country = tuple(row for row in observed if row.country_agrees)
        rejected_country = tuple(row for row in observed if not row.country_agrees)
        result[publication.worksheet_row] = (accepted_country, rejected_country)
    return result


def _require_int(value: object, label: str) -> int:
    if type(value) is not int:
        raise RootsiInputClosureError(f"Typed-cell {label} must be an integer")
    return value


def _typed_workbooks(manifest: JsonObject) -> dict[str, JsonObject]:
    capture = manifest.get("capture")
    if not isinstance(capture, dict):
        raise RootsiInputClosureError("Typed-cell capture is missing")
    selected = capture.get("selected_workbooks")
    if not isinstance(selected, list) or len(selected) != _TYPED_WORKBOOKS:
        raise RootsiInputClosureError("Typed-cell review must bind 79 workbooks")
    result: dict[str, JsonObject] = {}
    for raw in selected:
        if not isinstance(raw, dict):
            raise RootsiInputClosureError("Typed-cell workbook binding is invalid")
        row = cast(JsonObject, raw)
        member = row.get("archive_member")
        digest = row.get("sha256")
        byte_count = row.get("bytes")
        if (
            not isinstance(member, str)
            or not member.startswith("rootsi/")
            or not member.endswith(".xls")
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or _require_int(byte_count, "workbook byte count") <= 0
        ):
            raise RootsiInputClosureError("Typed-cell workbook binding is invalid")
        key = member.casefold()
        if key in result:
            raise RootsiInputClosureError("Typed-cell workbook names are not unique")
        result[key] = row
    return result


def _validate_typed_capture(manifest: JsonObject) -> None:
    capture = manifest.get("capture")
    if not isinstance(capture, dict):
        raise RootsiInputClosureError("Typed-cell capture is missing")
    expected = {
        "scope": "complete_retained_capture",
        "archive_sha256": ARCHIVE_SHA256,
        "archive_membership_verification": "retained_receipt_bound_not_replayed",
    }
    for key, value in expected.items():
        if capture.get(key) != value:
            raise RootsiInputClosureError(
                f"Typed-cell archive custody changed for {key!r}"
            )


def _read_inputs(
    landclim_raw_dir: Path,
    rootsi_metadata_path: Path,
    typed_cell_review_dir: Path,
) -> _Inputs:
    publication = read_landclim_study_inventory(Path(landclim_raw_dir))
    if publication.metadata_record_count != _PUBLICATION_RECORDS:
        raise RootsiInputClosureError("Publication denominator is not 1,128")
    if (
        reopen_landclim_study_inventory(
            publication.canonical_bytes, Path(landclim_raw_dir)
        )
        != publication
    ):
        raise RootsiInputClosureError("Publication inventory did not reopen exactly")

    rootsi_metadata_path = Path(rootsi_metadata_path)
    if rootsi_metadata_path.is_symlink() or not rootsi_metadata_path.is_file():
        raise RootsiInputClosureError("Rootsi metadata must be a regular file")
    rootsi = normalize_rootsi_site_metadata(rootsi_metadata_path)
    if len(rootsi) != _ROOTSI_RECORDS:
        raise RootsiInputClosureError("Rootsi metadata denominator is not 81")

    typed_cell_review_dir = Path(typed_cell_review_dir)
    bundle = read_rootsi_cell_review(
        typed_cell_review_dir,
        expected_manifest_sha256=_CELL_REVIEW_MANIFEST_SHA256,
    )
    manifest_bytes = (typed_cell_review_dir / _MANIFEST).read_bytes()
    if _sha256(manifest_bytes) != bundle.manifest_sha256:
        raise RootsiInputClosureError("Typed-cell manifest changed while reading")
    manifest = _json_object(manifest_bytes, "typed-cell manifest")
    _validate_typed_capture(manifest)
    accounting = bundle.accounting
    expected_accounting = {
        "workbooks": 79,
        "sheets": 107,
        "rectangle_positions": 547330,
        "scientifically_admitted_observations": 0,
    }
    for key, expected in expected_accounting.items():
        if accounting.get(key) != expected:
            raise RootsiInputClosureError(f"Typed-cell accounting changed for {key!r}")
    return _Inputs(
        publication=publication,
        rootsi=rootsi,
        typed_manifest=manifest,
        typed_manifest_bytes=manifest_bytes,
        typed_accounting=accounting,
        typed_workbooks=_typed_workbooks(manifest),
    )


def _candidate_payload(candidate: _Candidate) -> JsonObject:
    rootsi = candidate.rootsi
    source_values = dict(rootsi.source_values)
    return {
        "rootsi_source_row": rootsi.source_row_number,
        "rootsi_source_locator": f"{METADATA_MEMBER}!{rootsi.source_row_number}",
        "rootsi_site_name_raw": rootsi.site_name,
        "rootsi_sequence_label_raw": rootsi.site_label,
        "rootsi_sample_count_raw": source_values["nr_samples"],
        "rootsi_sample_count_claim": rootsi.sample_count_claim,
        "match_reasons": list(candidate.reasons),
        "reported_country_agrees": candidate.country_agrees,
        "sample_count_agrees": candidate.sample_count_agrees,
        "historical_primary_input_identity_verified": False,
    }


def _status(candidates: Sequence[_Candidate]) -> str:
    if not candidates:
        return "no_rootsi_metadata_candidate"
    if len(candidates) == 1:
        return "unique_rootsi_metadata_candidate"
    return "ambiguous_rootsi_metadata_candidates"


def _publication_candidates_bytes(
    inputs: _Inputs,
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> bytes:
    chunks: list[bytes] = []
    for record in inputs.publication.records:
        candidates, rejected = matches[record.worksheet_row]
        chunks.append(
            _json_line(
                {
                    "schema_version": "essd-rootsi-publication-candidate.v1",
                    "publication_worksheet_row": record.worksheet_row,
                    "publication_source_locator": record.source_locator,
                    "publication_site_name_raw": _raw(record, "SiteName"),
                    "publication_sequence_raw": _raw(record, "csvfilename"),
                    "publication_country_raw": _raw(record, "Country"),
                    "publication_sample_count_raw": _raw(record, "nPollenSamples"),
                    "publication_access_marker_raw": _raw(
                        record, "DataRestricted/NotRestriced"
                    ),
                    "publication_source_credit_raw": _raw(
                        record, "Database/Authorname and/or data collector"
                    ),
                    "publication_chronology_source_raw": _raw(
                        record, "chronologySource"
                    ),
                    "candidate_status": _status(candidates),
                    "metadata_candidates": [
                        _candidate_payload(candidate) for candidate in candidates
                    ],
                    "country_disagreeing_candidates": [
                        _candidate_payload(candidate) for candidate in rejected
                    ],
                    "authenticated_historical_primary_input": None,
                    "reproduction_ready": False,
                }
            )
        )
    return b"".join(chunks)


def _root_matches(
    record: RootsiSiteMetadataClaim,
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> tuple[list[tuple[int, _Candidate]], list[tuple[int, _Candidate]]]:
    accepted: list[tuple[int, _Candidate]] = []
    rejected: list[tuple[int, _Candidate]] = []
    for publication_row, (candidates, country_rejected) in matches.items():
        accepted.extend(
            (publication_row, candidate)
            for candidate in candidates
            if candidate.rootsi.source_row_number == record.source_row_number
        )
        rejected.extend(
            (publication_row, candidate)
            for candidate in country_rejected
            if candidate.rootsi.source_row_number == record.source_row_number
        )
    return accepted, rejected


def _pair_identity(
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> JsonObject:
    def payload(publication_row: int, candidate: _Candidate) -> JsonObject:
        return {
            "publication_worksheet_row": publication_row,
            "rootsi_source_row": candidate.rootsi.source_row_number,
            "match_reasons": list(candidate.reasons),
            "sample_count_agrees": candidate.sample_count_agrees,
        }

    accepted = [
        payload(publication_row, candidate)
        for publication_row, (candidates, _) in matches.items()
        for candidate in candidates
    ]
    rejected = [
        payload(publication_row, candidate)
        for publication_row, (_, candidates) in matches.items()
        for candidate in candidates
    ]

    def ordering(row: JsonObject) -> tuple[int, int]:
        return (
            cast(int, row["publication_worksheet_row"]),
            cast(int, row["rootsi_source_row"]),
        )

    return {
        "matching_profile": _MATCHING_PROFILE,
        "accepted_pairs": sorted(accepted, key=ordering),
        "country_rejected_pairs": sorted(rejected, key=ordering),
    }


def _pair_identity_sha256(
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> str:
    return _sha256(_json_bytes(_pair_identity(matches)))


def _root_crosswalk_bytes(
    inputs: _Inputs,
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> bytes:
    columns = (
        "rootsi_source_row",
        "rootsi_source_locator",
        "rootsi_site_name_raw",
        "rootsi_sequence_label_raw",
        "rootsi_sample_count_raw",
        "rootsi_sample_count_claim",
        "rootsi_country_raw",
        "rootsi_latitude_raw",
        "rootsi_longitude_raw",
        "rootsi_site_area_raw",
        "rootsi_site_radius_raw",
        "rootsi_date_count_raw",
        "rootsi_basin_type_raw",
        "rootsi_observation_workbook_claim",
        "typed_workbook_member",
        "typed_workbook_sha256",
        "typed_workbook_bytes",
        "publication_candidate_status",
        "publication_candidate_rows_json",
        "match_reasons_json",
        "sample_count_agrees_json",
        "country_disagreeing_publication_rows_json",
        "historical_primary_input_identity_status",
        "reproduction_ready",
    )
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(columns)
    for record in inputs.rootsi:
        accepted, rejected = _root_matches(record, matches)
        source_values = dict(record.source_values)
        claimed_member = (
            None
            if record.observation_workbook_claim is None
            else f"rootsi/{record.observation_workbook_claim}"
        )
        typed = (
            None
            if claimed_member is None
            else inputs.typed_workbooks.get(claimed_member.casefold())
        )
        if (typed is None) != (record.observation_workbook_claim is None):
            raise RootsiInputClosureError(
                f"Rootsi row {record.source_row_number} typed-workbook closure changed"
            )
        candidate_status = _status([candidate for _, candidate in accepted])
        writer.writerow(
            (
                record.source_row_number,
                f"{METADATA_MEMBER}!{record.source_row_number}",
                record.site_name,
                record.site_label,
                source_values["nr_samples"],
                _sample_text(record.sample_count_claim),
                source_values["Country"],
                source_values["LatDD"],
                source_values["LongDD"],
                source_values["Site area (ha)"],
                source_values["Site radius (m)"],
                source_values["No. of dates1"],
                source_values["Basin type"],
                record.observation_workbook_claim,
                None if typed is None else typed["archive_member"],
                None if typed is None else typed["sha256"],
                None if typed is None else typed["bytes"],
                candidate_status,
                json.dumps([row for row, _ in accepted], separators=(",", ":")),
                json.dumps(
                    [list(candidate.reasons) for _, candidate in accepted],
                    separators=(",", ":"),
                ),
                json.dumps(
                    [candidate.sample_count_agrees for _, candidate in accepted],
                    separators=(",", ":"),
                ),
                json.dumps([row for row, _ in rejected], separators=(",", ":")),
                "not_authenticated",
                "false",
            )
        )
    return stream.getvalue().encode("utf-8")


def _requirement_status_bytes(
    inputs: _Inputs,
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        (
            "namespace",
            "publication_worksheet_row",
            "publication_source_locator",
            "metadata_candidate_status",
            "requirement",
            "state",
            "reason_code",
        )
    )
    for record in inputs.publication.records:
        candidates, _ = matches[record.worksheet_row]
        for requirement, state, reason_code in _REQUIREMENTS:
            if not candidates:
                state = "not_applicable"
                reason_code = "no_rootsi_metadata_candidate"
            elif len(candidates) > 1:
                state = "unresolved"
                reason_code = "ambiguous_rootsi_metadata_candidates"
            writer.writerow(
                (
                    "essd-rootsi-input-requirement.v1",
                    record.worksheet_row,
                    record.source_locator,
                    _status(candidates),
                    requirement,
                    state,
                    reason_code,
                )
            )
    return stream.getvalue().encode("utf-8")


def _claims() -> JsonObject:
    return {
        "rootsi_archive_membership_replayed_by_closure": False,
        "rootsi_is_authenticated_historical_input": False,
        "historical_primary_pollen_inputs_recovered": False,
        "historical_selected_chronologies_recovered": False,
        "historical_current_revision_crosswalk_completed": False,
        "per_sequence_rights_cleared": False,
        "taxonomy_and_count_denominators_reviewed": False,
        "basin_and_profile_semantics_reviewed": False,
        "reproduction_input_complete": False,
        "original_profile_r_rerun_executed": False,
        "whole_paper_reproduction_certified": False,
        "publication_allowed": False,
        "scientifically_accepted": False,
        "scientific_acceptance": "not_evaluated",
    }


def _report(
    inputs: _Inputs,
    matches: dict[int, tuple[tuple[_Candidate, ...], tuple[_Candidate, ...]]],
) -> JsonObject:
    candidate_counts = Counter(
        _status(matches[record.worksheet_row][0])
        for record in inputs.publication.records
    )
    rootsi_counts = Counter(
        _status([candidate for _, candidate in _root_matches(record, matches)[0]])
        for record in inputs.rootsi
    )
    reason_sets = Counter(
        "+".join(candidate.reasons)
        for candidates, _ in matches.values()
        for candidate in candidates
    )
    sample_disagreements = sum(
        not candidate.sample_count_agrees
        for candidates, _ in matches.values()
        for candidate in candidates
    )
    country_rejections = sum(len(rejected) for _, rejected in matches.values())
    pair_identity_sha256 = _pair_identity_sha256(matches)
    applicable_requirement_records = sum(
        len(_REQUIREMENTS) for candidates, _ in matches.values() if candidates
    )
    return {
        "schema_version": "essd-rootsi-input-closure-report.v1",
        "profile": "landclim-ii-rootsi-metadata-candidate-closure-v1",
        "scope": {
            "publication_metadata_records_complete": True,
            "rootsi_metadata_records_complete": True,
            "typed_cell_review_consumed_by_reference": True,
            "archive_membership_replayed": False,
            "emitted_string_matching_fields_preserve_source_native_text": True,
            "rootsi_sample_count_emission": (
                "raw_source_text_and_normalized_integer_claim_separate"
            ),
            "country_agreement_is_exact_source_label_comparison": True,
            "metadata_matching_is_not_input_authentication": True,
        },
        "denominators": {
            "publication_metadata_records": len(inputs.publication.records),
            "rootsi_metadata_records": len(inputs.rootsi),
            "rootsi_typed_workbook_candidates": len(inputs.typed_workbooks),
            "typed_workbook_sheets": inputs.typed_accounting["sheets"],
            "typed_rectangle_positions": inputs.typed_accounting["rectangle_positions"],
            "publication_rows_with_unique_metadata_candidate": candidate_counts[
                "unique_rootsi_metadata_candidate"
            ],
            "publication_rows_without_rootsi_metadata_candidate": candidate_counts[
                "no_rootsi_metadata_candidate"
            ],
            "publication_rows_with_ambiguous_metadata_candidates": candidate_counts[
                "ambiguous_rootsi_metadata_candidates"
            ],
            "rootsi_rows_with_unique_publication_candidate": rootsi_counts[
                "unique_rootsi_metadata_candidate"
            ],
            "rootsi_rows_without_publication_candidate": rootsi_counts[
                "no_rootsi_metadata_candidate"
            ],
            "rootsi_rows_with_ambiguous_publication_candidates": rootsi_counts[
                "ambiguous_rootsi_metadata_candidates"
            ],
            "country_disagreeing_candidate_pairs_rejected": country_rejections,
            "unique_candidate_sample_count_disagreements": sample_disagreements,
            "requirement_status_records": len(inputs.publication.records)
            * len(_REQUIREMENTS),
            "applicable_requirement_status_records": applicable_requirement_records,
            "not_applicable_requirement_status_records": (
                len(inputs.publication.records) * len(_REQUIREMENTS)
                - applicable_requirement_records
            ),
            "not_authenticated_requirement_status_records": (
                applicable_requirement_records
                // len(_REQUIREMENTS)
                * sum(state == "not_authenticated" for _, state, _ in _REQUIREMENTS)
            ),
            "unresolved_requirement_status_records": (
                applicable_requirement_records
                // len(_REQUIREMENTS)
                * sum(state == "unresolved" for _, state, _ in _REQUIREMENTS)
            ),
            "authenticated_historical_primary_input_records": 0,
            "reproduction_ready_records": 0,
        },
        "candidate_evidence_pattern_counts": dict(sorted(reason_sets.items())),
        "pair_identity": {
            "matching_profile": _MATCHING_PROFILE,
            "sha256": pair_identity_sha256,
            "accepted_pairs": sum(len(rows) for rows, _ in matches.values()),
            "country_rejected_pairs": country_rejections,
        },
        "claims": _claims(),
        "blocking_dependencies": [
            "author or custodian confirmation of historical input revisions",
            "historical selected ages and chronology construction",
            "per-sequence rights and redistribution decisions",
            "taxon mapping and count-unit denominator decisions",
            "basin, radius and conflicting coordinate disposition",
            "publication-specific profile and PFT/ISTS transformation rules",
            "authenticated primary inputs for all publication records",
            "qualified scientific review",
        ],
    }


def _validate_expected_report(report: JsonObject) -> None:
    denominators = report.get("denominators")
    if not isinstance(denominators, dict):
        raise RootsiInputClosureError("Closure denominators are missing")
    expected = {
        "publication_metadata_records": 1128,
        "rootsi_metadata_records": 81,
        "rootsi_typed_workbook_candidates": 79,
        "publication_rows_with_unique_metadata_candidate": 79,
        "publication_rows_without_rootsi_metadata_candidate": 1049,
        "publication_rows_with_ambiguous_metadata_candidates": 0,
        "rootsi_rows_with_unique_publication_candidate": 79,
        "rootsi_rows_without_publication_candidate": 2,
        "rootsi_rows_with_ambiguous_publication_candidates": 0,
        "country_disagreeing_candidate_pairs_rejected": 1,
        "unique_candidate_sample_count_disagreements": 1,
        "requirement_status_records": 6768,
        "applicable_requirement_status_records": 474,
        "not_applicable_requirement_status_records": 6294,
        "not_authenticated_requirement_status_records": 237,
        "unresolved_requirement_status_records": 237,
        "authenticated_historical_primary_input_records": 0,
        "reproduction_ready_records": 0,
    }
    for key, value in expected.items():
        if denominators.get(key) != value:
            raise RootsiInputClosureError(
                f"Rootsi candidate closure changed for {key!r}"
            )
    patterns = report.get("candidate_evidence_pattern_counts")
    if patterns != {
        "normalized_sequence_label": 2,
        "normalized_sequence_label+normalized_site_name_and_exact_sample_count": 60,
        "normalized_site_name_and_exact_sample_count": 17,
    }:
        raise RootsiInputClosureError("Rootsi candidate evidence patterns changed")
    pair_identity = report.get("pair_identity")
    if pair_identity != {
        "matching_profile": _MATCHING_PROFILE,
        "sha256": _EXPECTED_PAIR_IDENTITY_SHA256,
        "accepted_pairs": 79,
        "country_rejected_pairs": 1,
    }:
        raise RootsiInputClosureError("Rootsi candidate pair identity changed")


def _manifest(inputs: _Inputs, peers: dict[str, bytes]) -> JsonObject:
    logical_rows = {
        _PUBLICATION_CANDIDATES: _PUBLICATION_RECORDS,
        _ROOTSI_CROSSWALK: _ROOTSI_RECORDS,
        _REQUIREMENT_STATUS: _PUBLICATION_RECORDS * len(_REQUIREMENTS),
        _REPORT: 1,
    }
    artifacts = [
        {
            "path": name,
            "byte_count": len(peers[name]),
            "sha256": _sha256(peers[name]),
            "logical_rows": logical_rows[name],
        }
        for name in (
            _PUBLICATION_CANDIDATES,
            _ROOTSI_CROSSWALK,
            _REQUIREMENT_STATUS,
            _REPORT,
        )
    ]
    return {
        "schema_version": "essd-rootsi-input-closure-manifest.v1",
        "producer": "bijux_pollenomics_dev.essd_reproduction.rootsi_input_closure",
        "profile": "landclim-ii-rootsi-metadata-candidate-closure-v1",
        "sources": {
            "publication_inventory": {
                "schema_version": inputs.publication.schema_version,
                "canonical_sha256": inputs.publication.sha256,
                "workbook_sha256": inputs.publication.workbook_sha256,
                "receipt_sha256": inputs.publication.receipt_sha256,
                "records": len(inputs.publication.records),
            },
            "rootsi_metadata": {
                "archive_sha256": ARCHIVE_SHA256,
                "archive_membership_verification": (
                    "retained_receipt_bound_not_replayed"
                ),
                "archive_replayed_by_closure": False,
                "member": METADATA_MEMBER,
                "member_sha256": METADATA_SHA256,
                "records": len(inputs.rootsi),
            },
            "typed_cell_review": {
                "manifest_sha256": _sha256(inputs.typed_manifest_bytes),
                "schema": inputs.typed_manifest["schema"],
                "workbooks": len(inputs.typed_workbooks),
                "sheets": inputs.typed_accounting["sheets"],
                "rectangle_positions": inputs.typed_accounting["rectangle_positions"],
                "consumption": "validated_reference_without_copy",
                "scientific_admission": inputs.typed_manifest["scientific_admission"],
                "archive_membership_verification": (
                    "retained_receipt_bound_not_replayed"
                ),
                "archive_replayed_by_closure": False,
            },
        },
        "output_contract": {
            "output_file_count": len(_OUTPUT_NAMES),
            "publication_candidate_records": _PUBLICATION_RECORDS,
            "rootsi_crosswalk_records": _ROOTSI_RECORDS,
            "requirement_status_records": _PUBLICATION_RECORDS * len(_REQUIREMENTS),
            "matching_profile": _MATCHING_PROFILE,
            "candidate_pair_identity_sha256": _EXPECTED_PAIR_IDENTITY_SHA256,
            "csv_null_encoding": "empty_field_with_explicit_status_columns",
        },
        "artifacts": artifacts,
        "claims": _claims(),
    }


def build_rootsi_input_closure(
    landclim_raw_dir: Path,
    rootsi_metadata_path: Path,
    typed_cell_review_dir: Path,
) -> dict[str, bytes]:
    """Build a deterministic candidate ledger without authenticating inputs."""
    inputs = _read_inputs(
        Path(landclim_raw_dir),
        Path(rootsi_metadata_path),
        Path(typed_cell_review_dir),
    )
    matches = _publication_matches(inputs)
    report = _report(inputs, matches)
    _validate_expected_report(report)
    peers = {
        _PUBLICATION_CANDIDATES: _publication_candidates_bytes(inputs, matches),
        _ROOTSI_CROSSWALK: _root_crosswalk_bytes(inputs, matches),
        _REQUIREMENT_STATUS: _requirement_status_bytes(inputs, matches),
        _REPORT: _json_bytes(report),
    }
    return {_MANIFEST: _json_bytes(_manifest(inputs, peers)), **peers}


def _validate_directory(output: Path, expected: dict[str, bytes]) -> dict[str, bytes]:
    if output.is_symlink() or not output.is_dir():
        raise RootsiInputClosureError(
            "Rootsi input closure must be a direct regular directory"
        )
    children = list(output.iterdir())
    if {path.name for path in children} != set(_OUTPUT_NAMES):
        raise RootsiInputClosureError("Rootsi input closure file inventory changed")
    for name in _OUTPUT_NAMES:
        path = output / name
        if path.is_symlink() or not path.is_file():
            raise RootsiInputClosureError(f"Unsafe closure output: {name}")
        if path.read_bytes() != expected[name]:
            raise RootsiInputClosureError(
                f"Closure output does not match authenticated parents: {name}"
            )
    return expected


def validate_rootsi_input_closure(
    landclim_raw_dir: Path,
    rootsi_metadata_path: Path,
    typed_cell_review_dir: Path,
    output: Path,
) -> dict[str, bytes]:
    """Rebuild from pinned parents and exact-compare every closure file."""
    expected = build_rootsi_input_closure(
        landclim_raw_dir, rootsi_metadata_path, typed_cell_review_dir
    )
    return _validate_directory(Path(output), expected)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _refuse_symlink_ancestors(path: Path) -> None:
    candidate = path.parent
    while True:
        if candidate.is_symlink():
            raise RootsiInputClosureError(
                f"Refusing a symlinked closure output ancestor: {candidate}"
            )
        parent = candidate.parent
        if parent == candidate:
            return
        candidate = parent


def _require_new_output(output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Refusing to replace existing output: {output}")


def publish_rootsi_input_closure(
    landclim_raw_dir: Path,
    rootsi_metadata_path: Path,
    typed_cell_review_dir: Path,
    output: Path,
) -> JsonObject:
    """Atomically publish one new source-bound closure directory."""
    products = build_rootsi_input_closure(
        landclim_raw_dir, rootsi_metadata_path, typed_cell_review_dir
    )
    output = Path(output).absolute()
    _refuse_symlink_ancestors(output)
    _require_new_output(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    _refuse_symlink_ancestors(output)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for name in _OUTPUT_NAMES:
            with (temporary / name).open("xb") as stream:
                stream.write(products[name])
                stream.flush()
                os.fsync(stream.fileno())
        _validate_directory(temporary, products)
        _fsync_directory(temporary)
        _refuse_symlink_ancestors(output)
        _require_new_output(output)
        publish_new_output_tree(
            final_output_root=output,
            staging_output_root=temporary,
        )
        _fsync_directory(output.parent)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return _json_object(products[_MANIFEST], _MANIFEST)


def main(argv: Sequence[str] | None = None) -> int:
    """Publish candidate closure from the three exact evidence parents."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landclim-raw-dir", required=True, type=Path)
    parser.add_argument("--rootsi-metadata", required=True, type=Path)
    parser.add_argument("--typed-cell-review", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest = publish_rootsi_input_closure(
        args.landclim_raw_dir,
        args.rootsi_metadata,
        args.typed_cell_review,
        args.output,
    )
    contract = cast(JsonObject, manifest["output_contract"])
    print(
        json.dumps(
            {
                "output": str(args.output),
                "publication_candidate_records": contract[
                    "publication_candidate_records"
                ],
                "rootsi_crosswalk_records": contract["rootsi_crosswalk_records"],
                "reproduction_ready_records": 0,
                "whole_paper_reproduction_certified": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
