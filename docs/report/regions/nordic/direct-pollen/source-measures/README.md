# Native measures in the Nordic direct-pollen target cohort

This [source account](report.json) partitions the source observations attached to the published Denmark, Finland, and Norway [direct-pollen target cohort](../RESULTS.md). It uses the study's original candidate-sample and source-default-age rules, then retains each observation's literal `source_unit`, `unit_family`, and direct-pollen count decision. The original predictions, scored bins, study [manifest](../manifest.json), and 16-label response are unchanged.

| Source measure in this target cohort | Observation rows | Interpretation |
| --- | ---: | --- |
| `NISP` / native `count` label | 165,699 | 116,727 pass the study's direct-pollen predicate; 48,972 retain a refusal such as non-pollen source element or invalid count. The unit label alone does not admit a row. |
| Concentration | 2,057 | Literal source measure, all refused by the study's NISP predicate; no count conversion. |
| Influx | 160 | Literal source measure, all refused by the NISP predicate; no count conversion. |
| Other literal source units | 7,054 | Preserved under their original unit and family strings, all refused by the NISP predicate. |
| Percentage or proportion; presence or absence; missing source unit | 0 in each category | No such source-family category appears among these selected target observations. This is not a claim about the entire Neotoma capture or landscape absence. |

The 174,970 distinct native observation IDs form 22 country/unit/decision strata. Of these, 116,727 pass and 58,243 fail the existing study predicate. Country target denominators remain 91 Danish, 1,797 Finnish, and 3,544 Norwegian candidate samples. The report records the first failed predicate condition and unique site, sample, and source-reported-name counts within each stratum. A sample can occur in multiple strata; adding those unique counts across rows would double-count it. Source-reported names are literal labels, not approved taxon identities.

The account pins the published study manifest, the source pollen screen, 14 relational source parts, and the existing study producer bytes. It does not rerun or alter the predictor, promote a refused row, infer pollen absence or vegetation cover, reconcile unlike measures, or resolve chronology, taxonomy, rights, or ecological review outside the fixed cohort.

From the repository root, reproduce the account in an absent artifact location:

```sh
mkdir -p artifacts/jobs/nordic-direct-pollen-source-measures
python -m bijux_pollenomics_dev.source_completion.neotoma.direct_pollen_measure_strata \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/nordic-direct-pollen-source-measures/report.json"
```

The governed `report.json` beside this reader must come from the configured source-bound owner and pass exact-byte and source-closure verification before publication.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
