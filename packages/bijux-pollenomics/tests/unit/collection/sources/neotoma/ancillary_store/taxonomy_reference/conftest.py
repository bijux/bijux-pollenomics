"""Share the generated three-projection input without actual retained payloads."""

from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.chain.native_products import (
    chain_products,
)
from tests.unit.collection.sources.neotoma.acquisition.linked_resources.ancestry.native_products import (
    ancestry_products,
)
from tests.unit.collection.sources.neotoma.ancillary_store.linked_evidence.native_products import (
    scoped_inputs,
)

from .test_archive import retained

__all__ = ["ancestry_products", "chain_products", "retained", "scoped_inputs"]
