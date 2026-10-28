# Neotoma dataset decisions for the Nordic pollen study

The [dataset ledger](report.json) joins the captured Neotoma relational dataset
part, the sample-level pollen prerequisite screen, and the retained four-country
direct observed-pollen study. It binds all **209 datasets and 12,388 samples** to
the exact source manifests and study files by SHA-256. The source part is also
checked against its relational manifest. Each dataset row retains its country,
site and canonical row digest.

The selected direct-pollen study used **85 datasets**: Sweden 3, Denmark 2,
Norway 52, Finland 28. The other **124** are explicitly outside that selected
study, including seven with unassigned country. This is a study inclusion
decision, not a claim that the other datasets are unusable. The sample screen
finds **10,637** count-and-comparable-age prerequisite candidates across all
datasets; it refuses 1,751 samples. Those candidates are not all on the
study's closed 16-label axis and are not LRA inputs.

Every dataset retains unresolved LRA source requirements and has no matched
independent measured-vegetation observation in this ledger. The source screen
already refuses all 12,388 samples for LRA admission. Basin history, taxonomy,
parameter binding and qualified source decisions remain separate. This one
family ledger does not complete the all-family entity matrix or approve source
use beyond the retained direct-pollen study.

Replay from the repository root:

```sh
mkdir -p artifacts/jobs/neotoma-entity-decisions
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.neotoma_entity_decisions \
  --repository . --output artifacts/jobs/neotoma-entity-decisions/report.json
```

The destination must be absent. The producer reads each of its six declared
source files once, then rechecks their byte identities before publishing the
report atomically. Compare the replay file byte for byte with this directory's
`report.json`.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
