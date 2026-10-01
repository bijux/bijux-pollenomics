# Swedish pollen cohort availability

We checked the [Neotoma Swedish pollen dataset query](https://api.neotomadb.org/v2.0/data/datasets?gpid=5392&datasettype=pollen&limit=500) captured on 1 October 2026 against the retained relational site identities. Its 102 dataset records identify 99 distinct sites. All 99 site IDs are already in the retained 200-site snapshot. This establishes no new physical site within that query; it does not rule out another archive or a future deposit.

We also checked two PANGAEA pollen metadata leads. The [Sämbosjön SAMBOTOT pollen record](https://doi.org/10.1594/PANGAEA.739778) shares its core handle with Neotoma site 3398, collection unit 4262 and pollen dataset 4403, which has already been scored. The [Klotjärnen KLOT pollen record](https://doi.org/10.1594/PANGAEA.739382) shares its core handle with retained Neotoma site 13336, collection unit 14908 and pollen dataset 19909. Their archive coordinates differ, so we preserve both coordinates in the [machine result](report.json); the handle and linked site metadata are enough to refuse either as an independently fresh core, not to settle the coordinate discrepancy. The [SAMBOTOT dated-control record](https://doi.org/10.1594/PANGAEA.740716) lists depths and raw radiocarbon ages/errors. Its checked metadata does not supply a selected calibrated pollen-sample age model.

We then screened a bounded [PANGAEA Swedish pollen-profile metadata search](https://ws.pangaea.de/es/pangaea/panmd/_search?q=%22Pollen%20profile%22%20AND%20%22Sweden%22&size=100&_source_includes=xml-thumb,URI). Of 66 returned titles, 59 named handles match retained Swedish Neotoma collection units, six named handles do not, and one generic Schonen title has no bound core handle. The six unmatched handles are **leads**, not proven distinct physical sites:

| Handle | Pollen DOI | Dated-control metadata DOI | Pollen-record access declaration |
| --- | --- | --- | --- |
| ADRAN | [738941](https://doi.org/10.1594/PANGAEA.738941) | [740137](https://doi.org/10.1594/PANGAEA.740137) | Access rights needed |
| GARASEL | [739248](https://doi.org/10.1594/PANGAEA.739248) | [740365](https://doi.org/10.1594/PANGAEA.740365) | Access rights needed |
| HAKULLA5 | [711892](https://doi.org/10.1594/PANGAEA.711892) | [740389](https://doi.org/10.1594/PANGAEA.740389) | CC BY-NC 3.0 |
| LEVEANIE | [739449](https://doi.org/10.1594/PANGAEA.739449) | [740509](https://doi.org/10.1594/PANGAEA.740509) | Access rights needed |
| NDRAKET | [739584](https://doi.org/10.1594/PANGAEA.739584) | No dated-control title in the checked handle search | CC BY-NC 3.0 |
| VUOLEPAL | [889510](https://doi.org/10.1594/PANGAEA.889510) | [888917](https://doi.org/10.1594/PANGAEA.888917) | Access rights needed |

The [Giesecke final sample-age table](https://doi.org/10.1594/PANGAEA.804596) lists 37 Swedish event handles; all 37 match retained Neotoma handles, and none is one of these six. The [Fyfe chronology-reference table](https://doi.org/10.1594/PANGAEA.853943) identifies HAKULLA5 as using “EPD chron2” and cautions that its top may be less accurate. That table supplies a chronology reference, not selected ages joined to pollen sample depths. We found no selected sample-age sequence for a named unmatched handle in these checked metadata sources. The next source is the [EPD data access route](https://epd.imbe.fr/getdata/) or a source-owner chronology packet for one lead, beginning with HAKULLA5's EPD chron2 and its core identity.

We opened metadata only, before any new candidate pollen observation or count table. This result does not validate an independent holdout or admit LRA inputs. The next candidate needs a distinct physical core, a source-linked selected calibrated sample-age sequence, permitted use, and a frozen prediction protocol before target counts are inspected. The [research need](https://github.com/bijux/bijux-pollenomics/blob/main/reports/needed/README.md#independent-confirmation) remains open.

The [source declaration](sources.json) binds seven Neotoma/PANGAEA responses, 16 EPD/PANGAEA metadata and age-table sources, and the relational snapshot by exact digest. Reproduce the machine result from the repository root, with the private source store adjacent to the repository:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py \
  --repository . --private-root ../bijux-pollenomics-data \
  --output artifacts/jobs/swedish-cohort-availability/replay.json
cmp docs/report/source-relations/neotoma/swedish-cohort-availability/report.json \
  artifacts/jobs/swedish-cohort-availability/replay.json
```
