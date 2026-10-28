# Neotoma source relationship validation

The [acquisition scope receipt](acquisition-scope/README.md) binds retained
inventory JSON rows and requested dataset IDs to the nine-part manifest. It
records six differences in current country selection and the absent original
HTTP pagination and response-byte authority.

The [observation attribute trace](observation-attributes/README.md) follows one
pinned raw datum through its normalized convenience fields and native parent
IDs. It records source nulls and the absent denominator explicitly.
The [native variable surface reconciliation](variable-surface/README.md)
checks all 1,262 relational variable identities, names, source taxon groups,
other source semantics and units against 370,936 native datum rows.
The [compact sample summary derivation](compact-summary/README.md) checks a
displayed site count against pinned relational samples and retains a reverse
trace to one observation.

The [Nordic lake-parameter review](lakeparameters/README.md) retains the exact
five public source matches, the 54-site candidate denominator and a replay
against the externally retained page capture. It admits zero historical basins
or LRA samples.

The [Swedish LandClim site comparison](landclim-site-identity/README.md)
replays all 77 current Swedish prerequisite sites against 84 published
LandClim sequences. It retains 34 same-name point leads, including 16 within
10 m, while refusing source identity and radius transfer for every row. The
older 37-site comparison is contained row for row in this wider cohort.

The [Swedish pollen cohort availability result](swedish-cohort-availability/README.md)
checks a current Neotoma metadata query and a bounded PANGAEA/EPD profile
screen before target counts are opened. Its 99 queried Neotoma site IDs are all
retained. Two PANGAEA leads collide with existing core handles; three more
apparent leads are retained `UNASSIGNED` cores, while three named handles need
core, age and rights review. It does not close independent confirmation.

The [Abborrtjärnen core comparison](abbo-core-identity/README.md) retains a
same-name, 107-sample and 0.334 m point lead but refuses to transfer the
published radius or age labels to the Neotoma core.

The [Bussjösjön and Bökesjön core comparison](swedish-lake-core-identity/README.md)
retains their full native count and age-claim coverage alongside published
site metadata. Close source points and similar series-end numbers still do
not establish historical basin radii or core identity.

The [retained result](summary.json) verifies the unchanged relational snapshot
through the production materialization reader. It includes 200 sites, 206
collection units, 209 datasets, 384 chronologies, 2,798 chronology controls,
12,388 samples, 23,281 age claims, 1,262 variables and 370,936 observations.
The source retains 33 conflict records and 52 orphan records. The 33 include
32 chronology-control payload conflicts and one actual same-age-type default
chronology conflict. The earlier materialization reported 144 conflicts because
it treated multiple default chronologies of different age types as contradictory.
[Neotoma's chronology manual](https://open.neotomadb.org/manual/chronology-age-related-tables-1.html)
permits one default per age type; the corrected producer preserves those valid
radiocarbon/calibrated pairs. The raw source and all other relational row counts
are unchanged.

The reader checks parent existence and consistent site, collection unit, dataset
and country ownership across the source graph, alongside manifested file hashes,
row counts, stable ordering, country partitions and exact file membership. Its
compact parent index does not retain the observation population. The atomic
materializer uses the same reader before publishing its staging directory.

The current refresh review at `data/neotoma/review/relational_refresh_review.md`
compares the present pinned candidate with its governed baseline. It is a
zero-difference fixed point at the same baseline identity; a changed candidate
requires a new source-specific drift explanation and review before replacement.

Unresolved chronology references remain explicit nulls; missing reference fields
are refused. Source zeros remain unchanged, while corrected default conflict
accounting is fully manifested.
This validates relational transport, not chronological comparability, taxon
review, propagation eligibility or measured vegetation accuracy.

## Reproduce

Run from the repository root using the configured environment:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/verify_ownership.py \
  --source-root "$PWD/data/neotoma/relational"
```

The consumer validates source bytes directly rather than using this summary as
input. Compare the emitted source/build/manifest/materialization identities with
the retained result before reusing it. A changed source requires a new result.

Focused regressions cover missing parents, contradictory ancestry and countries,
explicit null chronology, omitted chronology semantics, rejection before atomic
publication, and rejection of a dangling sample link even after the modified
part and complete materialization hashes are recomputed correctly. An existing
country-partition regression alters a site without dependent rows so that it
still reaches and tests country reconciliation independently of ownership.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The Neotoma ownership summary records preserved relational counts and parent/country consistency for one pinned snapshot.

**Unsupported claim.** Relational integrity does not establish original HTTP pagination, comparable selected ages, taxon acceptance or measured vegetation accuracy.

**Actual verification performed.** Read the ownership summary and native round-trip account, including corrected same-age-type default-conflict policy; no materialization rerun.

**Remaining input or review.** Original acquisition authority and source-specific chronology, taxon, count and rights decisions remain.

**Cause category.** Transport validity and scientific eligibility are separate.

**Consequence.** 33 conflicts and 52 orphans stay explicit instead of becoming accepted source evidence.

**Precise next acceptance route.** Review exact source alternatives and acquisition records before scientific admission or a separately identified refreshed capture.

**Negative or refused result.** 32 control-payload conflicts and 1 same-age-type default conflict remain; source null chronology references stay null.

**Matched denominator.** 200 sites, 206 units, 209 datasets, 384 chronologies, 2,798 controls, 12,388 samples, 23,281 age claims, 1,262 variables/370,936 observations.

- [Retained qualification evidence: docs/report/source-relations/neotoma/summary.json](summary.json) (SHA-256 `e59999e4726e27491b7ed0c2a3595c3b401bc74aaae5ce56b11e0099a84282ff`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/native-roundtrip/report.json](native-roundtrip/report.json) (SHA-256 `d8ea1c10cb91dee71af6554c4e43e246ba9a972f48df9a47df7afe294717f869`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
