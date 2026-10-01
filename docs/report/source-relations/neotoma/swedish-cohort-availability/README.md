# Swedish pollen cohort availability

We checked the [Neotoma Swedish pollen dataset query](https://api.neotomadb.org/v2.0/data/datasets?gpid=5392&datasettype=pollen&limit=500) captured on 1 October 2026 against the retained relational site identities. Its 102 dataset records identify 99 distinct sites. All 99 site IDs are already in the retained 200-site snapshot. This establishes no new physical site within that query; it does not rule out another archive or a future deposit.

We also checked two PANGAEA pollen metadata leads. The [Sämbosjön SAMBOTOT pollen record](https://doi.org/10.1594/PANGAEA.739778) shares its core handle with Neotoma site 3398, collection unit 4262 and pollen dataset 4403, which has already been scored. The [Klotjärnen KLOT pollen record](https://doi.org/10.1594/PANGAEA.739382) shares its core handle with retained Neotoma site 13336, collection unit 14908 and pollen dataset 19909. Their archive coordinates differ, so we preserve both coordinates in the [machine result](report.json); the handle and linked site metadata are enough to refuse either as an independently fresh core, not to settle the coordinate discrepancy. The [SAMBOTOT dated-control record](https://doi.org/10.1594/PANGAEA.740716) lists depths and raw radiocarbon ages/errors. Its checked metadata does not supply a selected calibrated pollen-sample age model.

We opened metadata only, before any new candidate pollen observation or count table. This result does not validate an independent holdout or admit LRA inputs. The next candidate needs a distinct physical core, a source-linked selected calibrated sample-age sequence, permitted use, and a frozen prediction protocol before target counts are inspected. The [research need](https://github.com/bijux/bijux-pollenomics/blob/main/reports/needed/README.md#independent-confirmation) remains open.

The [source declaration](sources.json) binds seven retained private metadata responses and the relational snapshot by exact digest. Reproduce the machine result from the repository root, with the private source store adjacent to the repository:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py \
  --repository . --private-root ../bijux-pollenomics-data \
  --output artifacts/jobs/swedish-cohort-availability/replay.json
cmp docs/report/source-relations/neotoma/swedish-cohort-availability/report.json \
  artifacts/jobs/swedish-cohort-availability/replay.json
```
