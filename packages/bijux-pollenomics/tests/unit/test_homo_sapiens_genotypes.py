from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna import build_homo_sapiens_genotype_contract


def test_homo_sapiens_genotype_contract_keeps_future_artifacts_human_only() -> None:
    contract = build_homo_sapiens_genotype_contract(
        data_root=Path("/tmp/data"),
        version="v66",
    )

    assert contract.schema_version == "homo-sapiens-genotype-contract.v1"
    assert contract.species_latin_name == "Homo sapiens"
    assert len(contract.required_artifacts) == 3
    assert contract.ingestion_ready is False
    assert "missing_geno_artifact" in contract.ingestion_blockers
    assert (
        "Non-human species must not mimic AADR .geno/.ind/.snp layout"
        in contract.nonhuman_boundary
    )
