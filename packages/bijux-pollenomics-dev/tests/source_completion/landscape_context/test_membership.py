"""Keep native source support identities and per-record chronology separate."""

from bijux_pollenomics_dev.source_completion.landscape_context.membership import (
    identities,
)
from bijux_pollenomics_dev.source_completion.landscape_context.source import (
    Record,
    overlap,
)


def test_repeated_site_and_claim_are_not_independent_context_counts() -> None:
    rows = [
        Record(
            "a",
            "site",
            (55, 13),
            82,
            83,
            "numeric",
            ("claim1",),
            (),
            "a" * 64,
            "linked_record_interval",
            "numeric",
        ),
        Record(
            "b",
            "site",
            (55, 13),
            105,
            107,
            "numeric",
            ("claim1", "claim2"),
            ("From",),
            "b" * 64,
            "linked_record_interval",
            "numeric",
        ),
    ]
    result = identities(rows)
    assert (
        result["feature_count"] == 2
        and result["site_count"] == 1
        and result["distinct_claim_count"] == 2
    )
    assert result["qualified_or_uncertain_feature_count"] == 1
    assert not any(overlap(row.lower, row.upper, 84, 105) for row in rows)
    assert overlap(82, 107, 84, 105)
