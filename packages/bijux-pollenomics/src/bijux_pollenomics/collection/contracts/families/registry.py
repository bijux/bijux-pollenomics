from __future__ import annotations

from dataclasses import asdict

from ..capabilities import build_source_capability_contract_payload
from .archaeology_contracts import build_archaeology_source_family_contracts
from .boundary_contracts import build_boundary_source_family_contracts
from .dna_contracts import build_dna_source_family_contracts
from .hydrography_contracts import build_hydrography_source_family_contracts
from .models import SourceFamilyContract
from .pollen_contracts import build_pollen_source_family_contracts


def build_source_family_contracts() -> tuple[SourceFamilyContract, ...]:
    """Build the durable layer contracts for every tracked source family."""
    return (
        *build_pollen_source_family_contracts(),
        *build_archaeology_source_family_contracts(),
        *build_boundary_source_family_contracts(),
        *build_hydrography_source_family_contracts(),
        *build_dna_source_family_contracts(),
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
