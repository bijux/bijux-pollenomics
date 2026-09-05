from __future__ import annotations

import random

from hypothesis import given
from hypothesis import strategies as st

from .support import _context, _derive, _mapping, _membership, _observation


def test_empty_result_digest_is_bound_to_full_derivation_context() -> None:
    baseline = _derive(memberships=[], mappings=[], observations=[])
    variants = (
        _context(source_family="sead"),
        _context(mapping_version="neotoma-crosswalk.v2"),
        _context(threshold_profile_id="reported-positive.v2"),
        _context(config_digest=f"sha256:{'d' * 64}"),
        _context(producer_version="classification-events.v2"),
    )

    variant_digests = {
        _derive(
            memberships=[], mappings=[], observations=[], context=context
        ).result_digest
        for context in variants
    }

    assert baseline.context == _context()
    assert baseline.classification_authority_manifest_sha256
    assert baseline.result_digest not in variant_digests
    assert len(variant_digests) == len(variants)


@given(st.integers(min_value=0, max_value=2**32 - 1))
def test_input_order_does_not_change_events_reconciliation_or_digest(seed: int) -> None:
    memberships = [
        _membership("observation:1", "concept:1"),
        _membership("observation:2", "concept:2"),
    ]
    mappings = [
        _mapping("concept:1", "taxon:triticum"),
        _mapping(
            "concept:2",
            "taxon:hordeum",
            source_variable_id="neotoma:variable:hordeum",
            source_taxon_id=2,
            source_reported_name="Hordeum",
        ),
    ]
    observations = [
        _observation("observation:1"),
        _observation(
            "observation:2",
            source_variable_id="neotoma:variable:hordeum",
            source_taxon_id=2,
            source_reported_name="Hordeum",
        ),
    ]
    expected = _derive(
        memberships=memberships,
        mappings=mappings,
        observations=observations,
    )
    random.Random(seed).shuffle(memberships)
    random.Random(seed + 1).shuffle(mappings)
    random.Random(seed + 2).shuffle(observations)

    actual = _derive(
        memberships=memberships,
        mappings=mappings,
        observations=observations,
    )

    assert actual == expected
