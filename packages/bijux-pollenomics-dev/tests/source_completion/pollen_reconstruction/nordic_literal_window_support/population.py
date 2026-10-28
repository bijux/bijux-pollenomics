"""Complete per-core owner and window accounting without complete-case selection."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.native_rows import (
    TAXA,
    WINDOWS,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.population import (
    group_mass,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    same,
)

from .native_owners import native_owner, require, sample_account


def expected_core(
    source: dict[str, Any], core: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    require(
        protocol["schema_version"] == "nordic-literal-window-support-protocol.v1",
        "prospective protocol schema",
    )
    same(
        protocol["taxa"],
        [{"label": label, "taxon_id": identifier} for label, identifier in TAXA],
    )
    same(protocol["windows"], [list(pair) for pair in WINDOWS])
    require(
        core in protocol["cores"] and type(core["key"]) is str and bool(core["key"]),
        "declared core only",
    )
    chronology, metadata, owners = native_owner(source, core)
    samples = [
        sample_account(row, index, core, protocol["windows"])
        for index, row in enumerate(owners)
    ]
    unassigned = [
        r["sample_id"]
        for r in samples
        if r["age_disposition"] == "unassignable_selected_age"
    ]
    windows = [
        {
            "window": pair,
            **group_mass([r for r in samples if r["window"] == pair], unassigned),
        }
        for pair in protocol["windows"]
    ]
    totals = group_mass(samples, [])
    totals["known_valid_pollen_cell_sum"] = sum(
        r["known_valid_pollen_cell_sum"] for r in samples
    )
    datum_states: Counter[str] = Counter()
    for row in samples:
        datum_states.update(
            {
                state: count
                for state, count in row["datum_status_counts"].items()
                if count
            }
        )
    return {
        "schema_version": "nordic-literal-core-support.v1",
        "key": core["key"],
        "status": "literal_source_support_accounted",
        "source": core["source"],
        "identity": core["identity"],
        "chronology": chronology,
        "native_source_metadata": metadata,
        "samples": samples,
        "windows": windows,
        "population": {
            "samples": len(samples),
            "age_disposition_counts": dict(
                Counter(r["age_disposition"] for r in samples)
            ),
            "selected_age_status_counts": dict(
                Counter(r["selected_age_status"] for r in samples)
            ),
            "panel_complete_samples": sum(r["panel_complete"] for r in samples),
            "full_mass_complete_samples": sum(
                r["pollen_N"] is not None for r in samples
            ),
        },
        "source_totals": totals,
        "support_summary": {
            "supported_windows": sum(r["status"] == "supported" for r in windows),
            "window_status_counts": dict(Counter(r["status"] for r in windows)),
            "literal_taxon_state_counts": dict(
                Counter(t["status"] for r in samples for t in r["taxa"])
            ),
            "datum_status_counts": dict(datum_states),
        },
        "engine_calls": 0,
        "model_fits": 0,
        "source_acquisition": False,
        "scientific_or_field_admission": False,
        **{
            k: protocol[k]
            for k in ("scope", "suppression_semantics", "rights_and_attribution")
        },
    }
