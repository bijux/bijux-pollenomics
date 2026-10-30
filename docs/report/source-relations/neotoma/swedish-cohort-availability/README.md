# Swedish pollen cohort availability

We checked the [Neotoma Swedish pollen dataset query](https://api.neotomadb.org/v2.0/data/datasets?gpid=5392&datasettype=pollen&limit=500) captured on 1 October 2026 against the retained relational site identities. Its 102 dataset records identify 99 distinct sites. All 99 site IDs are already in the retained 200-site snapshot. This establishes no new physical site within that query; it does not rule out another archive or a future deposit.

We also checked two PANGAEA pollen metadata leads. The [Sämbosjön SAMBOTOT pollen record](https://doi.org/10.1594/PANGAEA.739778) shares its core handle with Neotoma site 3398, collection unit 4262 and pollen dataset 4403, which has already been scored. The [Klotjärnen KLOT pollen record](https://doi.org/10.1594/PANGAEA.739382) shares its core handle with retained Neotoma site 13336, collection unit 14908 and pollen dataset 19909. Their archive coordinates differ, so we preserve both coordinates in the [machine result](report.json); the handle and linked site metadata are enough to refuse either as an independently fresh core, not to settle the coordinate discrepancy. The [SAMBOTOT dated-control record](https://doi.org/10.1594/PANGAEA.740716) lists depths and raw radiocarbon ages/errors. Its checked metadata does not supply a selected calibrated pollen-sample age model.

We then screened a bounded [PANGAEA Swedish pollen-profile metadata search](https://ws.pangaea.de/es/pangaea/panmd/_search?q=%22Pollen%20profile%22%20AND%20%22Sweden%22&size=100&_source_includes=xml-thumb,URI). Of 66 returned titles, 62 named handles match retained Neotoma collection units, three named handles do not, and one generic Schonen title has no bound core handle. We compared **all** 206 retained core handles, including records whose governed country assignment is `UNASSIGNED`. Restricting that comparison to `SE` alone would incorrectly present three existing cores as new. Source geopolitical labels still do not approve a country assignment.

| Handle | Pollen DOI | Retained Neotoma site/core/dataset | Age-determination lead | Access declaration |
| --- | --- | --- | --- | --- |
| ADRAN | [738941](https://doi.org/10.1594/PANGAEA.738941) | No exact handle match | [740137](https://doi.org/10.1594/PANGAEA.740137) | Access rights needed |
| GARASEL | [739248](https://doi.org/10.1594/PANGAEA.739248) | No exact Neotoma handle match; prior Rootsi numeric processing recorded | [740365](https://doi.org/10.1594/PANGAEA.740365) | Retained metadata: access rights needed; not eligible as untouched |
| HAKULLA5 | [711892](https://doi.org/10.1594/PANGAEA.711892) | 3138 / 3955 / 4082; `UNASSIGNED` | [740389](https://doi.org/10.1594/PANGAEA.740389) | CC BY-NC 3.0 |
| LEVEANIE | [739449](https://doi.org/10.1594/PANGAEA.739449) | No exact handle match | [740509](https://doi.org/10.1594/PANGAEA.740509) | Access rights needed |
| NDRAKET | [739584](https://doi.org/10.1594/PANGAEA.739584) | 3311 / 4162 / 4298; `UNASSIGNED` | No age-determination title in checked handle search | CC BY-NC 3.0 |
| VUOLEPAL | [889510](https://doi.org/10.1594/PANGAEA.889510) | 26118 / 32167 / 45312; `UNASSIGNED` | [888917](https://doi.org/10.1594/PANGAEA.888917) | Access rights needed |

The [Giesecke final sample-age table](https://doi.org/10.1594/PANGAEA.804596) lists 37 Swedish event handles; all 37 match retained Neotoma handles, and none is one of these six. The [Fyfe chronology-reference table](https://doi.org/10.1594/PANGAEA.853943) identifies HAKULLA5 as using “EPD chron2” and cautions that its top may be less accurate. The later [LegacyAge site table](https://doi.org/10.1594/PANGAEA.933132) independently identifies HAKULLA5 as Neotoma site 3138/dataset 4082 with its own revised `AWI` age model. Neither site metadata table is a selected pollen-sample age series for a new core. Absence from the Neotoma handle list does not establish freshness: GARASEL has a separately recorded Rootsi exposure history below. The other five candidate dispositions are unchanged by that focused check.

We checked GARASEL's linked records more closely. Its
[pollen-profile metadata](https://doi.org/10.1594/PANGAEA.739248) identify
depths from 0.12 to 5.50 m and pollen count parameters, but no sample-age
column. The [dated-control metadata](https://doi.org/10.1594/PANGAEA.740365)
identify depths from 3.025 to 7.175 m and raw radiocarbon dates and errors,
not a selected calibrated age at each pollen-sample depth. Both records
declare unknown licensing and require login for data access. A common event
name is a lead for core reconciliation, not proof of an independent physical
core. These are the retained 1 October 2026 metadata declarations, not a new
rights decision. GARASEL still contributes zero admitted prediction samples;
repairing its core, age or use metadata cannot undo prior numeric processing.

We opened metadata only, before any new candidate pollen observation or count table. This result does not validate an independent holdout or admit LRA inputs. The next candidate needs a distinct physical core, a source-linked selected calibrated sample-age sequence, permitted use, and a frozen prediction protocol before target counts are inspected. The research need remains open.

## GARASEL prior-processing refusal

The earlier availability screen and this replay read metadata only. That does
not mean the shared source corpus had never processed GARASEL measurements.
The existing [Rootsi identity crosswalk](../../../../../data/landclim/review/rootsi-candidate-inputs/rootsi-crosswalk.csv)
links `Garaselet (Byskeälven)` / `GARASEL`, metadata row 25, to
`rootsi/GARASEL.xls`: 19,968 bytes, SHA-256
`fcc6a5deffb86c658ec4dd1be705820c2fde0bb1dda2729886cd242d8df01797`.
Its recorded coordinates match the PANGAEA metadata site at 65.333333° N,
19.933333° E to their stated precision.

The [completed feature-census metadata](../../../../../reports/science/publication-correspondence/rootsi-feature-census/report.json)
records the same workbook identity and `Sheet1` with status `computed`, from
source commit `6bc07eb8e6b1599739473ff1478f45cb68fa9333`. Its value origin is
decoded cached values. The maintained census code opens the hash-bound
workbook, identifies candidate feature columns and reads their numeric cells
across the data rows to classify missing, zero and other numeric states.
This proves prior numeric feature processing; it does **not** establish model
fitting, tuning, score inspection or scientifically approved count semantics.
No workbook, cached cell payload, target diagram or new measurement was opened
to establish this exposure fact.

The current metadata gate binds the crosswalk and census through
[sources.json](sources.json), verifies their common workbook identity, and
marks GARASEL `refused_as_untouched_prior_numeric_source_processing`.
`untouched_confirmation_eligible` and
`untouched_status_restored_by_age_or_rights_repair` are both false. Missing,
changed or uncomputed evidence is refused rather than treated as proof of
non-exposure. Resolving source rights or selected ages can still help
development or historical questions; it cannot make this workbook an untouched
confirmation target. This focused refusal makes no new exposure finding for
the other five leads.

A genuine confirmation requires an unexposed physical-site/cohort identity and
grouped core, sample, chronology, publication and derived-product dependencies,
with eligible inputs and predictions frozen before outcomes. The requested
physical LRA route additionally requires qualified spatial vegetation and
forward-pollen support, with vegetation and pollen evaluated separately.
An observed-pollen transfer study alone does not supply that confirmation.
The research need
remains open for a different genuinely unexposed cohort.

The historical report capture predates the recorded GARASEL exposure. Its
immutable publication, source declaration and original failed observer remain
historical evidence. The current report consumer now validates that history
separately, then permits only the independently metadata-bound stricter GARASEL
refusal and scoped wording in the current report. All other scientific fields
and the five other lead dictionaries must agree exactly. The historical source
declaration permits only its separately checked exposure-metadata addendum;
its earlier fields and other source identities remain exact. Current inventory
bytes must identify the actual current report, rather than its old capture.

This corrects an observed consumer failure that still required GARASEL's old
unresolved disposition and historical report bytes after the current metadata
replay had already established prior processing. Seventy-nine affected consumer
and producer controls, configured Ruff and strict mypy pass. A bounded check of
the actual repository consumer on reviewed working changes exited zero in
0.45 s, peak macOS RSS 83,279,872 bytes, within 30 s / 256 MiB. Its compact
output is retained in
`artifacts/wetland-source-review/current-garasel-actual-consumer.txt`.
This was a current consumer check, not another source replay or census. The
historical whole failure, corrected observer success, unresolved owner,
zero retained selections and all eight false admission/scope flags survive.

## Actual metadata replay

The maintained replay at committed source
`ac55a2219cc211cdcb3611c41c02bded82803208` exited zero in **0.12 seconds**
(`/usr/bin/time -l`), with peak resident memory **46,612,480 bytes**. The owned
tool result was `db359d`; its completed process needed no yielded session.
The **9,356-byte** report is below the predeclared 100,000-byte bound; runtime
and memory are below 60 seconds and 256 MiB. The actual command, native stderr
and output are retained under `artifacts/garasel-exposure/metadata-runtime/`.

The integrator independently compared the generated report to its historical
version: every existing top-level data field except scoped wording and the
additive exposure facet remains equal; all EPD-screen fields except the named
lead list remain equal; the other five lead dictionaries remain equal; and
GARASEL's original fields remain equal except its decision. The workbook
identity was independently cross-checked. No additional study or target read
was needed for that comparison.

Sixteen controlled fixtures and configured Ruff/strict types passed. The tests
restrict file opening to the two exposure-metadata inputs and reject XLS/XLSX
or cached-cell reads, preserve the five other candidate dispositions, refuse
drifting or uncomputed evidence, and keep GARASEL refused under all tested
age/rights repair combinations. An initial import-order lint finding in the
existing replay was corrected before the successful checks. No actual replay
failure, new target exposure or model execution occurred.

The [source declaration](sources.json) preserves its seven Neotoma/PANGAEA
response pins, 17 EPD/PANGAEA metadata/age-table pins and relational identities,
and additionally binds the two existing exposure-metadata inputs. Reproduce the
machine result from the repository root, with the private source store adjacent
to the repository:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py \
  --repository . --private-root ../-bijux-pollenomics-data \
  --output artifacts/jobs/swedish-cohort-availability/replay.json
cmp docs/report/source-relations/neotoma/swedish-cohort-availability/report.json \
  artifacts/jobs/swedish-cohort-availability/replay.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** This metadata-only search identifies no qualified fresh physical core. GARASEL's hash-bound Rootsi workbook identity has recorded prior numeric processing and is refused as untouched.

**Unsupported claim.** Missing a Neotoma handle does not establish independence. This exposure record does not prove fitting/tuning or scientific count admission; repairing GARASEL's ages or rights does not restore untouched status.

**Actual verification performed.** Read the retained 102-record/99-site query and 66-title screen with all 206 retained handles and source declarations; no target count table or network request. Canonical Swedish source production returned0 on c292dafa60f9d992f162c92dd327207d9aefd76b; its original observer1 and whole1 remain literal. A separately registered corrected nested-source independent observer and complete tracked-byte check returned0, without producer repetition; the full typed report and publication bytes are unchanged. The authored78member capsule preserves3537 original and3581 corrected input identities, with26private metadata and3481runtime payloads omitted.102records/99sites,206all-country handles,66titles (62retained/3unmatched/1generic),37events and original cross-archive/UNASSIGNED collisions are retained metadata scope. No new acquisition, count observations, fresh physical cohort, calibrated selected sample ages, country normalization, rights/human/ecology/LRA admission or new retention-native outcome. The original Swedish cohort ownership criterion remains verbatim and unresolved: the retained metadata reconstruction and corrected byte comparison do not establish original private capture/provider custody and permission for all26source members. Original producer0/observer1/whole1 and corrected observer0/whole0 remain distinct. Results remain partial source evidence, not fresh-cohort acceptance; no numerical result, source chronology, permission, human decision or LRA admission changes.

Committed metadata replay ac55a2219cc211cdcb3611c41c02bded82803208 exited zero; 16 controlled checks and configured lint/types passed. Independent metadata comparison confirms other five leads and prior scope/counts unchanged. No target count, workbook, diagram, network or model was opened by this check. Historical source production at c292dafa returned zero, its initial observer/aggregate failed, and a separately corrected observer passed; those historical outcomes are retained without treating them as untouched-cohort evidence.

**Remaining input or review.** A different genuinely unexposed physical-site/cohort, source-qualified chronology/basin/parameters/use, dependency grouping and frozen predictions remain needed. GARASEL's unresolved source questions concern development/history, not restored untouched eligibility.

**Cause category.** Recorded prior numeric processing, cross-archive identity collisions and incomplete source qualifications.

**Consequence.** GARASEL and the three retained UNASSIGNED cores cannot be represented as untouched new Swedish targets on this evidence.

**Precise next acceptance route.** Qualify a genuinely unexposed different physical site under the original confirmation design before opening its outcomes. Keep GARASEL available only for separately qualified development/history work; age or rights repair cannot reverse its recorded processing history.

**Negative or refused result.** All 99 queried sites are already retained; SAMBOTOT/KLOT collide; GARASEL additionally has known prior Rootsi processing. No candidate is admitted to untouched confirmation.

**Matched denominator.** 102 queried dataset records/99 sites; 66 metadata titles: 62 retained handles, 3 unmatched named handles, 1 generic; 37 final-age events all retained.

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-cohort-availability/report.json](report.json) (SHA-256 `91c21717d160d5f6e217696367de484dd1cb1848a438e9e0b68031bcaf9da528`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-cohort-availability/sources.json](sources.json) (SHA-256 `c7e2c67488faec670c585fdb3d03c067cb58449bf0e4a49032698c5a1c9aad81`).

- [Retained qualification evidence: reports/science/source-lineage/swedish-cohort-metadata.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/swedish-cohort-metadata.json) (SHA-256 `b4e9e507cfd56ccc9dbda8d78c23a7d652baaf08032c85f5771feee16ec927fd`).

- [Retained qualification evidence: reports/science/source-cohorts/swedish-cohort-original-acceptance.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/swedish-cohort-original-acceptance.json) (SHA-256 `8a9e26bcc8aa17431e4cb3547c702537920b464c027d2880b25930b12cbdb3d3`).

- [Historical metadata qualification](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-lineage/swedish-cohort-metadata.json); historical owner criteria remain separate from this current exposure finding.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
