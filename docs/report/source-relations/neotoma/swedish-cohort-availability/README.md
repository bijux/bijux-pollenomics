# Swedish pollen cohort availability

We checked the [Neotoma Swedish pollen dataset query](https://api.neotomadb.org/v2.0/data/datasets?gpid=5392&datasettype=pollen&limit=500) captured on 1 October 2026 against the retained relational site identities. Its 102 dataset records identify 99 distinct sites. All 99 site IDs are already in the retained 200-site snapshot. This establishes no new physical site within that query; it does not rule out another archive or a future deposit.

We also checked two PANGAEA pollen metadata leads. The [Sämbosjön SAMBOTOT pollen record](https://doi.org/10.1594/PANGAEA.739778) shares its core handle with Neotoma site 3398, collection unit 4262 and pollen dataset 4403, which has already been scored. The [Klotjärnen KLOT pollen record](https://doi.org/10.1594/PANGAEA.739382) shares its core handle with retained Neotoma site 13336, collection unit 14908 and pollen dataset 19909. Their archive coordinates differ, so we preserve both coordinates in the [machine result](report.json); the handle and linked site metadata are enough to refuse either as an independently fresh core, not to settle the coordinate discrepancy. The [SAMBOTOT dated-control record](https://doi.org/10.1594/PANGAEA.740716) lists depths and raw radiocarbon ages/errors. Its checked metadata does not supply a selected calibrated pollen-sample age model.

We then screened a bounded [PANGAEA Swedish pollen-profile metadata search](https://ws.pangaea.de/es/pangaea/panmd/_search?q=%22Pollen%20profile%22%20AND%20%22Sweden%22&size=100&_source_includes=xml-thumb,URI). Of 66 returned titles, 62 named handles match retained Neotoma collection units, three named handles do not, and one generic Schonen title has no bound core handle. We compared **all** 206 retained core handles, including records whose governed country assignment is `UNASSIGNED`. Restricting that comparison to `SE` alone would incorrectly present three existing cores as new. Source geopolitical labels still do not approve a country assignment.

| Handle | Pollen DOI | Retained Neotoma site/core/dataset | Age-determination lead | Access declaration |
| --- | --- | --- | --- | --- |
| ADRAN | [738941](https://doi.org/10.1594/PANGAEA.738941) | No exact handle match | [740137](https://doi.org/10.1594/PANGAEA.740137) | Access rights needed |
| GARASEL | [739248](https://doi.org/10.1594/PANGAEA.739248) | No exact handle match | [740365](https://doi.org/10.1594/PANGAEA.740365) | Access rights needed |
| HAKULLA5 | [711892](https://doi.org/10.1594/PANGAEA.711892) | 3138 / 3955 / 4082; `UNASSIGNED` | [740389](https://doi.org/10.1594/PANGAEA.740389) | CC BY-NC 3.0 |
| LEVEANIE | [739449](https://doi.org/10.1594/PANGAEA.739449) | No exact handle match | [740509](https://doi.org/10.1594/PANGAEA.740509) | Access rights needed |
| NDRAKET | [739584](https://doi.org/10.1594/PANGAEA.739584) | 3311 / 4162 / 4298; `UNASSIGNED` | No age-determination title in checked handle search | CC BY-NC 3.0 |
| VUOLEPAL | [889510](https://doi.org/10.1594/PANGAEA.889510) | 26118 / 32167 / 45312; `UNASSIGNED` | [888917](https://doi.org/10.1594/PANGAEA.888917) | Access rights needed |

The [Giesecke final sample-age table](https://doi.org/10.1594/PANGAEA.804596) lists 37 Swedish event handles; all 37 match retained Neotoma handles, and none is one of these six. The [Fyfe chronology-reference table](https://doi.org/10.1594/PANGAEA.853943) identifies HAKULLA5 as using “EPD chron2” and cautions that its top may be less accurate. The later [LegacyAge site table](https://doi.org/10.1594/PANGAEA.933132) independently identifies HAKULLA5 as Neotoma site 3138/dataset 4082 with its own revised `AWI` age model. Neither site metadata table is a selected pollen-sample age series for a new core. The three unmatched handles are only **leads**, not proven distinct physical sites. GARASEL's [age-determination lead](https://doi.org/10.1594/PANGAEA.740365), the [EPD data access route](https://epd.imbe.fr/getdata/), or a source-owner packet would need to establish core identity, selected sample ages and permitted use before any prediction freeze.

We checked GARASEL's linked records more closely. Its
[pollen-profile metadata](https://doi.org/10.1594/PANGAEA.739248) identify
depths from 0.12 to 5.50 m and pollen count parameters, but no sample-age
column. The [dated-control metadata](https://doi.org/10.1594/PANGAEA.740365)
identify depths from 3.025 to 7.175 m and raw radiocarbon dates and errors,
not a selected calibrated age at each pollen-sample depth. Both records
declare unknown licensing and require login for data access. A common event
name is a lead for core reconciliation, not proof of an independent physical
core. GARASEL still contributes zero admitted prediction samples.

We opened metadata only, before any new candidate pollen observation or count table. This result does not validate an independent holdout or admit LRA inputs. The next candidate needs a distinct physical core, a source-linked selected calibrated sample-age sequence, permitted use, and a frozen prediction protocol before target counts are inspected. The [research need](https://github.com/bijux/bijux-pollenomics/blob/main/reports/needed/README.md#independent-confirmation) remains open.

The [source declaration](sources.json) binds seven Neotoma/PANGAEA responses, 17 EPD/PANGAEA metadata and age-table sources, and the relational snapshot by exact digest. Reproduce the machine result from the repository root, with the private source store adjacent to the repository:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py \
  --repository . --private-root ../bijux-pollenomics-data \
  --output artifacts/jobs/swedish-cohort-availability/replay.json
cmp docs/report/source-relations/neotoma/swedish-cohort-availability/report.json \
  artifacts/jobs/swedish-cohort-availability/replay.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The metadata-only search identifies no qualified new physical core in its bounded Swedish Neotoma/PANGAEA surfaces.

**Unsupported claim.** A missing literal handle is not proof of a distinct core, and metadata discovery does not validate an untouched independent holdout.

**Actual verification performed.** Read the retained 102-record/99-site query and 66-title screen with all 206 retained handles and source declarations; no target count table or network request.

**Remaining input or review.** A truly distinct physical core, selected calibrated sample ages, permitted use and frozen pre-exposure prediction protocol remain needed.

**Cause category.** Cross-archive identity collisions and absent age/use authority.

**Consequence.** Three retained UNASSIGNED cores cannot be marketed as fresh Swedish observations.

**Precise next acceptance route.** Resolve ADRAN/GARASEL/LEVEANIE identity, selected sample ages and access terms before inspecting target counts or freezing evaluation.

**Negative or refused result.** All 99 queried sites already retained; SAMBOTOT/KLOT collide; 3 unmatched named handles remain leads, not admitted prediction samples.

**Matched denominator.** 102 queried dataset records/99 sites; 66 metadata titles: 62 retained handles, 3 unmatched named handles, 1 generic; 37 final-age events all retained.

Qualified authored reader SHA-256: `0aacdf2816cf17ce133e08186066164b2636f710cb217bffc8eb27615d079ec9`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-cohort-availability/report.json](report.json) (SHA-256 `dc915089ee968411dafb97c269693613b89dbcbfecbd3e92a580405ea50cad89`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/swedish-cohort-availability/sources.json](sources.json) (SHA-256 `c7e2c67488faec670c585fdb3d03c067cb58449bf0e4a49032698c5a1c9aad81`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
