from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
from pathlib import Path

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
    coverage_metrics: dict[str, int]
    blocking_reasons: tuple[str, ...]


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
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/sead/review",
                required=True,
                purpose="site-level temporal review of SEAD period, duration, and uncertainty semantics",
                example_artifacts=("data/sead/review/temporal_review.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published pollen-context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
                ),
            ),
            coverage_metric_keys=("landclim_site_count", "landclim_grid_cell_count"),
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
                example_artifacts=("data/neotoma/normalized/nordic_pollen_sites.geojson",),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/source_family_evidence_stage_matrix.json",
                required=True,
                purpose="cross-family review of freshness, coverage, and publication posture",
                example_artifacts=("data/source_family_evidence_stage_matrix.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published Neotoma context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_environmental_sites.geojson",
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
                purpose="tracked SEAD site inventory and source payload capture",
                example_artifacts=("data/sead/raw/nordic_sites.json",),
            ),
            normalized_layer=SourceFamilyLayerContract(
                layer_key="normalized",
                repository_path="data/sead/normalized",
                required=True,
                purpose="tracked normalized SEAD context ready for downstream use",
                example_artifacts=(
                    "data/sead/normalized/nordic_environmental_sites.geojson",
                ),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/source_family_evidence_stage_matrix.json",
                required=True,
                purpose="cross-family review of freshness, coverage, and publication posture",
                example_artifacts=("data/source_family_evidence_stage_matrix.json",),
            ),
            published_layer=SourceFamilyLayerContract(
                layer_key="published",
                repository_path="docs/report/world",
                required=True,
                purpose="published archaeology context layers used in atlas outputs",
                example_artifacts=(
                    "docs/report/regions/nordic/nordic_environmental_sites.geojson",
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
                example_artifacts=("data/raa/normalized/sweden_archaeology_layer.json",),
            ),
            reviewed_layer=SourceFamilyLayerContract(
                layer_key="reviewed",
                repository_path="data/source_family_evidence_stage_matrix.json",
                required=True,
                purpose="cross-family review of freshness, coverage, and publication posture",
                example_artifacts=("data/source_family_evidence_stage_matrix.json",),
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
                repository_path="data/source_family_evidence_stage_matrix.json",
                required=True,
                purpose="cross-family review of framing coverage and publication posture",
                example_artifacts=("data/source_family_evidence_stage_matrix.json",),
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
        raw_status = _layer_status(output_root, contract.raw_layer)
        normalized_status = _layer_status(output_root, contract.normalized_layer)
        reviewed_status = _layer_status(output_root, contract.reviewed_layer)
        published_status = _layer_status(output_root, contract.published_layer)
        coverage_metrics = _coverage_metrics(output_root, counts, contract.source_key)
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
                ),
                coverage_metrics=coverage_metrics,
                blocking_reasons=_blocking_reasons(
                    raw_status=raw_status,
                    normalized_status=normalized_status,
                    reviewed_status=reviewed_status,
                    published_status=published_status,
                    coverage_metrics=coverage_metrics,
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
    rows = [asdict(row) for row in build_source_family_state_rows(output_root, counts=counts)]
    return {
        "schema_version": "source-family-evidence-stage-matrix.v1",
        "row_count": len(rows),
        "rows": rows,
    }


def _layer_status(output_root: Path, contract: SourceFamilyLayerContract) -> str:
    path = _resolve_repository_path(output_root, contract.repository_path)
    if not contract.required and not _path_has_content(path):
        return "optional_absent"
    return "present" if _path_has_content(path) else "missing"


def _resolve_repository_path(output_root: Path, repository_path: str) -> Path:
    if repository_path == "data":
        return output_root
    if repository_path.startswith("data/"):
        return output_root / repository_path.removeprefix("data/")
    return output_root.parent / repository_path


def _path_has_content(path: Path) -> bool:
    if not path.exists():
        return False
    if path.is_file():
        return path.stat().st_size > 0
    if path.is_dir():
        return any(child.is_file() for child in path.rglob("*"))
    return False


def _provenance_depth(
    *, raw_status: str, normalized_status: str, reviewed_status: str
) -> str:
    if raw_status == "present" and normalized_status == "present" and reviewed_status == "present":
        return "review_ready"
    if raw_status == "present" and normalized_status == "present":
        return "normalized_without_review_layer"
    if raw_status == "present":
        return "captured_only"
    return "missing_source_capture"


def _publication_posture(
    *, normalized_status: str, reviewed_status: str, published_status: str
) -> str:
    if normalized_status == "present" and reviewed_status == "present" and published_status == "present":
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
    coverage_metrics: Mapping[str, int],
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
    if not coverage_metrics or not any(value > 0 for value in coverage_metrics.values()):
        reasons.append("zero_coverage_metrics")
    return tuple(reasons)


def _coverage_metrics(
    output_root: Path, counts: Mapping[str, int], source_key: str
) -> dict[str, int]:
    if source_key == "landclim":
        return {
            "landclim_site_count": int(counts.get("landclim_site_count", 0)),
            "landclim_grid_cell_count": int(counts.get("landclim_grid_cell_count", 0)),
        }
    if source_key == "neotoma":
        return {"neotoma_point_count": int(counts.get("neotoma_point_count", 0))}
    if source_key == "sead":
        return {"sead_point_count": int(counts.get("sead_point_count", 0))}
    if source_key == "raa":
        return {
            "raa_total_site_count": int(counts.get("raa_total_site_count", 0)),
            "raa_heritage_site_count": int(counts.get("raa_heritage_site_count", 0)),
        }
    if source_key == "boundaries":
        return {
            "boundary_country_count": _geojson_feature_count(
                output_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
            )
        }
    if source_key == "aadr":
        return {"aadr_file_count": int(counts.get("aadr_file_count", 0))}
    if source_key == "animal_adna":
        return _animal_adna_metrics(output_root)
    return {}


def _geojson_feature_count(path: Path) -> int:
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        return 0
    return len(features)


def _animal_adna_metrics(output_root: Path) -> dict[str, int]:
    species_root = output_root / "adna" / "species"
    source_library_root = output_root / "adna" / "governance" / "source_library"
    truth_path = output_root / "adna" / "governance" / "animal_sample_foundation_truth.json"
    sample_count = 0
    project_count = 0
    if truth_path.is_file():
        payload = json.loads(truth_path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        if isinstance(summary, dict):
            sample_count = int(summary.get("curated_sample_row_count", 0))
    project_registry = source_library_root / "project_registry.json"
    if project_registry.is_file():
        payload = json.loads(project_registry.read_text(encoding="utf-8"))
        rows = payload.get("rows", [])
        if isinstance(rows, list):
            project_count = len(rows)
    species_count = (
        sum(1 for child in species_root.iterdir() if child.is_dir() and child.name != "homo_sapiens")
        if species_root.is_dir()
        else 0
    )
    return {
        "animal_species_count": species_count,
        "animal_project_count": project_count,
        "animal_sample_count": sample_count,
    }
