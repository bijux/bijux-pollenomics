# Author example raw and prepared taxon support

The [source-bound ledger](report.json) compares the raw input headers for all
17 sites in author grids 512 and 562 with the author's 31-target taxonomy
lookup and each site's 31-row prepared `LRAready` matrix. It records exact
SHA-256 identities for the author lookup, PPE table, target-name crosswalk,
grid site lists and all 34 raw/prepared site files. The report SHA-256 is
`fa1a0ba1e0214fd9fada133f38012aa7026346a1f0a2bfacd830e398c5cecf19`.
The private author source remains in the external source store; this report
retains only derived support facts and source identities.

All 17 prepared matrices contain 31 target rows, but the raw headers have
literal author-lookup names for only **12–24 targets per site**. Across sites,
**168 prepared target rows** have no exact raw source-name lead. Most of those
rows are all zero. At `WHH05`, however, five such prepared rows have positive
values: `Calluna vulgaris` (sum 1,364), `Fagus sylvatica` (5), `Fraxinus` (1),
`Juniperus` (2), and `Poaceae` (138). These sums describe the prepared matrix
across its windows; they are not a source count denominator or an approved
raw-name mapping. `WHH05` raw labels include similar-looking names with spaces,
but spelling resemblance does not identify the preprocessing rule.

Four raw files also carry duplicate column labels: blank headers at
`HARESDOWN`, `WINDMILL` and `NTWITCHEN`, plus repeated `Centaurea` at
`LOBBSBOG` and `Hypericum` at `WINDMILL`. The ledger retains the exact labels
and multiplicities. Source-header presence is therefore only a literal lead,
and header absence cannot be converted to a measured zero. This does not
invalidate the separately verified reproduction of the historical author R
calculation on its own prepared inputs. It blocks admission of an all-measured
taxon mask for the separately reviewed covariance and joint-draw profiles.

The row-specific decision needed from the source author or a qualified
taxonomy reviewer is: which raw columns and preprocessing rules produce the
five positive `WHH05` target rows, how duplicate or blank columns are handled,
and whether each absent target in each site was actually observed as zero or
was not recorded under that site's counting scheme. A source-backed counting
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
```

The [producer](../../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_taxon_support.py)
checks the 17 site identities, exact 31 target and prepared axes, source-file
membership, raw header identities and positive prepared rows without exact
raw-name leads before retaining the result.
