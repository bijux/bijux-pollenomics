from __future__ import annotations

from pathlib import Path

from ...adna.governance_contracts import materialize_adna_governance_contracts
from ...core.files import write_json
from ..data_contracts import (
    build_evidence_artifact_contract_payload,
    build_source_fact_ownership_payload,
)
from ..models import DataCollectionSummary
from ..source_family_contracts import (
    build_source_family_contract_payload,
    build_source_family_state_matrix_payload,
)

__all__ = ["write_data_contract_surfaces"]


def write_data_contract_surfaces(summary: DataCollectionSummary) -> None:
    """Write durable data-contract surfaces that explain source ownership and stages."""
    output_root = summary.output_root
    contract_artifacts = summary.contract_artifacts
    write_json(
        Path(contract_artifacts["source_family_contracts"]),
        build_source_family_contract_payload(),
    )
    write_json(
        Path(contract_artifacts["source_family_evidence_stage_matrix"]),
        build_source_family_state_matrix_payload(
            output_root,
            counts={
                "aadr_file_count": summary.aadr_file_count,
                "landclim_site_count": summary.landclim_site_count,
                "landclim_grid_cell_count": summary.landclim_grid_cell_count,
                "neotoma_point_count": summary.neotoma_point_count,
                "sead_point_count": summary.sead_point_count,
                "raa_total_site_count": summary.raa_total_site_count,
                "raa_heritage_site_count": summary.raa_heritage_site_count,
            },
        ),
    )
    write_json(
        Path(contract_artifacts["source_fact_ownership_registry"]),
        build_source_fact_ownership_payload(),
    )
    write_json(
        Path(contract_artifacts["evidence_artifact_contracts"]),
        build_evidence_artifact_contract_payload(),
    )
    materialize_adna_governance_contracts(output_root)
