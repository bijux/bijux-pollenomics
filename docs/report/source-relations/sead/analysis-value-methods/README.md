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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The 28-group projection preserves class/type/method/unit metadata for 27,541 parents without typed child rows.

**Unsupported claim.** A source-declared method is not proof a laboratory procedure occurred; tree species and age text are not accepted pollen or dated events.

**Actual verification performed.** Read the method report and grouped rows against component census totals, including Years-link and source-null distinctions; no source projection rerun.

**Remaining input or review.** Qualified entity/taxonomy, measurement and age parsers with source units/chronology/use authority remain.

**Cause category.** Declared metadata and absent typed values have different evidential roles.

**Consequence.** Age in years without unit_id stays unlinked and source-null text stays null.

**Precise next acceptance route.** Qualify each source class/type/entity/parser and chronology relation before deriving measures or ecological events.

**Negative or refused result.** 0 Palynology-method links in this population; 4,797 tree-age parents lack unit relation; all event eligibility refused.

**Matched denominator.** 27,541 untyped Swedish parents/28 groups: 27,451 Dendrochronology, 90 Ancient DNA; 12,508 unit-linked/15,033 unlinked; 44 null displays.

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-value-methods/report.json](report.json) (SHA-256 `2ac12565c062668a35ba9a26e7da0bd300fda73e5af1fffaf7476d8bdf749f05`).

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-value-methods/rows.csv](rows.csv) (SHA-256 `0ed363bae34ec4feef96cd79fbce88e95ddb2ca4a4468d7dfed9f1daec34afa3`).

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-value-components/report.json](../analysis-value-components/report.json) (SHA-256 `b7c62ea8f3552f0e50e5d55aa0091a8485eafb5ad0c012641e8f1b53f92b784f`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
