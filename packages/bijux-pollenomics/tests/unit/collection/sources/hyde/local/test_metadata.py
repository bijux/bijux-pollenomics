from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.hyde.local.metadata import (
    review_hyde_native_metadata,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _write(path: Path, content: str) -> tuple[Path, str]:
    path.write_text(content)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _inputs(tmp_path: Path) -> dict[str, object]:
    license_path, license_hash = _write(
        tmp_path / "License.txt",
        "Attribution-NonCommercial 4.0 International\n",
    )
    readme_path, readme_hash = _write(
        tmp_path / "readme.txt",
        """README release HYDE version 3.5 (hyde35), d.d. March 2025.
The period covered is 10,000 BCE to 2023 CE.
Extension of the database to year 2025
The HYDE 3.3 release contains: a Baseline estimate scenario, a Lower estimate
scenario and an Upper estimate scenario. Files include 0AD.
The Creative Commons License (CC BY 3.0) applies to all HYDE data.
""",
    )
    yoda_path, yoda_hash = _write(
        tmp_path / "yoda.json",
        json.dumps(
            {
                "License": (
                    "Creative Commons Attribution-NonCommercial 4.0 "
                    "International Public License"
                ),
                "Description": (
                    "This HYDE version 3.5 replaces former HYDE 3.4. "
                    "The period covered is 10,000 BCE to 2024 CE. "
                    "Extension of the database to year 2025"
                ),
            }
        ),
    )
    custody_path, custody_hash = _write(
        tmp_path / "custody.json",
        json.dumps(
            {
                "status": "passed",
                "manifest_sha256": "a" * 64,
                "dataset_inventory_sha256": "b" * 64,
                "counts": {
                    "file_count": 3,
                    "dataset_file_count": 3,
                    "archive_file_count": 1,
                    "archive_member_count": 2,
                    "netcdf_named_file_count": 3,
                },
                "scientific_acceptance": "not_evaluated",
                "public_release_allowed": False,
            }
        ),
    )
    custody_files_path, custody_files_hash = _write(
        tmp_path / "files.json",
        json.dumps(
            [
                {"path": "original/base/anthromes/0AD_anthromes.zip"},
                {"path": "original/lower/2000AD_lu.zip"},
                {"path": "original/upper/2000AD_lu.zip"},
            ]
        ),
    )
    rows = []
    for scenario in ("base", "lower", "upper"):
        rows.append(
            {
                "path": f"original/gbc2025_7apr_{scenario}/NetCDF/cropland.nc",
                "attributes": {
                    "license": "The Creative Commons License (CC BY 3.0)",
                    "description": "HYDE3.4 test netCDF",
                    "version": "HYDE3.4",
                },
                "variables": {
                    "time": {
                        "attributes": {
                            "calendar": "365_day",
                            "units": "days since 1-5-1 00:00:00",
                        }
                    }
                },
            }
        )
    headers_path, headers_hash = _write(tmp_path / "headers.json", json.dumps(rows))
    return {
        "license_path": license_path,
        "license_sha256": license_hash,
        "readme_path": readme_path,
        "readme_sha256": readme_hash,
        "yoda_path": yoda_path,
        "yoda_sha256": yoda_hash,
        "custody_receipt_path": custody_path,
        "custody_receipt_sha256": custody_hash,
        "custody_files_path": custody_files_path,
        "custody_files_sha256": custody_files_hash,
        "netcdf_headers_path": headers_path,
        "netcdf_headers_sha256": headers_hash,
    }


def test_conflicting_declarations_remain_attributed_and_refused(tmp_path: Path) -> None:
    review = review_hyde_native_metadata(**_inputs(tmp_path))  # type: ignore[arg-type]
    payload = review.payload()
    assert payload["admission"] == {
        "native_release_status": "refused_pending_review",
        "scientific_acceptance": "not_evaluated",
        "public_release_allowed": False,
        "country_projection_allowed": False,
        "canonical_calendar_conversion_allowed": False,
        "required_reviews": [
            "qualified_release_identity",
            "qualified_release_specific_rights",
            "native_calendar_and_0ad_interpretation",
            "coverage_end_year",
            "scenario_uncertainty_semantics",
        ],
    }
    claims = payload["claims"]
    assert isinstance(claims, list)
    assert {row["value"] for row in claims if row["topic"] == "license"} == {
        "CC-BY-3.0",
        "CC-BY-NC-4.0",
        "Creative Commons Attribution-NonCommercial 4.0 International Public License",
        "The Creative Commons License (CC BY 3.0)",
    }
    assert {row["value"] for row in claims if row["topic"] == "coverage_end_year"} == {
        "2023",
        "2024",
        "2025",
    }
    assert {row["value"] for row in claims if row["topic"] == "calendar"} == {"365_day"}
    conflicts = payload["conflicts"]
    assert isinstance(conflicts, list)
    assert {
        "license_declaration_conflict",
        "release_identity_conflict",
        "coverage_end_year_conflict",
        "calendar_mapping_unresolved",
        "zero_ad_calendar_interpretation_unresolved",
    }.issubset(set(conflicts))


def test_scenarios_are_not_relabelled_confidence_bounds(tmp_path: Path) -> None:
    review = review_hyde_native_metadata(**_inputs(tmp_path))  # type: ignore[arg-type]
    scenario = review.payload()["scenario_semantics"]
    assert scenario == {
        "labels": ["base", "lower", "upper"],
        "netcdf_header_counts": {"base": 1, "lower": 1, "upper": 1},
        "role": "provider_estimate_scenarios",
        "confidence_bounds_status": "not_declared",
        "pointwise_ordering_contract": "none",
    }
    assert "scenario_uncertainty_semantics_unresolved" in review.conflicts


def test_same_pinned_inputs_produce_identical_canonical_review(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    first = review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
    second = review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256 == second.sha256


def test_release_claim_values_follow_attributed_source_bytes(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    readme = inputs["readme_path"]
    yoda = inputs["yoda_path"]
    assert isinstance(readme, Path) and isinstance(yoda, Path)
    readme.write_text(
        readme.read_text()
        .replace("version 3.5", "version 9.7")
        .replace("HYDE 3.3 release", "HYDE 8.2 release")
    )
    yoda_payload = json.loads(yoda.read_text())
    yoda_payload["Description"] = yoda_payload["Description"].replace(
        "version 3.5", "version 7.6"
    )
    yoda.write_text(json.dumps(yoda_payload))
    inputs["readme_sha256"] = hashlib.sha256(readme.read_bytes()).hexdigest()
    inputs["yoda_sha256"] = hashlib.sha256(yoda.read_bytes()).hexdigest()
    review = review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
    claims = review.payload()["claims"]
    assert isinstance(claims, list)
    assert {row["value"] for row in claims if row["topic"] == "release"} == {
        "7.6",
        "8.2",
        "9.7",
        "HYDE3.4",
    }


def test_digest_drift_refuses_before_interpretation(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    path = inputs["readme_path"]
    assert isinstance(path, Path)
    path.write_text(path.read_text() + "changed")
    with pytest.raises(IntakeRefusal, match="hyde_metadata_digest_mismatch"):
        review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]


def test_header_count_disagreement_is_preserved_as_conflict(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    custody = inputs["custody_receipt_path"]
    assert isinstance(custody, Path)
    payload = json.loads(custody.read_text())
    payload["counts"]["netcdf_named_file_count"] = 48
    custody.write_text(json.dumps(payload))
    inputs["custody_receipt_sha256"] = hashlib.sha256(custody.read_bytes()).hexdigest()
    review = review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
    assert "custody_netcdf_header_count_conflict" in review.conflicts


def test_missing_provider_claim_or_duplicate_json_key_refuses(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    readme = inputs["readme_path"]
    assert isinstance(readme, Path)
    readme.write_text(readme.read_text().replace("Upper estimate scenario", "upper"))
    inputs["readme_sha256"] = hashlib.sha256(readme.read_bytes()).hexdigest()
    with pytest.raises(IntakeRefusal, match="hyde_metadata_claim_missing"):
        review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
    yoda = inputs["yoda_path"]
    assert isinstance(yoda, Path)
    yoda.write_text('{"License":"first","License":"second"}')
    inputs["yoda_sha256"] = hashlib.sha256(yoda.read_bytes()).hexdigest()
    with pytest.raises(IntakeRefusal, match="hyde_metadata_json_duplicate_key"):
        review_hyde_native_metadata(**inputs)  # type: ignore[arg-type]
