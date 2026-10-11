from bijux_pollenomics.collection.contracts.families.context.hydrography import (
    build_hydrography_source_family_contracts,
)
from bijux_pollenomics.collection.contracts.families.context.land_use import (
    build_hyde_source_family_contract,
)


def test_context_domains_preserve_distinct_evidence_roles() -> None:
    (lake,) = build_hydrography_source_family_contracts()
    land = build_hyde_source_family_contract()
    assert lake.source_key == "svar" and lake.evidence_role == "sampling_domain"
    assert (
        land.source_key == "hyde" and land.evidence_role == "external_model_comparison"
    )
    assert land.raw_layer.repository_path == "data/hyde/3.5/raw"
