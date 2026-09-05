from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path

from .source_capabilities import (
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
    build_source_capability_audit_payload,
    build_source_capability_contract_payload,
)

__all__ = [
    "SourceFamilyContract",
    "SourceFamilyLayerContract",
    "SourceFamilyStateRow",
    "build_source_family_contract_payload",
    "build_source_family_contracts",
    "build_source_family_state_matrix_payload",
    "build_source_family_state_rows",
]


@dataclass(frozen=True)
class SourceFamilyLayerContract:
    layer_key: str
    repository_path: str
    required: bool
    purpose: str
    example_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class SourceFamilyContract:
    source_key: str
    display_name: str
    domain_group: str
    evidence_role: str
    primary_question: str
    raw_layer: SourceFamilyLayerContract
    normalized_layer: SourceFamilyLayerContract
    reviewed_layer: SourceFamilyLayerContract
    published_layer: SourceFamilyLayerContract
    coverage_metric_keys: tuple[str, ...]


@dataclass(frozen=True)
class SourceFamilyStateRow:
    source_key: str
    display_name: str
    domain_group: str
    evidence_role: str
    primary_question: str
    raw_status: str
    normalized_status: str
    reviewed_status: str
    published_status: str
    provenance_depth: str
    publication_posture: str
    authority_status: str
    authority_reasons: tuple[str, ...]
    coverage_metrics: dict[str, int | None]
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True)
class _SourceAuthorityState:
    status: str
    reason_codes: tuple[str, ...]
    governed_metrics: dict[str, int | None] | None = None


def build_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    """Build the durable layer contracts for every tracked source family."""
    return (
        SourceFamilyContract(
            source_key="landclim",
            display_name="LandClim pollen context",
            domain_group="pollen_context",
            evidence_role="primary_context",
            primary_question=(
                "Which tracked LandClim pollen-site records exist and survive "
                "normalization into map-ready context layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/landclim/raw",
                required=True,
                purpose="tracked upstream pollen-site source capture",
                example_artifacts=("data/landclim/raw/landclim_sources.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/landclim/normalized",
                required=True,
                purpose="tracked pollen-site and grid outputs prepared for interpretation",
                example_artifacts=(
                    "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
                    "data/landclim/normalized/nordic_reveals_grid_cells.geojson",
                    "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson",
                    "data/landclim/normalized/landclim_bibliography.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/landclim/review",
                required=True,
                purpose="source-specific review of temporal support and normalization quality",
                example_artifacts=("data/landclim/review/spatiotemporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published pollen-context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
                    "docs/report/regions/nordic/nordic_reveals_temporal_grid_cells.geojson",
                ),
            ),
            coverage_metric_keys=(
                "landclim_site_count",
                "landclim_grid_cell_count",
                "landclim_temporal_grid_feature_count",
            ),
        ),
        SourceFamilyContract(
            source_key="neotoma",
            display_name="Neotoma pollen context",
            domain_group="pollen_context",
            evidence_role="primary_context",
            primary_question=(
                "Which tracked Neotoma pollen records survive normalization and "
                "remain visible in atlas-ready context layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/neotoma/raw",
                required=True,
                purpose="tracked Neotoma acquisition and downloaded source tables",
                example_artifacts=("data/neotoma/raw/neotoma_pollen_sites.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/neotoma/normalized",
                required=True,
                purpose="tracked normalized Neotoma context ready for downstream layering",
                example_artifacts=(
                    "data/neotoma/normalized/nordic_pollen_sites.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/neotoma/review",
                required=True,
                purpose="site-level temporal comparability review for Neotoma pollen context",
                example_artifacts=("data/neotoma/review/temporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published Neotoma context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
                ),
            ),
            coverage_metric_keys=("neotoma_point_count",),
        ),
        SourceFamilyContract(
            source_key="sead",
            display_name="SEAD archaeology context",
            domain_group="archaeology_context",
            evidence_role="contextual_domain",
            primary_question=(
                "Which SEAD records are captured, normalized, and still safe to use "
                "as contextual archaeology layers?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/sead/raw",
                required=True,
                purpose="admitted SEAD acquisition and exact site payload capture",
                example_artifacts=(
                    SEAD_ADMITTED_ACQUISITION_ADMISSION,
                    SEAD_ADMITTED_ACQUISITION_ADMISSION.replace(
                        "admission.json", "payloads/tbl_sites.json"
                    ),
                ),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/sead/normalized",
                required=True,
                purpose="tracked normalized SEAD context ready for downstream use",
                example_artifacts=(
                    "data/sead/normalized/nordic_environmental_sites.geojson",
                    "data/sead/normalized/nordic_temporal_evidence.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/sead/review",
                required=True,
                purpose="site-level access, temporal, and normalization-legibility review for SEAD archaeology context",
                example_artifacts=(
                    "data/sead/review/evidence_legibility_review.json",
                    "data/sead/review/access_model.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published archaeology context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_environmental_sites.geojson",
                    "docs/report/regions/nordic/nordic_temporal_evidence.geojson",
                ),
            ),
            coverage_metric_keys=("sead_point_count",),
        ),
        SourceFamilyContract(
            source_key="raa",
            display_name="RAÄ archaeology context",
            domain_group="archaeology_context",
            evidence_role="contextual_domain",
            primary_question=(
                "Which Sweden-scoped archaeology context layers are captured and "
                "published from RAÄ?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/raa/raw",
                required=True,
                purpose="tracked RAÄ source capture",
                example_artifacts=("data/raa/raw/fornsok_domains.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/raa/normalized",
                required=True,
                purpose="tracked normalized archaeology layers used in density and map products",
                example_artifacts=(
                    "data/raa/normalized/sweden_archaeology_layer.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/raa/review",
                required=True,
                purpose="source-specific review of temporal support and publication limits",
                example_artifacts=("data/raa/review/spatiotemporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published archaeology density and context layers",
                example_artifacts=(
                    "docs/report/regions/nordic/sweden_archaeology_density.geojson",
                ),
            ),
            coverage_metric_keys=("raa_total_site_count", "raa_heritage_site_count"),
        ),
        SourceFamilyContract(
            source_key="boundaries",
            display_name="Boundary framing",
            domain_group="framing_context",
            evidence_role="framing_domain",
            primary_question=(
                "Which tracked framing geometries constrain interpretation of country "
                "and atlas outputs?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/boundaries/raw",
                required=True,
                purpose="tracked upstream boundary geometry capture",
                example_artifacts=("data/boundaries/raw/sweden.geojson",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/boundaries/normalized",
                required=True,
                purpose="tracked normalized boundary layers ready for publication",
                example_artifacts=(
                    "data/boundaries/normalized/nordic_country_boundaries.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/boundaries/review",
                required=True,
                purpose="source-specific review of geometry coverage and framing limits",
                example_artifacts=(
                    "data/boundaries/review/boundary_review.json",
                    "data/boundaries/review/manifest.json",
                    "data/boundaries/review/country-decisions/animal_adna.json",
                    "data/boundaries/review/country-decisions/landclim.json",
                    "data/boundaries/review/country-decisions/neotoma.json",
                    "data/boundaries/review/country-decisions/sead.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published boundary layers used in map framing",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_country_boundaries.geojson",
                ),
            ),
            coverage_metric_keys=("boundary_country_count",),
        ),
        SourceFamilyContract(
            source_key="svar",
            display_name="SMHI SVAR lake registry",
            domain_group="hydrography_context",
            evidence_role="sampling_domain",
            primary_question=(
                "Which official Sweden lake-register geometries and stable lake "
                "identities are available for sampling-oriented ranking?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/svar/raw",
                required=True,
                purpose="tracked SMHI SVAR WFS capture metadata and source manifest",
                example_artifacts=("data/svar/raw/svar_lake_registry_manifest.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/svar/normalized",
                required=True,
                purpose="tracked normalized Sweden lake registry with stable lake identities and geometry",
                example_artifacts=(
                    "data/svar/normalized/sweden_lake_registry.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/svar/review",
                required=True,
                purpose="source-specific review of evidence-linked lake identity, area, and sampling readiness",
                example_artifacts=(
                    "data/svar/review/lake_candidate_registry_review.json",
                    "data/svar/review/sweden_lake_candidate_registry.geojson",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/countries/sweden",
                required=True,
                purpose="published Sweden lake ranking and fieldwork surfaces derived from the official lake registry",
                example_artifacts=(
                    "docs/report/countries/sweden/sweden_lake_evidence_richness_v66.geojson",
                ),
            ),
            coverage_metric_keys=("svar_lake_count",),
        ),
        SourceFamilyContract(
            source_key="aadr",
            display_name="AADR human ancient DNA",
            domain_group="human_ancient_dna",
            evidence_role="direct_evidence_domain",
            primary_question=(
                "Which tracked human ancient-DNA inputs and normalized records exist "
                "under the governed AADR program?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/aadr",
                required=True,
                purpose="tracked AADR versioned source files",
                example_artifacts=("data/aadr/v66",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/adna/species/homo_sapiens/normalized",
                required=True,
                purpose="tracked governed Homo sapiens normalized outputs",
                example_artifacts=("data/adna/species/homo_sapiens/normalized",),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/adna/species/homo_sapiens/review",
                required=True,
                purpose="review-ready Homo sapiens package artifacts",
                example_artifacts=("data/adna/species/homo_sapiens/review",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report",
                required=True,
                purpose="country and atlas outputs that consume governed AADR records",
                example_artifacts=("docs/report/published_reports_summary.json",),
            ),
            coverage_metric_keys=("aadr_file_count",),
        ),
        SourceFamilyContract(
            source_key="animal_adna",
            display_name="Animal ancient DNA recovery",
            domain_group="animal_ancient_dna",
            evidence_role="sample_owned_evidence_domain",
            primary_question=(
                "Which animal ancient-DNA records are only captured, which are "
                "normalized, and which are safe for public publication?"
            ),
            raw_layer=SourceFamilyLayerContract(
                layer_key="raw",
                repository_path="data/adna/governance/source_library",
                required=True,
                purpose=(
                    "tracked project, paper, archive, and supplement capture for the "
                    "animal recovery program"
                ),
                example_artifacts=(
                    "data/adna/governance/source_library/project_registry.json",
                ),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/adna/species",
                required=True,
                purpose=(
                    "species-owned normalized sample, locality, chronology, and "
                    "coordinate evidence"
                ),
                example_artifacts=(
                    "data/adna/species/equus_caballus/normalized/sample_records.json",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/adna/governance",
                required=True,
                purpose="cross-species review, curation, and evidence-honesty artifacts",
                example_artifacts=(
                    "data/adna/governance/animal_sample_foundation_truth.json",
                ),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="data/adna/final",
                required=True,
                purpose="shared publication-ready animal bundles and atlas candidate surfaces",
                example_artifacts=(
                    "data/adna/final/atlas/animal_atlas_point_candidates.json",
                ),
            ),
            coverage_metric_keys=(
                "animal_species_count",
                "animal_project_count",
                "animal_sample_count",
            ),
        ),
    )


def build_source_family_contract_payload() -> dict[str, object]:
    """Build a machine-readable contract payload for every tracked source family."""
    rows = []
    for contract in build_source_family_contracts():
        payload = asdict(contract)
        payload["layer_contracts"] = {
            "raw": asdict(contract.raw_layer),
            "normalized": asdict(contract.normalized_layer),
            "reviewed": asdict(contract.reviewed_layer),
            "published": asdict(contract.published_layer),
        }
        rows.append(payload)
    return {
        "schema_version": "source-family-contracts.v1",
        "row_count": len(rows),
        "rows": rows,
        "capability_contract": build_source_capability_contract_payload(),
    }


def build_source_family_state_rows(
    output_root: Path,
    *,
    counts: Mapping[str, int],
) -> tuple[SourceFamilyStateRow, ...]:
    """Build one durable state row per tracked source family."""
    output_root = Path(output_root)
    states: list[SourceFamilyStateRow] = []
    for contract in build_source_family_contracts():
        authority = _source_authority_state(output_root, contract.source_key)
        raw_status = _layer_status(output_root, contract.raw_layer)
        normalized_status = _layer_status(output_root, contract.normalized_layer)
        reviewed_status = _layer_status(output_root, contract.reviewed_layer)
        published_layer_status = _layer_status(output_root, contract.published_layer)
        published_status = (
            "refused"
            if contract.source_key == "raa" and authority.status == "refused"
            else published_layer_status
        )
        coverage_metrics = _coverage_metrics(
            output_root,
            counts,
            contract.source_key,
            governed_metrics=authority.governed_metrics,
        )
        states.append(
            SourceFamilyStateRow(
                source_key=contract.source_key,
                display_name=contract.display_name,
                domain_group=contract.domain_group,
                evidence_role=contract.evidence_role,
                primary_question=contract.primary_question,
                raw_status=raw_status,
                normalized_status=normalized_status,
                reviewed_status=reviewed_status,
                published_status=published_status,
                provenance_depth=_provenance_depth(
                    raw_status=raw_status,
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                ),
                publication_posture=_publication_posture(
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                    published_status=published_status,
                    authority_status=authority.status,
                ),
                authority_status=authority.status,
                authority_reasons=authority.reason_codes,
                coverage_metrics=coverage_metrics,
                blocking_reasons=_blocking_reasons(
                    raw_status=raw_status,
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                    published_status=published_status,
                    coverage_metrics=coverage_metrics,
                    authority_status=authority.status,
                    authority_reasons=authority.reason_codes,
                ),
            )
        )
    return tuple(states)


def build_source_family_state_matrix_payload(
    output_root: Path,
    *,
    counts: Mapping[str, int],
) -> dict[str, object]:
    """Build a machine-readable evidence-stage matrix across tracked source families."""
    state_rows = build_source_family_state_rows(output_root, counts=counts)
    rows = [asdict(row) for row in state_rows]
    return {
        "schema_version": "source-family-evidence-stage-matrix.v2",
        "row_count": len(rows),
        "rows": rows,
        "capability_materialization_audit": build_source_capability_audit_payload(
            output_root,
            coverage_metrics_by_source={
                row.source_key: row.coverage_metrics for row in state_rows
            },
            source_blockers={
                row.source_key: row.blocking_reasons for row in state_rows
            },
        ),
    }


def _layer_status(output_root: Path, contract: SourceFamilyLayerContract) -> str:
    has_evidence = all(
        _path_has_governed_content(_resolve_repository_path(output_root, artifact_path))
        for artifact_path in contract.example_artifacts
    )
    if not contract.required and not has_evidence:
        return "optional_absent"
    return "present" if has_evidence else "missing"


def _resolve_repository_path(output_root: Path, repository_path: str) -> Path:
    if repository_path == "data":
        return output_root
    if repository_path.startswith("data/"):
        return output_root / repository_path.removeprefix("data/")
    return output_root.parent / repository_path


def _path_has_governed_content(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return not path.name.startswith(".") and path.stat().st_size > 0
    if path.is_dir():
        return any(
            child.is_file()
            and not child.name.startswith(".")
            and child.stat().st_size > 0
            for child in path.rglob("*")
        )
    return False


def _provenance_depth(
    *, raw_status: str, normalized_status: str, reviewed_status: str
) -> str:
    if (
        raw_status == "present"
        and normalized_status == "present"
        and reviewed_status == "present"
    ):
        return "review_ready"
    if raw_status == "present" and normalized_status == "present":
        return "normalized_without_review_layer"
    if raw_status == "present":
        return "captured_only"
    return "missing_source_capture"


def _publication_posture(
    *,
    normalized_status: str,
    reviewed_status: str,
    published_status: str,
    authority_status: str,
) -> str:
    if authority_status == "refused":
        return "refused_not_publication_ready"
    if authority_status == "review_required":
        return "review_required_not_publication_ready"
    if (
        normalized_status == "present"
        and reviewed_status == "present"
        and published_status == "present"
    ):
        return "published_with_review_support"
    if normalized_status == "present" and reviewed_status == "present":
        return "review_ready_not_yet_published"
    if normalized_status == "present":
        return "normalized_but_thin"
    return "not_publication_ready"


def _blocking_reasons(
    *,
    raw_status: str,
    normalized_status: str,
    reviewed_status: str,
    published_status: str,
    coverage_metrics: Mapping[str, int | None],
    authority_status: str,
    authority_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if raw_status == "missing":
        reasons.append("missing_raw_capture")
    if normalized_status == "missing":
        reasons.append("missing_normalized_outputs")
    if reviewed_status == "missing":
        reasons.append("missing_review_surface")
    if published_status == "missing":
        reasons.append("missing_published_surface")
    if authority_status == "refused":
        reasons.append("source_authority_refused")
    elif authority_status == "review_required":
        reasons.append("source_authority_review_required")
    reasons.extend(authority_reasons)
    governed_values = [
        value for value in coverage_metrics.values() if value is not None
    ]
    if coverage_metrics and not governed_values:
        reasons.append("unavailable_governed_coverage_metrics")
    elif not coverage_metrics or not any(value > 0 for value in governed_values):
        reasons.append("zero_coverage_metrics")
    return tuple(dict.fromkeys(reasons))


def _source_authority_state(
    output_root: Path, source_key: str
) -> _SourceAuthorityState:
    if source_key == "raa":
        from .sources.raa.authority import assess_raa_density_authority

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
    return _SourceAuthorityState(status="not_required", reason_codes=())


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
    from .boundaries import (
        BOUNDARY_CODES,
        NATURAL_EARTH_ADMIN0_URL,
        NATURAL_EARTH_TERMS_URL,
        NATURAL_EARTH_VERSION,
    )
    from .sources.boundaries.store import load_country_boundaries

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


def _coverage_metrics(
    output_root: Path,
    counts: Mapping[str, int],
    source_key: str,
    *,
    governed_metrics: Mapping[str, int | None] | None,
) -> dict[str, int | None]:
    if governed_metrics is not None:
        return dict(governed_metrics)
    if source_key == "landclim":
        return {
            "landclim_site_count": int(counts.get("landclim_site_count", 0)),
            "landclim_grid_cell_count": int(counts.get("landclim_grid_cell_count", 0)),
            "landclim_temporal_grid_feature_count": int(
                counts.get("landclim_temporal_grid_feature_count", 0)
            ),
        }
    if source_key == "neotoma":
        return {"neotoma_point_count": int(counts.get("neotoma_point_count", 0))}
    if source_key == "sead":
        return {"sead_point_count": int(counts.get("sead_point_count", 0))}
    if source_key == "aadr":
        return {"aadr_file_count": int(counts.get("aadr_file_count", 0))}
    if source_key == "animal_adna":
        return _animal_adna_metrics(output_root)
    return {}


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


def _geojson_feature_count(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        return 0
    return len(features)


def _animal_adna_metrics(output_root: Path) -> dict[str, int | None]:
    species_root = output_root / "adna" / "species"
    source_library_root = output_root / "adna" / "governance" / "source_library"
    truth_path = (
        output_root / "adna" / "governance" / "animal_sample_foundation_truth.json"
    )
    sample_count = 0
    project_count = 0
    if truth_path.is_file():
        payload = json.loads(truth_path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        if isinstance(summary, dict):
            sample_count = int(summary.get("sample_row_count", 0))
    project_registry = source_library_root / "project_registry.json"
    if project_registry.is_file():
        payload = json.loads(project_registry.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
        if isinstance(rows, list):
            project_count = len(rows)
    species_count = (
        sum(
            1
            for child in species_root.iterdir()
            if child.is_dir() and child.name != "homo_sapiens"
        )
        if species_root.is_dir()
        else 0
    )
    return {
        "animal_species_count": species_count,
        "animal_project_count": project_count,
        "animal_sample_count": sample_count,
    }
