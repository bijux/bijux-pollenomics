# Neotoma source relationship validation

The [Nordic lake-parameter review](lakeparameters/README.md) retains the exact
five public source matches, the 54-site candidate denominator and a replay
against the externally retained page capture. It admits zero historical basins
or LRA samples.

The [Swedish LandClim site comparison](landclim-site-identity/README.md)
replays all 77 current Swedish prerequisite sites against 84 published
LandClim sequences. It retains 34 same-name point leads, including 16 within
10 m, while refusing source identity and radius transfer for every row. The
older 37-site comparison is contained row for row in this wider cohort.

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
