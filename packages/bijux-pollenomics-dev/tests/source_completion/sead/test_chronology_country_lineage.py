"""Bind chronology-country reports to one exact reviewed source run and build."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import (
    sead_chronology_country_accounting as owner,
)


def _document(value: Mapping[str, object]) -> bytes:
    return (json.dumps(value, sort_keys=True) + "\n").encode()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inputs(*, review_run: str, review_build: str) -> dict[str, bytes]:
    claims = {
        "source_run_id": "run-a",
        "source_build_id": "build-a",
        "acquisition_bundle_sha256": "bundle-a",
        "acquisition_manifest_sha256": "manifest-a",
        "propagation_status": "refused",
        "propagation_reason_code": "source_classification_not_accepted",
        "claims": [],
        "claim_count": 0,
        "country_counts": {},
        "claim_type_counts": {},
        "comparability_counts": {},
        "chronology_eligibility_counts": {},
        "refusal_reason_counts": {},
    }
    claims_bytes = _document(claims)
    sites_bytes = b"record_id,country,site_uuid\n"
    review_csv = b"chronology_claim_id\n"
    lineage = {
        "normalized_surface_sha256": {
            "normalized/chronology_claims.json": _sha(claims_bytes),
            "normalized/nordic_environmental_sites.csv": _sha(sites_bytes),
        },
        "source_run_id": "run-a",
        "build_id": "build-a",
        "acquisition_bundle_sha256": "bundle-a",
        "acquisition_manifest_sha256": "manifest-a",
    }
    lineage_bytes = _document(lineage)
    review = {
        "claim_review_csv": {
            "path": "claims.csv",
            "sha256": _sha(review_csv),
            "row_count": 0,
        },
        "source_run_id": review_run,
        "source_build_id": review_build,
        "input_hashes": {"manifest_sha256": "manifest-a"},
        "claim_count": 0,
        "claim_type_counts": {},
        "comparability_counts": {},
        "chronology_eligibility_counts": {},
        "reviewed_age_basis_counts": {},
    }
    custody = {
        "source_run_id": "run-a",
        "acquisition_bundle_sha256": "bundle-a",
        "inputs_sha256": {
            owner.SITES.as_posix(): _sha(sites_bytes),
            owner.LINEAGE.as_posix(): _sha(lineage_bytes),
        },
    }
    return {
        owner.CLAIMS.as_posix(): claims_bytes,
        owner.LINEAGE.as_posix(): lineage_bytes,
        owner.SITES.as_posix(): sites_bytes,
        (owner.REVIEW / "claims.csv").as_posix(): review_csv,
        (owner.REVIEW / "report.json").as_posix(): _document(review),
        owner.CUSTODY.as_posix(): _document(custody),
    }


def _run_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    review_run: str,
    review_build: str,
) -> Path:
    contents = _inputs(review_run=review_run, review_build=review_build)
    monkeypatch.setattr(
        owner, "_read", lambda _repository, path: contents[path.as_posix()]
    )
    result = {
        "claim_count": 0,
        "country_counts": {},
        "claim_type_counts": {},
        "comparability_counts": {},
        "chronology_eligibility_counts": {},
        "reviewed_age_basis_counts": {},
        "chronology_refusal_reasons_by_country": {},
    }
    monkeypatch.setattr(
        owner,
        "account",
        lambda _claims, _reviews, _sites, _custody: ([], result.copy()),
    )
    repository = tmp_path / "repository"
    (repository / "artifacts").mkdir(parents=True)
    output = repository / "artifacts" / "country-claims"
    owner.run(repository, output)
    return output


def test_matching_run_and_build_are_accepted_for_source_accounting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = _run_case(
        tmp_path, monkeypatch, review_run="run-a", review_build="build-a"
    )
    assert json.loads((output / "report.json").read_bytes())["source_run_id"] == "run-a"
    assert (output / "rows.csv").read_text() == ",".join(owner.FIELDS) + "\n"


@pytest.mark.parametrize(
    ("review_run", "review_build"),
    [("run-b", "build-a"), ("run-a", "build-b")],
)
def test_changed_review_identity_is_refused_before_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    review_run: str,
    review_build: str,
) -> None:
    with pytest.raises(
        ValueError, match="source/review/public custody digests or lineage differ"
    ):
        _run_case(
            tmp_path, monkeypatch, review_run=review_run, review_build=review_build
        )
    assert not (tmp_path / "repository/artifacts/country-claims").exists()
