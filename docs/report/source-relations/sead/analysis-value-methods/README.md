# SEAD analysis-value method and type coverage

The [method coverage report](report.json) and [class and type table](rows.csv) join the [governed analysis-value component census](../analysis-value-components/README.md) to the original SEAD value-class, value-type, method and unit definitions. Each group preserves the source class and type IDs and names. The 28 compact groups account for the 27,541 Swedish analysis-value parents with no typed component row. “No typed component” describes a missing child relation in this capture; it does not mean that a class or declared type is absent or that the source row is erroneous.

The pinned source definitions associate 27,451 of these parents with Dendrochronology and 90 with Ancient DNA analysis (Sample Extraction/Analysis). None has a value-class link to the source Palynology method. A total of 12,508 untyped parents have a source unit link to Years; 15,033 do not have a unit relation. Forty-four preserve a source-null display, while 27,497 have reported source text. Method here is metadata declared by the value class; the report does not independently establish that a laboratory procedure was performed for each parent.

The `Age in years` value-type label has no `unit_id` in the captured definition. Its 4,797 untyped tree-age lower and upper parents should therefore stay in the unlinked-unit stratum. Growth-year and felling-year strings or ranges are not accepted numeric ages without a reviewed source parser and chronology relation. The 4,777 `Tree species` labels need taxonomy and entity review before they can support an ecological observation. Ancient-DNA metadata are a separate source family; these counts are not pollen NISP, concentration or influx.

The maintained CLI consumes the two governed census outputs, three source definition tables already pinned in the census readset, and the original method table independently authenticated by the raw admission and manifest. It refuses changed bytes, missing foreign keys, changed class/type names, lost units, duplicate groups, changed denominators and postread mutation before atomic publication. It writes only compact groups under an absent artifact destination:

```sh
mkdir -p artifacts/jobs/sead-analysis-value-methods
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  -m bijux_pollenomics_dev.source_completion.sead.analysis_value_methods \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/sead-analysis-value-methods/source-products"
```

This is a source-accounting projection. It admits zero ecological events and does not settle chronology, taxonomy, measurement compatibility, source rights, or complete cross-source measure and denominator acceptance.
