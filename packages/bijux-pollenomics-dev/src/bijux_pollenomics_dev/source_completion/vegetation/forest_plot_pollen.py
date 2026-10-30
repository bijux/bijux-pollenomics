"""Frozen descriptive EMPD2–NFI development protocol.

The cohort is the existing sixteen nearest <= 1 km leads and fourteen native
plot-years. Every lead is development-exposed, including the earlier Färskesjön
tree-volume examination. New basal-area access does not restore untouched
evidence. No distance, year, radius, taxon or outcome-based cohort tuning is
permitted. Shared plot-years remain repeated rows, not independent samples.

Decode exactly BaPine, BaContorta, BaSpruce, BaBirch, BaOtherDec in native
m²/ha, using the existing source-bound dictionary/schema and its declared
7 m circular, 153.94 m² plot support. No additional area rescaling is applied.
The provisional descriptive crosswalk is Pinus=BaPine+BaContorta,
Picea=BaSpruce, Betula=BaBirch. It is not qualified botanical equivalence.
Retain all five fields, their full and selected sums, and OtherDec's share.
These fractions describe selected tree basal area, not vegetation cover,
nonforest area, regional forest composition or a lake's pollen source area.

Pollen uses only canonical native variables 75/126/12 on the same named axis.
Aliases, fragments, types and cf. records are excluded without reassignment.
Require source percent/digitisation flags zero and finite nonnegative integer
counts below 2**53 before coercion. Absence is missing; explicit 0 is measured.
Keep the literal sum of all REPORTED native count values, the selected three
sum and excluded reported values. Other source variables can include sum or
nonpollen roles: this accounting total is neither guaranteed grain count nor
a complete pollen denominator, and is not used for biological coverage.
Any missing/invalid native count or basal field refuses a comparison. Zero
selected denominators remain undefined. No pseudocount or zero-fill is used.

For complete rows, show both selected subcompositions and their signed and
absolute differences, plus total variation half-L1. This measures descriptive
discordance of DIFFERENT quantities, not prediction error, calibration,
vegetation accuracy or LRA validation. No fitting, PPE, significance test,
confidence interval, success threshold or confirmatory admission is supplied.
Dates/footprints/units/taxonomy/rights and independent pairing remain separate
requirements; all original pair refusals remain. Private plot keys, coordinates
and dates are omitted. The existing opaque identities are reused unchanged.

The maintained command writes one CSV. Commit this protocol and decoder before
opening new measurement outcomes; record that real source Git revision/command
with the result. A later confirmatory study needs distinct independent groups,
qualified review and its own frozen benchmark.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
from fractions import Fraction
import os
from pathlib import Path
import tempfile

from .forest_plot_inputs import AXIS, BASAL_FIELDS, DevelopmentPair, read_inputs

FIELDS = (
    "candidate_id",
    "nfi_row_identity_sha256",
    "plot_year_reuse",
    "evidence_role",
    "comparison_status",
    "reason_codes",
    *BASAL_FIELDS,
    "basal_area_five_total_m2_ha",
    "basal_area_selected_total_m2_ha",
    "other_deciduous_fraction_of_five",
    "selected_fraction_of_five",
    "pollen_native_rows",
    "pollen_noncanonical_alias_rows",
    "pollen_reported_count_total",
    "pollen_selected_count_total",
    "pollen_excluded_count_total",
    *(f"pollen_count_{taxon}" for taxon in AXIS),
    *(f"basal_fraction_{taxon}" for taxon in AXIS),
    *(f"pollen_fraction_{taxon}" for taxon in AXIS),
    *(f"basal_minus_pollen_fraction_{taxon}" for taxon in AXIS),
    *(f"absolute_fraction_difference_{taxon}" for taxon in AXIS),
    "descriptive_total_variation",
    "vegetation_pair_admitted",
)


def _display(value: Fraction) -> str:
    return format(float(value), ".17g")


def _decimal_total(value: Fraction) -> str:
    # Finite decimal source values have only powers of two/five in denominators.
    # This precision bound preserves their sum without a binary64 conversion.
    with localcontext() as context:
        context.prec = max(
            28, len(str(abs(value.numerator))) + value.denominator.bit_length()
        )
        return format(Decimal(value.numerator) / Decimal(value.denominator), "f")


def comparison_row(pair: DevelopmentPair) -> dict[str, object]:
    """Preserve every attempted row and distinguish undefined from measured zero."""
    pollen = pair.pollen
    row: dict[str, object] = dict.fromkeys(FIELDS, "")
    row.update(
        candidate_id=pair.candidate_id,
        nfi_row_identity_sha256=pair.plot_year_id,
        plot_year_reuse=pair.plot_year_reuse,
        evidence_role="exposed_development_different_estimands",
        pollen_native_rows=pollen.row_count,
        pollen_noncanonical_alias_rows=pollen.noncanonical_alias_rows,
        pollen_reported_count_total=pollen.reported_total,
        pollen_selected_count_total=pollen.selected_total,
        pollen_excluded_count_total=pollen.excluded_total,
        vegetation_pair_admitted="false",
    )
    row.update(zip(BASAL_FIELDS, pair.basal_area, strict=True))
    row.update(
        (f"pollen_count_{taxon}", value)
        for taxon, value in zip(AXIS, pollen.counts, strict=True)
    )
    reasons = set(pair.basal_reasons) | set(pollen.reasons)
    selected: tuple[Fraction, ...]
    if all(value is not None for value in pair.basal_area):
        basal_values = [
            Fraction(Decimal(value)) for value in pair.basal_area if value is not None
        ]
        selected = basal_values[0] + basal_values[1], basal_values[2], basal_values[3]
        five_total = sum(basal_values, Fraction(0))
        selected_total = sum(selected, Fraction(0))
        row["basal_area_five_total_m2_ha"] = _decimal_total(five_total)
        row["basal_area_selected_total_m2_ha"] = _decimal_total(selected_total)
        if five_total > 0:
            row["other_deciduous_fraction_of_five"] = _display(
                basal_values[4] / five_total
            )
            row["selected_fraction_of_five"] = _display(selected_total / five_total)
        if selected_total <= 0:
            reasons.add("zero_selected_basal_area")
        else:
            row.update(
                (f"basal_fraction_{taxon}", _display(value / selected_total))
                for taxon, value in zip(AXIS, selected, strict=True)
            )
    else:
        selected, selected_total = (), Fraction(0)
        reasons.add("incomplete_basal_area")
    if pollen.selected_total == 0:
        reasons.add("zero_selected_pollen_count")
    if pollen.selected_total is None:
        reasons.add("incomplete_selected_pollen")
    elif (
        pollen.selected_total > 0
        and "pollen_count_units_or_digitisation_unresolved" not in pollen.reasons
    ):
        row.update(
            (
                f"pollen_fraction_{taxon}",
                _display(Fraction(value, pollen.selected_total)),
            )
            for taxon, value in zip(AXIS, pollen.counts, strict=True)
            if value is not None
        )
    if not reasons:
        assert pollen.selected_total is not None
        basal = tuple(value / selected_total for value in selected)
        observed = tuple(
            Fraction(value, pollen.selected_total)
            for value in pollen.counts
            if value is not None
        )
        differences = tuple(a - b for a, b in zip(basal, observed, strict=True))
        for prefix, values in (
            ("basal_fraction", basal),
            ("pollen_fraction", observed),
            ("basal_minus_pollen_fraction", differences),
            ("absolute_fraction_difference", tuple(abs(v) for v in differences)),
        ):
            row.update(
                (f"{prefix}_{taxon}", _display(value))
                for taxon, value in zip(AXIS, values, strict=True)
            )
        row["descriptive_total_variation"] = _display(
            sum((abs(value) for value in differences), Fraction(0)) / 2
        )
    row["comparison_status"] = "refused" if reasons else "descriptive_comparison"
    row["reason_codes"] = ";".join(sorted(reasons))
    return row


def build(
    repository: Path, private_source_store: Path, output: Path
) -> tuple[tuple[dict[str, object], ...], int]:
    """Publish only the fixed public columns, leaving original sources unchanged."""
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output CSV required")
    pairs, physical_plots = read_inputs(repository, private_source_store)
    rows = tuple(comparison_row(pair) for pair in pairs)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=output.parent,
            prefix=".forest-plot-pollen-",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            writer = csv.DictWriter(stream, FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, output)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)
    return rows, physical_plots


def main() -> None:
    """Execute the fixed exposed-development descriptive protocol."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, physical_plots = build(
        args.repository, args.private_source_store, args.output
    )
    print(
        f"rows={len(rows)} physical_plots={physical_plots} compared={sum(row['comparison_status'] == 'descriptive_comparison' for row in rows)} vegetation_pairs_admitted=0"
    )


if __name__ == "__main__":
    main()
