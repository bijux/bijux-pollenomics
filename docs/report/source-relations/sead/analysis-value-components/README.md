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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
