"""Release-evidence count reconciliation fixtures."""

from __future__ import annotations

from bijux_pollenomics.provenance import CountReconciliation


def _reconciliations() -> list[CountReconciliation]:
    counts = {
        "SE": (4, 3, 2, 1, 0, 1),
        "DK": (2, 2, 2, 0, 0, 0),
        "NO": (1, 0, 0, 1, 0, 0),
        "FI": (0, 0, 0, 0, 0, 0),
        "UNASSIGNED": (1, 0, 0, 0, 1, 0),
        "OUTSIDE": (0, 0, 0, 0, 0, 0),
    }
    rows = [
        CountReconciliation(
            identity="neotoma.samples.source",
            dimension="source",
            source="neotoma",
            entity="samples",
            country_code=None,
            candidate_count=8,
            eligible_count=5,
            accepted_count=4,
            unresolved_count=2,
            excluded_count=1,
            refused_count=1,
        )
    ]
    for country, values in counts.items():
        rows.append(
            CountReconciliation(
                identity=f"neotoma.samples.{country.lower()}",
                dimension="country",
                source="neotoma",
                entity="samples",
                country_code=country,
                candidate_count=values[0],
                eligible_count=values[1],
                accepted_count=values[2],
                unresolved_count=values[3],
                excluded_count=values[4],
                refused_count=values[5],
            )
        )
    return rows
