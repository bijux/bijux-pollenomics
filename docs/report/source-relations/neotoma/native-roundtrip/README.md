# Neotoma native hierarchy round trip

The [retained report](report.json) compares the eight relational surfaces'
`source_payload` fields with their parent-scoped source payloads in the
validated nine-part Neotoma download archive. The comparison includes sites,
collection units, datasets, chronologies, controls, samples, ages and
observations. For repeated parent records it compares distinct source payloads;
for ages and observations it also
compares multiplicity. Control payloads retained as conflict variants count as
preserved evidence. The materialization reader separately validates surface
hashes, row counts, ownership and referential integrity before this comparison.

The pinned source snapshot has 209 downloads and 200 distinct site payloads.
The audit finds zero missing or unexpected parent-scoped payloads in all eight
surfaces, including 23,281 age claims and 370,936 observations. The source has
2,867 control rows and 2,836 distinct parent-scoped control payloads; 2,798
control rows are accepted and 70 variant rows appear in conflict records.
These counts describe preservation of source evidence. They do not approve age
selection, count denominators, taxa, rights or scientific admission.

Replay from the repository root with the configured environment:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/native-roundtrip/replay.py \
  > artifacts/jobs/neotoma-native-roundtrip/report-replay.json
```

Compare the replay file with `report.json`. The source identity and
materialization digest must match the retained report before reusing its
conclusion. The audit does not independently verify the original acquisition
query or pagination receipts, selected chronology semantics, normalized
observation convenience fields, compact-site derivation or refresh review.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
