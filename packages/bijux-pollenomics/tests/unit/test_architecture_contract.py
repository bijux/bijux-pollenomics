from __future__ import annotations

from bijux_pollenomics.foundation import build_repository_architecture_contract


def test_repository_architecture_contract_exposes_lifecycle_and_package_split() -> None:
    contract = build_repository_architecture_contract()

    assert [stage.stage_key for stage in contract.lifecycle_stages] == [
        "runtime_commands",
        "source_collection",
        "evidence_normalization",
        "evidence_review",
        "publication_assembly",
        "public_artifact_writing",
    ]
    assert [
        stage.stage_key for stage in contract.animal_adna_stages
    ] == [
        "animal_adna_intake",
        "animal_adna_extraction",
        "animal_adna_normalization",
        "animal_adna_validation",
        "animal_adna_publication",
    ]
    package_roles = {
        contract.distribution_name: contract.responsibility
        for contract in contract.package_split
    }
    assert package_roles["bijux-pollenomics"].startswith("canonical runtime")
    assert package_roles["bijux-pollenomics-dev"].startswith("maintainer checks")
    assert package_roles["pollenomics"].startswith("compatibility alias")


def test_repository_architecture_contract_connects_code_data_and_docs_roots() -> None:
    contract = build_repository_architecture_contract()

    surface_map = {
        surface.surface_key: surface.repository_path
        for surface in contract.cross_tree_surfaces
    }
    assert surface_map == {
        "tracked_source_state": "data/",
        "public_publication_state": "docs/report/",
        "reader_explanation_state": "docs/",
    }
    assert set(contract.allowed_broad_boundaries) == {"core", "foundation"}
