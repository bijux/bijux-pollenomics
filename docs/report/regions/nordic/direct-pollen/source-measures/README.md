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

The account pins the published study manifest, the source pollen screen and 14 relational source parts. It authenticates the original study producer through a reachable Git byte witness, without importing or executing the archived program, and records the current accounting implementation separately. Actual executions reproduce every original scientific field and all 22 strata. It does not rerun or alter the predictor, promote a refused row, infer pollen absence or vegetation cover, reconcile unlike measures, or resolve chronology, taxonomy, rights, or ecological review outside the fixed cohort.

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

**Supported claim.** The retained account partitions each unique native target-cohort observation by literal unit/family and the existing direct-pollen admission predicate without changing predictions or measures.

**Unsupported claim.** Native unit labels do not admit all count rows, convert concentration/influx to counts, approve taxa, establish absence or supply LRA/vegetation evidence.

**Actual verification performed.** Executed the maintained native-measure account against all 16 pinned inputs. Independent JSON comparison preserves scalar kinds and every original scientific field across 174,970 observations and 22 strata; only historical producer custody and current accounting implementation provenance are added. A second actual execution observes 19 imported source files and reproduces the complete report bytes. No predictor, fit, numerical oracle or vegetation comparison was rerun.

**Remaining input or review.** The historical producer is authenticated through a reachable Git byte witness without executing the archived program. Configured reference/replay owner qualification remains separate from these scoped executions; native measure/classification, chronology uncertainty and scientific admission remain open.

**Cause category.** Native observation accounting with retained historical producer identity.

**Consequence.** Unique sample/site counts within unit strata can overlap and cannot be added as independent observations; unlike measures remain unlike.

**Precise next acceptance route.** Complete the configured reference/replay owner receipt against this exact generated report and the declared 19-file source closure. Source-specific review is still required for changed measures, chronology choices and biological use; no study refit is needed to reproduce this accounting.

**Negative or refused result.** 58,243 of 174,970 observations fail the predicate, including all 2,057 concentration and 160 influx rows; these are refusals rather than inferred missing pollen.

**Matched denominator.** 174,970 distinct observations in 22 strata: 165,699 NISP/count, 2,057 concentration, 160 influx and 7,054 other; 116,727 pass. Candidate samples remain DK 91, FI 1,797 and NO 3,544.

- [Retained qualification evidence: docs/report/regions/nordic/direct-pollen/source-measures/report.json](report.json) (SHA-256 `1e21777344c5adb5cdd03c7d358a9d58a833b716f158f1c79207a81d0b8b6244`).

- [Retained qualification evidence: docs/report/regions/nordic/direct-pollen/source-correspondence.json](../source-correspondence.json) (SHA-256 `6918782578b1ab62808464ca43fae6796bd276d366c23e24e439aed3c8a0bd14`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
