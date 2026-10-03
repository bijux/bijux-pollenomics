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
