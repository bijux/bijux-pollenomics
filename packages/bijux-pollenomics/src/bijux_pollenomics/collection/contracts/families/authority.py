from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath

from ....config import DEFAULT_AADR_VERSION
from .models import _SourceAuthorityState


def _source_authority_state(
    output_root: Path,
    source_key: str,
    *,
    version: str = DEFAULT_AADR_VERSION,
) -> _SourceAuthorityState:
    if source_key == "raa":
        from ...sources.raa.authority import assess_raa_density_authority

        decision = assess_raa_density_authority(output_root)
        metrics: dict[str, int | None] = (
            {
                "raa_total_site_count": decision.archived_feature_count,
                "raa_heritage_site_count": decision.heritage_site_count,
            }
            if decision.admitted
            else {
                "raa_total_site_count": None,
                "raa_heritage_site_count": None,
            }
        )
        return _SourceAuthorityState(
            status="admitted" if decision.admitted else "refused",
            reason_codes=decision.reason_codes,
            governed_metrics=metrics,
        )
    if source_key == "boundaries":
        return _boundary_authority_state(output_root)
    if source_key == "svar":
        return _svar_authority_state(output_root)
    if source_key == "animal_adna":
        return _animal_adna_authority_state(output_root)
    if source_key == "aadr":
        return _aadr_authority_state(output_root, version=version)
    return _SourceAuthorityState(status="not_required", reason_codes=())


def _aadr_authority_state(
    output_root: Path,
    *,
    version: str = DEFAULT_AADR_VERSION,
) -> _SourceAuthorityState:
    from ...sources.aadr.materialization.accountability import (
        validate_aadr_source_accountability_receipt,
    )

    receipt_path = (
        output_root
        / "adna"
        / "species"
        / "homo_sapiens"
        / "review"
        / f"aadr_{version}_source_accountability.json"
    )
    try:
        receipt = _load_json_object(receipt_path)
        validate_aadr_source_accountability_receipt(receipt)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return _SourceAuthorityState(
            status="review_required",
            reason_codes=("missing_or_invalid_aadr_source_accountability",),
        )
    if receipt.get("source_release") != version:
        return _SourceAuthorityState(
            status="review_required",
            reason_codes=("aadr_source_accountability_release_mismatch",),
        )
    if not _aadr_receipt_inputs_are_current(
        output_root,
        receipt.get("input_artifacts"),
    ):
        return _SourceAuthorityState(
            status="review_required",
            reason_codes=("stale_or_unverifiable_aadr_source_accountability_inputs",),
        )
    return _SourceAuthorityState(
        status="review_required",
        reason_codes=("qualified_human_adna_source_review_missing",),
    )


def _aadr_receipt_inputs_are_current(
    output_root: Path,
    input_artifacts: object,
) -> bool:
    if output_root.is_symlink() or not isinstance(input_artifacts, list):
        return False
    root = output_root.resolve()
    for raw_artifact in input_artifacts:
        if not isinstance(raw_artifact, Mapping):
            return False
        logical_path = raw_artifact.get("path")
        expected_sha256 = raw_artifact.get("sha256")
        expected_byte_count = raw_artifact.get("byte_count")
        if (
            not isinstance(logical_path, str)
            or not isinstance(expected_sha256, str)
            or isinstance(expected_byte_count, bool)
            or not isinstance(expected_byte_count, int)
            or expected_byte_count < 0
        ):
            return False
        try:
            relative_path = PurePosixPath(logical_path).relative_to("data")
        except ValueError:
            return False
        physical_path = output_root.joinpath(*relative_path.parts)
        current = output_root
        path_uses_symlink = False
        for part in relative_path.parts:
            current /= part
            if current.is_symlink():
                path_uses_symlink = True
                break
        if path_uses_symlink:
            return False
        try:
            resolved_path = physical_path.resolve(strict=True)
            content = physical_path.read_bytes()
        except OSError:
            return False
        if (
            physical_path.is_symlink()
            or not physical_path.is_file()
            or root not in resolved_path.parents
            or len(content) != expected_byte_count
            or hashlib.sha256(content).hexdigest() != expected_sha256
        ):
            return False
    return True


def _animal_adna_authority_state(output_root: Path) -> _SourceAuthorityState:
    guard_path = (
        output_root
        / "adna"
        / "governance"
        / "source_library"
        / "source_recovery_release_guard.json"
    )
    review_path = (
        output_root / "adna" / "governance" / "animal_source_scientific_review.json"
    )
    reasons: list[str] = []
    try:
        guard = _load_json_object(guard_path)
        if guard.get("schema_version") != "animal-source-recovery-release-guard.v1":
            reasons.append("missing_or_invalid_animal_source_recovery_guard")
        elif guard.get("passing") is not True:
            reasons.append("animal_source_recovery_guard_failed")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        reasons.append("missing_or_invalid_animal_source_recovery_guard")

    experiment_only_count = 0
    for sample_master_path in output_root.glob(
        "adna/governance/source_library/projects/*/sample_master.json"
    ):
        try:
            sample_master = _load_json_object(sample_master_path)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            continue
        rows = sample_master.get("rows")
        if isinstance(rows, list):
            experiment_only_count += sum(
                1
                for row in rows
                if isinstance(row, dict)
                and row.get("source_native_identity_kind")
                == "sequencing_experiment_accession"
            )
    if experiment_only_count:
        reasons.append("experiment_to_biological_sample_mapping_unavailable")

    try:
        review = _load_json_object(review_path)
        review_accepted = (
            review.get("schema_version") == "animal-source-scientific-review.v1"
            and review.get("release_status") == "accepted"
            and isinstance(review.get("reviewer_id"), str)
            and bool(str(review["reviewer_id"]).strip())
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        review_accepted = False
    if not review_accepted:
        reasons.append("qualified_animal_source_review_missing")
    return _SourceAuthorityState(
        status="admitted" if not reasons else "review_required",
        reason_codes=tuple(reasons),
    )


def _boundary_authority_state(output_root: Path) -> _SourceAuthorityState:
    from ...sources.boundaries.collection import (
        BOUNDARY_CODES,
        NATURAL_EARTH_ADMIN0_URL,
        NATURAL_EARTH_TERMS_URL,
        NATURAL_EARTH_VERSION,
    )
    from ...sources.boundaries.store import load_country_boundaries

    family_root = output_root / "boundaries"
    normalized_path = family_root / "normalized" / "nordic_country_boundaries.geojson"
    manifest_path = family_root / "raw" / "source_manifest.json"
    try:
        boundaries = load_country_boundaries(
            output_root=family_root,
            boundary_codes=BOUNDARY_CODES,
            natural_earth_version=NATURAL_EARTH_VERSION,
            natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
            natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
        )
        manifest = _load_json_object(manifest_path)
        normalized = _load_json_object(normalized_path)
        normalized_record = _object(manifest.get("normalized_artifact"))
        features = _feature_list(normalized)
        expected_digest = normalized_record.get("sha256")
        actual_digest = hashlib.sha256(normalized_path.read_bytes()).hexdigest()
        if (
            boundaries is None
            or set(boundaries) != set(BOUNDARY_CODES)
            or normalized_record.get("path")
            != "normalized/nordic_country_boundaries.geojson"
            or expected_digest != actual_digest
            or normalized_record.get("feature_count") != len(features)
            or len(features) != len(BOUNDARY_CODES)
        ):
            raise ValueError("boundary authority does not reconcile")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return _SourceAuthorityState(
            status="refused",
            reason_codes=("missing_or_invalid_boundary_authority",),
            governed_metrics={"boundary_country_count": None},
        )

    review_path = family_root / "review" / "boundary_review.json"
    review_accepted = False
    try:
        review = _load_json_object(review_path)
        boundary_authority = _object(review.get("boundary_authority"))
        countries = review.get("countries")
        review_accepted = (
            review.get("schema_version") == "nordic-boundary-review.v1"
            and review.get("machine_validation_status") == "passed"
            and review.get("qualified_review_status") == "accepted"
            and review.get("release_status") == "accepted"
            and boundary_authority.get("version") == NATURAL_EARTH_VERSION
            and boundary_authority.get("normalized_artifact_sha256") == actual_digest
            and isinstance(countries, list)
            and len(countries) == len(BOUNDARY_CODES)
            and all(
                isinstance(country, Mapping)
                and country.get("qualified_review_status") == "accepted"
                and isinstance(country.get("qualified_reviewer"), str)
                and bool(str(country["qualified_reviewer"]).strip())
                for country in countries
            )
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass
    return _SourceAuthorityState(
        status="admitted" if review_accepted else "review_required",
        reason_codes=(
            () if review_accepted else ("qualified_boundary_inclusion_review_missing",)
        ),
        governed_metrics={"boundary_country_count": len(features)},
    )


def _svar_authority_state(output_root: Path) -> _SourceAuthorityState:
    family_root = output_root / "svar"
    manifest_path = family_root / "raw" / "svar_lake_registry_manifest.json"
    registry_path = family_root / "normalized" / "sweden_lake_registry.geojson"
    summary_path = family_root / "normalized" / "svar_summary.json"
    try:
        manifest = _load_json_object(manifest_path)
        registry = _load_json_object(registry_path)
        summary = _load_json_object(summary_path)
        features = _feature_list(registry)
        lake_count = len(features)
        if (
            manifest.get("source") != "SMHI SVAR"
            or summary.get("source") != "SMHI SVAR"
            or not features
            or _non_negative_int(manifest.get("matched_lake_count")) != lake_count
            or _non_negative_int(manifest.get("normalized_lake_count")) != lake_count
            or _non_negative_int(summary.get("lake_count")) != lake_count
        ):
            raise ValueError("SVAR authority counts do not reconcile")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return _SourceAuthorityState(
            status="refused",
            reason_codes=("missing_or_invalid_svar_authority",),
            governed_metrics={"svar_lake_count": None},
        )

    review_path = family_root / "review" / "lake_candidate_registry_review.json"
    review_surface = family_root / "review" / "sweden_lake_candidate_registry.geojson"
    review_accepted = False
    try:
        review = _load_json_object(review_path)
        review_registry = _load_json_object(review_surface)
        review_accepted = (
            bool(_feature_list(review_registry))
            and review.get("source") == "SMHI SVAR"
            and _non_negative_int(review.get("source_lake_count")) == lake_count
            and review.get("registry_sha256")
            == hashlib.sha256(registry_path.read_bytes()).hexdigest()
            and review.get("release_status") == "accepted"
            and isinstance(review.get("reviewer_id"), str)
            and bool(str(review["reviewer_id"]).strip())
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        pass
    return _SourceAuthorityState(
        status="admitted" if review_accepted else "review_required",
        reason_codes=(
            () if review_accepted else ("qualified_svar_publication_review_missing",)
        ),
        governed_metrics={"svar_lake_count": lake_count},
    )


def _load_json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Authority artifact must be an object: {path}")
    return payload


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Authority manifest record must be an object")
    return value


def _feature_list(payload: Mapping[str, object]) -> list[object]:
    if payload.get("type") != "FeatureCollection":
        raise ValueError("Authority geometry must be a FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Authority geometry must contain a feature list")
    return features


def _non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value
