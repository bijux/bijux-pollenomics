# SEAD analysis-value components

The [component census](report.json) and [country/class table](rows.csv)
account for all **68,705** captured SEAD analysis-value parents in the pinned
full-evidence snapshot. Four native component tables supply 41,164 typed
parents; **27,541 remain untyped**. Their source display text is retained
without inferring a numeric measure or ecological observation.

Each group keeps the governed country, source class and type, native unit ID
when linked, and explicit unit posture. Counts are parent counts. The producer
refuses duplicate parents, overlapping components, orphans, changed source
rows, changed country or unit lineage, and changed event-refusal posture.
The JSON records the exact source readset and binds the CSV hash.

All parents in this source table belong to governed Swedish sites. The wider
SEAD site capture includes Danish, Norwegian and Finnish records; its
[site and country account](../source-unit-accounting/README.md) has a different
population. Of these analysis values, 16,938 have a native unit link and
51,767 have no unit exposed through their source type relation. A missing
unit link is preserved rather than filled with an assumed denominator.

## Reproduce the census

From the installed development environment at a clean repository checkout,
use an absent artifact destination:

```sh
mkdir -p artifacts/jobs/sead-analysis-value-components
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  -m bijux_pollenomics_dev.source_completion.sead.analysis_value_components \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/sead-analysis-value-components/source-products"
```

## Scientific boundary

This is source accounting. The snapshot admits no ecological events. Unit
links do not prove comparable pollen measures; source display text does not
prove species presence. The census does not approve chronology, cross-source
classification, source rights or release.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The component census closes 68,705 analysis-value parents into typed and untyped strata with native unit-link posture.

**Unsupported claim.** Untyped text is not an inferred measure, and this Swedish analysis table is not the four-country sample/observation population.

**Actual verification performed.** Read the full 63-group report and country/class CSV, checking component totals and unit gaps; no source census rerun.

**Remaining input or review.** Source-specific semantics, comparable measurement support, taxonomy, chronology and rights remain unqualified.

**Cause category.** Absent component or unit relations must remain missing.

**Consequence.** 27,541 untyped parents and 51,767 unlinked units cannot become observed zeros or assumed denominators.

**Precise next acceptance route.** Resolve exact class/type/unit authority and qualified biological/date use before accepting any measurement or event.

**Negative or refused result.** All events refused; 27,541 parents have no typed component; 51,767 expose no unit relation.

**Matched denominator.** 68,705 Swedish parents=41,164 typed+27,541 untyped; typed 24,701 integer+11,603 boolean+4,800 categorical+60 numerical; 16,938 linked units.

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-value-components/report.json](report.json) (SHA-256 `b7c62ea8f3552f0e50e5d55aa0091a8485eafb5ad0c012641e8f1b53f92b784f`).

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-value-components/rows.csv](rows.csv) (SHA-256 `c935541d8da42d7cdfd9308ec6343349380ef3b8e682912eed32f67ab2a92cce`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
