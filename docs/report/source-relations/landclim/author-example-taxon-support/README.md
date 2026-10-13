# Author example raw and prepared taxon support

The [source-bound ledger](report.json) compares the raw input headers for all
17 sites in author grids 512 and 562 with the author's 31-target taxonomy
lookup and each site's 31-row prepared `LRAready` matrix. It records exact
SHA-256 identities for the author lookup, PPE table, target-name crosswalk,
author formatting script, grid site lists and all 34 raw/prepared site files.
The report SHA-256 is
`a00d3fa98f1eeacf512ee3afd8243be45305aed2dcc7c420e9624a5f13b2a65e`.
The private author source remains in the external source store; this report
retains only derived support facts and source identities.

All 17 prepared matrices contain 31 target rows, but the raw headers have
literal author-lookup names for only **12–24 targets per site**. Across sites,
**168 prepared target rows** have no exact raw source-name lead. Most of those
rows are all zero. At `WHH05`, however, five such prepared rows have positive
values: `Calluna vulgaris` (sum 1,364), `Fagus sylvatica` (5), `Fraxinus` (1),
`Juniperus` (2), and `Poaceae` (138). The [R parser witness](whh05-header-parity.csv)
uses the retained author's `read.csv(..., check.names = FALSE)` call and its
taxonomy lookup. R strips trailing spaces from those five `WHH05` headers;
all five parsed names match the author lookup and their raw column sums equal
the corresponding prepared row sums. The author formatting script calls
`read.csv` before matching column names. These five positive rows therefore
have source-parser support. The remaining 163 literal gaps have no such
whitespace lead in the checked raw headers. Prepared row sums across windows
are not a source count denominator or proof of the original counting scheme.

Four raw files also carry duplicate column labels: blank headers at
`HARESDOWN`, `WINDMILL` and `NTWITCHEN`, plus repeated `Centaurea` at
`LOBBSBOG` and `Hypericum` at `WINDMILL`. The ledger retains the exact labels
and multiplicities. Source-header presence is therefore only a literal lead,
and header absence cannot be converted to a measured zero. This does not
invalidate the separately verified reproduction of the historical author R
calculation on its own prepared inputs. It blocks admission of an all-measured
taxon mask for the separately reviewed covariance and joint-draw profiles.

The row-specific decision needed from the source author or a qualified
taxonomy reviewer is how duplicate or blank columns are handled and whether
each absent target in each site was actually observed as zero or was not
recorded under that site's counting scheme. A source-backed counting
denominator and sample/window relation are also required before scientific
LRA use. No answer or approval is inferred here.

Replay into `artifacts/` and compare the report byte-for-byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_taxon_support \
  --source-root /path/to/landclim/author-reference \
  --output artifacts/author-example-taxon-support/replay
cmp docs/report/source-relations/landclim/author-example-taxon-support/report.json \
  artifacts/author-example-taxon-support/replay/report.json
Rscript docs/report/source-relations/landclim/author-example-taxon-support/whh05_header_parity.R \
  /path/to/landclim/author-reference \
  artifacts/author-example-taxon-support/replay/whh05-header-parity.csv
cmp docs/report/source-relations/landclim/author-example-taxon-support/whh05-header-parity.csv \
  artifacts/author-example-taxon-support/replay/whh05-header-parity.csv
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_taxon_support.py)
checks the 17 site identities, exact 31 target and prepared axes, source-file
membership, raw header identities and positive prepared rows without exact
raw-name leads before retaining the result. The separate
[R witness script](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/source-relations/landclim/author-example-taxon-support/whh05_header_parity.R) checks the actual parsed names,
author lookup targets and source/prepared sums for the five `WHH05` rows.

## Full author formatting replay

The [site comparison](sites.csv) replays the released R formatter's harmonize,
aggregate, missing-PPE-row fill and time-window operations for the 17 listed
author sites. It consumes 871 raw sample rows. All **17 prepared files** match
the retained author files byte-for-byte; all **15,028 cells** match, including
taxon labels, window values and the zero-filled rows. The comparison CSV has
SHA-256 `13b26b7828ade00ba4037ac334207c9b865a5032f33c40ffe17dc951397321ba`.
The [replay script](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/source-relations/landclim/author-example-taxon-support/author_prepared_replay.R) transcribes the calculation with
absolute source paths and per-site scratch files under `artifacts/`; it does not
claim execution of the original Windows-path wrapper unmodified.

The separate [count preparation audit](../author-preparation-audit/README.md)
recounts all 17 raw and prepared source files: 501,713 raw counts, 299,660
prepared counts and a 202,053-count difference. It verifies the older
independent challenge's site totals from private custody while keeping its
historical exclusion-category checks distinct from the fresh count sums.

The additional exact source identities are: `run.all.taxa.100219.csv`
`055a38b01755b5c47510199b44f7adebaf7fb33c6e75927544a76e2ceeb9df72`,
`bins.csv` `62cac73bafacb8be8d8b7007e9871494024e661ab1a2f28774dcf7cb7046a71f`,
`TWlookup.csv` `888a2d5d035c8a49bd957917ca0658bb08824240ac15c1da4b717c633ddae3dd`,
and `site.metadata.csv`
`72949e9e3faf417be0b7425fc111a9638b37c4a38aab8f8d82e0c3d8739da2de`.
The formatter SHA-256 is
`f7463b6e625781dbfdc58186fad70011af9c9f7f03f724ea29abe2489040e118`;
the ledger above hashes that script and all 17 raw/prepared pairs. Replay used
R 4.6.0. The exact numerical match explains how this released source produces
its prepared example files; it does not identify the historical inputs to the
published Nordic archive, establish a source count denominator for each window,
or convert formatter-inserted zeros to observed absences.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  Rscript docs/report/source-relations/landclim/author-example-taxon-support/author_prepared_replay.R \
  /path/to/landclim/author-reference artifacts/jobs/author-prepared-replay
cmp docs/report/source-relations/landclim/author-example-taxon-support/sites.csv \
  artifacts/jobs/author-prepared-replay/sites.csv
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
