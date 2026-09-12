"""Generate a derived closure view from the repository's existing authorities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import EvidenceReader, digest, indexed_rows
from .landclim import audit_landclim
from .manifests import audit_neotoma, audit_sead

_AUTHORITIES = {
    "families": "data/source_family_contracts.json",
    "stages": "data/source_family_evidence_stage_matrix.json",
    "countries": "data/country_dimension_coverage.json",
    "ownership": "data/source_fact_ownership_registry.json",
    "postures": "data/source_spatiotemporal_posture_registry.json",
}


def build_source_audit(root: Path) -> dict[str, Any]:
    """Preserve source status namespaces and test the pinned accounting evidence."""
    reader = EvidenceReader(root)
    authorities: dict[str, dict[str, Any]] = {}
    for key, path in _AUTHORITIES.items():
        payload = reader.json(path)
        if payload is None:
            raise ValueError(f"Missing governing registry: {path}")
        authorities[key] = payload
    families = indexed_rows(authorities["families"], "source_key")
    stages = indexed_rows(authorities["stages"], "source_key")
    postures = indexed_rows(authorities["postures"], "source_key")
    ownership = indexed_rows(authorities["ownership"], "fact_key")
    if set(families) != set(stages):
        reader.issue(
            "source_registry_identity_mismatch",
            _AUTHORITIES["stages"],
            only_contract=sorted(set(families) - set(stages)),
            only_stage=sorted(set(stages) - set(families)),
        )
    countries = authorities["countries"]["cells"]
    if authorities["countries"]["cell_count"] != len(countries):
        reader.issue("country_cell_count_mismatch", _AUTHORITIES["countries"])
    country_keys = [
        (c["source_family"], c["country_code"], c["country_dimension"])
        for c in countries
    ]
    if len(country_keys) != len(set(country_keys)):
        reader.issue("duplicate_country_dimension_identity", _AUTHORITIES["countries"])
    capabilities = authorities["stages"]["capability_materialization_audit"]["rows"]
    rows = []
    for key, family in sorted(families.items()):
        stage = stages.get(key)
        materialization = []
        for layer, contract in sorted(family["layer_contracts"].items()):
            files = []
            for path in contract["example_artifacts"]:
                if any(char in path for char in "<*>?"):
                    files.append({"path": path, "presence": "template_not_resolved"})
                else:
                    reader.read_bytes(path)
                    files.append(reader.files[path])
            materialization.append(
                {
                    "layer": layer,
                    "repository_path": contract["repository_path"],
                    "declared_stage_status": None
                    if stage is None
                    else stage.get(f"{layer}_status"),
                    "contract_examples": files,
                    "note": "Example presence is not full layer reconciliation or semantic approval.",
                }
            )
        source_capabilities = [c for c in capabilities if c["source_key"] == key]
        for capability in source_capabilities:
            for path in capability["evidence_paths"]:
                if not any(char in path for char in "<*>?"):
                    reader.read_bytes(path)
                    observed_present = reader.files[path]["presence"] == "present"
                    declared_present = path in capability.get(
                        "present_evidence_paths", []
                    )
                    declared_missing = path in capability.get(
                        "missing_evidence_paths", []
                    )
                    if (declared_present and not observed_present) or (
                        declared_missing and observed_present
                    ):
                        reader.issue(
                            "capability_evidence_presence_drift",
                            path,
                            source_key=key,
                            dimension=capability["dimension"],
                        )
        source_countries = [c for c in countries if c["source_family"] == key]
        missing_countries = sorted(
            {"SE", "DK", "NO", "FI"}
            - {
                c["country_code"]
                for c in source_countries
                if c["country_dimension"] == "source_reported"
            }
        )
        if missing_countries:
            reader.issue(
                "nordic_country_cells_missing",
                _AUTHORITIES["countries"],
                source_key=key,
                country_codes=missing_countries,
            )
        rows.append(
            {
                "source_key": key,
                "display_name": family["display_name"],
                "domain_group": family["domain_group"],
                "evidence_role": family["evidence_role"],
                "materialization_layers": materialization,
                "source_stage_record": stage,
                "semantic_capability_records": source_capabilities,
                "spatiotemporal_posture_record": postures.get(key),
                "country_availability_records": source_countries,
                "qualified_review_dimensions": sorted(
                    c["dimension"]
                    for c in source_capabilities
                    if c["human_review_required"]
                ),
                "missing_supported_dimensions": sorted(
                    c["dimension"]
                    for c in source_capabilities
                    if c["support"] != "unsupported"
                    and c["materialization"] in ("missing", "partial")
                ),
                "v2_full_confirmation": "not_established",
            }
        )
    sead_owner = ownership.get("sead_archaeology_context", {})
    neotoma = audit_neotoma(reader) if "neotoma" in families else None
    sead = (
        audit_sead(reader, sead_owner.get("governing_surface_path"))
        if "sead" in families
        else None
    )
    landclim = audit_landclim(reader) if "landclim" in families else None
    files = sorted(reader.files.values(), key=lambda row: row["path"])
    result = {
        "schema_version": "source-completion-audit.v1",
        "authority_paths": _AUTHORITIES,
        "source_count": len(families),
        "country_cell_count": len(countries),
        "capability_cell_count": len(capabilities),
        "source_rows": rows,
        "neotoma_relational_reconciliation": neotoma,
        "sead_authority_reconciliation": sead,
        "landclim_publication_inventory": landclim,
        "input_files": files,
        "manifest_byte_verifications": sorted(
            reader.verifications.values(), key=lambda row: row["path"]
        ),
        "input_closure_sha256": digest(files),
        "accounting_findings": sorted(
            reader.issues,
            key=lambda row: (row["path"], row["reason_code"], digest(row)),
        ),
        "accounting_checks_pass": not reader.issues,
        "full_source_confirmation": False,
        "scope": "The source registry and explicitly consumed manifests; no assertion of live-provider completeness, qualified approval, or unseen intake admission.",
        "status_namespace_note": "Original source-stage, country-availability and semantic-capability records retain their native fields; accounting_checks_pass is only mechanical reconciliation.",
    }
    result["audit_sha256"] = digest(result)
    return result
