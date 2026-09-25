"""Keep dev tools on explicitly reviewed host integration surfaces."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEV_SRC = REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "src"

# Dev is an installed client of the host package. Each use of host code must be
# reviewed here by file, module and imported symbol; the default is refusal.
# scientific_evidence reads two private constants to verify generated evidence,
# not to run the application. Keep those exact names visible until a public
# verification facade replaces them.
APPROVED_HOST_IMPORTS: dict[str, dict[str, frozenset[str]]] = {
    "bijux_pollenomics_dev/ci/atlas_browser/artifact_candidate.py": {
        "bijux_pollenomics.analysis.lra.api": frozenset({"read_lra_product"}),
    },
    "bijux_pollenomics_dev/ci/atlas_media/gallery.py": {
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {"build_neotoma_source_label_preset_catalog"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_media/publication.py": {
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {"NEOTOMA_SOURCE_LABEL_PRESETS"}
        ),
    },
    "bijux_pollenomics_dev/ci/atlas_media/source_authority.py": {
        "bijux_pollenomics.reporting.source_chronology.source_label_presets": frozenset(
            {
                "MEMBERSHIP_SEMANTICS",
                "NEOTOMA_SOURCE_LABEL_PRESETS",
                "NEOTOMA_SOURCE_LABEL_TAXA",
                "build_neotoma_source_label_preset_catalog",
            }
        ),
    },
    "bijux_pollenomics_dev/ci/scientific_evidence.py": {
        "bijux_pollenomics.analysis.propagation.outputs": frozenset(
            {
                "PROPAGATION_PRODUCER_ID",
                "PROPAGATION_PRODUCER_SOURCE_PATHS",
                "PROPAGATION_PRODUCER_VERSION",
                "PropagationMaterializationResult",
                "PropagationOutputRefusalError",
                "materialize_propagation_outputs",
            }
        ),
        "bijux_pollenomics.analysis.propagation.outputs.models": frozenset(
            {"_CLASSIFICATION_AUTHORITY", "_OUTPUT_NAMES"}
        ),
        "bijux_pollenomics.evidence.classification.audit_outputs": frozenset(
            {
                "ClassificationAuditMaterializationResult",
                "ClassificationAuditOutputPaths",
                "ClassificationAuditRefusalError",
                "materialize_classification_audit",
            }
        ),
        "bijux_pollenomics.evidence.classification.audit_outputs.constants": frozenset(
            {"OUTPUT_NAMES"}
        ),
        "bijux_pollenomics.evidence.classification.neotoma": frozenset(
            {"build_neotoma_classification_accounting"}
        ),
        "bijux_pollenomics.evidence.sources.neotoma": frozenset(
            {"read_validated_neotoma_relational_manifest"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/comparison.py": {
        "bijux_pollenomics.collection.sources.landclim.published_inventory": frozenset(
            {"LandClimPublishedEstimateInventory"}
        ),
        "bijux_pollenomics.collection.sources.landclim.published_inventory.contracts": frozenset(
            {"EVIDENCE_ROLE", "VALUE_UNIT"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/fitted_prediction.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"Fold", "SiteRecord"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {
                "HALF_COUNT",
                "HALF_COUNT_POLICY",
                "SiteCoordinate",
                "SpatialConfig",
                "fit_spatial_model",
                "half_count_composition",
            }
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_block_holdouts"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/hellinger_comparison.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/prediction.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"Fold", "SiteRecord"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_block_holdouts"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/scoring.py": {
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"HALF_COUNT", "HALF_COUNT_POLICY"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/source.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"site_group_id"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/observed_pollen_baseline.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "site_group_id"}
        ),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.splits": frozenset(
            {"grouped_leave_one_out"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/published_window_alignment.py": {
        "bijux_pollenomics.collection.sources.landclim.catalog": frozenset(
            {"time_window_from_tw_filename"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/published_window_correspondence.py": {
        "bijux_pollenomics.collection.sources.landclim.catalog": frozenset(
            {"time_window_from_tw_filename"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/rootsi_input_closure.py": {
        "bijux_pollenomics.collection.sources.landclim.study_inventory": frozenset(
            {
                "LandClimStudyMetadataInventory",
                "StudyMetadataRecord",
                "read_landclim_study_inventory",
                "reopen_landclim_study_inventory",
            }
        ),
        "bijux_pollenomics.collection.sources.rootsi": frozenset(
            {"RootsiSiteMetadataClaim", "normalize_rootsi_site_metadata"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.authority": frozenset(
            {"ARCHIVE_SHA256", "METADATA_MEMBER", "METADATA_SHA256"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.cells": frozenset(
            {"read_rootsi_cell_review"}
        ),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/essd_reproduction/rootsi_workbook_replay.py": {
        "bijux_pollenomics.collection.sources.rootsi": frozenset(
            {
                "RootsiSiteMetadataClaim",
                "normalize_rootsi_site_metadata",
            }
        ),
        "bijux_pollenomics.collection.sources.rootsi.authority": frozenset(
            {"ARCHIVE_SHA256", "METADATA_MEMBER", "METADATA_SHA256"}
        ),
        "bijux_pollenomics.collection.sources.rootsi.cells": frozenset(
            {"replay_rootsi_cell_review"}
        ),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/source_completion/abborrtjarne_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/bokesjon_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/bussjosjon_native_counts.py": {
        "bijux_pollenomics.collection.sources.rootsi.cells.decoding": frozenset(
            {"parser"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/author_pollen_spatial/development_search.py": {
        "bijux_pollenomics.analysis.lra_validation.baselines": frozenset(
            {"predict_spatial_baseline"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset({"Fold"}),
        "bijux_pollenomics.analysis.lra_validation.metrics": frozenset(
            {"hellinger_distance", "score_pollen"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial": frozenset(
            {"SpatialConfig", "fit_spatial_model", "half_count_composition"}
        ),
        "bijux_pollenomics.analysis.lra_validation.spatial.configuration": frozenset(
            {"distance_km"}
        ),
    },
    "bijux_pollenomics_dev/essd_reproduction/study_inputs.py": {
        "bijux_pollenomics.collection.sources.landclim.study_inventory": frozenset(
            {
                "LandClimStudyMetadataInventory",
                "StudyMetadataRecord",
                "read_landclim_study_inventory",
                "reopen_landclim_study_inventory",
            }
        ),
    },
    "bijux_pollenomics_dev/lra_validation/experiment_ledger.py": {
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {"reopen_cohort_admission"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/admission.py": {
        "bijux_pollenomics.analysis.lra_validation.channels": frozenset(
            {"ObservationChannels", "PollenChannel"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "site_group_id"}
        ),
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {"ExternalInput", "Support"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/decisions.py": {
        "bijux_pollenomics.analysis.lra_validation.channels": frozenset(
            {"ObservationChannels"}
        ),
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"SiteRecord", "canonical_json", "manifest_sha256"}
        ),
        "bijux_pollenomics.analysis.lra_validation.evaluation.api": frozenset(
            {
                "COHORT_DECISION_PROFILE",
                "EvaluationSite",
                "ExternalInput",
                "ReviewedEvaluationCohort",
                "admit_reviewed_evaluation_cohort",
            }
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/evidence.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
        "bijux_pollenomics.core.geospatial.distance": frozenset(
            {"wgs84_inverse_geodesic"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/parameters.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/pollen_index.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/projection.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json", "manifest_sha256"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/empd2_nfi_reference/taxon_mapping.py": {
        "bijux_pollenomics.analysis.lra_validation.contracts": frozenset(
            {"canonical_json"}
        ),
    },
    "bijux_pollenomics_dev/source_completion/hyde_nordic_window.py": {
        "bijux_pollenomics.collection.sources.hyde.ascii": frozenset(
            {"NativeAsciiWindow", "read_hyde_ascii_window"}
        ),
        "bijux_pollenomics.collection.sources.hyde.ascii.geometry": frozenset(
            {"native_axis_geometry"}
        ),
        "bijux_pollenomics.collection.sources.hyde.local.contracts": frozenset(
            {"checked_path", "decode", "digest", "encode", "sha256"}
        ),
        "bijux_pollenomics.collection.sources.hyde.netcdf": frozenset(
            {
                "HydeNetcdfDeclarationInventory",
                "read_hyde_netcdf_declaration_inventory",
            }
        ),
        "bijux_pollenomics.collection.sources.quarantine": frozenset({"IntakeRefusal"}),
        "bijux_pollenomics.core.owned_tree": frozenset({"publish_new_output_tree"}),
    },
    "bijux_pollenomics_dev/taxa_review/neotoma.py": {
        "bijux_pollenomics.evidence.classification": frozenset(
            {"build_neotoma_classification_accounting"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/__main__.py": {
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"read_neotoma_evidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/decisions.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"NeotomaEvidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/lra_prerequisites/projection.py": {
        "bijux_pollenomics.analysis.lra.materialization.models": frozenset(
            {"canonical_bytes"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.candidate_groups": frozenset(
            {"summarize_neotoma_candidate_groups"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.frontier": frozenset(
            {"assess_neotoma_lra_frontier"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.lakeparameters": frozenset(
            {"assess_neotoma_lakeparameters"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.pollen_screen": frozenset(
            {"assess_neotoma_pollen_screen"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence": frozenset(
            {"assess_neotoma_candidate_site_evidence"}
        ),
        "bijux_pollenomics.analysis.lra.materialization.reading": frozenset(
            {"NeotomaEvidence"}
        ),
    },
    "bijux_pollenomics_dev/taxa_review/sead.py": {
        "bijux_pollenomics.collection.sources.sead.evidence.review": frozenset(
            {"validate_sead_scientific_classification_review"}
        ),
    },
}


def host_import_violations(source: str, relative_path: str) -> tuple[str, ...]:
    """Inspect executable imports, excluding import-like text in strings/comments."""
    allowed = APPROVED_HOST_IMPORTS.get(relative_path, {})
    failures: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module != "bijux_pollenomics" and not module.startswith(
                "bijux_pollenomics."
            ):
                continue
            names = {alias.name for alias in node.names}
            if "*" in names or not names <= allowed.get(module, frozenset()):
                failures.append(
                    f"{relative_path}:{node.lineno} imports {module}: {sorted(names)}"
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "bijux_pollenomics" or alias.name.startswith(
                    "bijux_pollenomics."
                ):
                    failures.append(
                        f"{relative_path}:{node.lineno} imports {alias.name}"
                    )
        elif isinstance(node, ast.Call):
            dynamic = (
                isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
            if dynamic and node.args and isinstance(node.args[0], ast.Constant):
                target = node.args[0].value
                if isinstance(target, str) and (
                    target == "bijux_pollenomics"
                    or target.startswith("bijux_pollenomics.")
                ):
                    failures.append(
                        f"{relative_path}:{node.lineno} dynamically imports {target}"
                    )
    return tuple(failures)


def test_dev_package_uses_only_reviewed_host_imports() -> None:
    failures = [
        violation
        for path in sorted(DEV_SRC.rglob("*.py"))
        for violation in host_import_violations(
            path.read_text(encoding="utf-8"), path.relative_to(DEV_SRC).as_posix()
        )
    ]
    assert not failures, "unreviewed dev-to-host imports:\n" + "\n".join(failures)


def test_import_boundary_rejects_new_symbols_modules_and_dynamic_imports() -> None:
    path = "bijux_pollenomics_dev/taxa_review/neotoma.py"
    assert not host_import_violations(
        "from bijux_pollenomics.evidence.classification import build_neotoma_classification_accounting",
        path,
    )
    for source in (
        "from bijux_pollenomics.evidence.classification import unreviewed",
        "from bijux_pollenomics.evidence.sources.neotoma import read_validated_neotoma_relational_manifest",
        "import bijux_pollenomics.analysis.lra.api",
        "from bijux_pollenomics.evidence.classification import *",
        "__import__('bijux_pollenomics.analysis.lra.api')",
    ):
        assert host_import_violations(source, path)
    assert not host_import_violations(
        'script = "from bijux_pollenomics.analysis.lra.api import read_lra_product"',
        path,
    )
