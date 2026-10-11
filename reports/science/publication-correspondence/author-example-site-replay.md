# Our LandClim II author-example site decision

We connected one released raw pollen sample to its prepared time window and
the independently executed author-R and installed-LRA estimate for the same
site. We also checked every site in the two released example grids. This gives
us a reproducible calculation result on the author's example inputs. The
historical input revisions behind the published Nordic archive are still
unidentified, so we do not call this a replay of all published estimates.

## The WHH05 source-to-estimate trace

The released author revision
`57ead2e2fcc493d099be4e5a3092fc396e1c3d3a` identifies `WHH05` as
White Horse Hill 2005 section in grid 512. We checked the raw
`input/WHH05.csv` sample at depth 16 and age 1320 cal BP against the
author-prepared `LRAready_WHH05.csv` window labelled 1500 BP. The source
sample contains 301 grains across 30 named taxon fields; its `Sum` column is
a total, not another taxon. The prepared 31-taxon vector contains 297 grains
across 10 positive taxa. We accounted for the four missing grains as four
explicitly named, one-grain source fields. That is a mechanical source
reconciliation; it does not decide whether the original counting protocol
excluded those taxa ecologically. The [input-slice reader](../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/one_site.py)
binds the nine selected source files by SHA-256 and records the exact counts,
labels and exclusions.

The sample age belongs to the author's `[1250,1750)` cal BP interval. The
1500 BP number labels that interval; it is not the sample's measured age. The
author metadata and prepared file both give radius 150 m and lake model code
2. The native host's corresponding basin diameter is 300 m. The source PPE
table has 31 means and a 31-by-31 covariance axis. We have not approved those
parameters for a different core or established the sample's complete source
counting denominator.

The author REVEALS calculation for grid 512 uses nine sites, not WHH05 alone.
The independent [R/native execution](../../../docs/report/publication-replay/landclim-example-reexecution/README.md)
retains a WHH05 site estimate in eight of its 25 windows. Its ordered site
receipt places WHH05 at author-R site 6 and native site 5. In the 1500 BP
window, the [row-level correspondence](../../../docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv)
contains 31 paired means and 31 paired standard errors in fractional-cover
units. These are the five largest author-R means:

| Taxon | Author-R mean | Author-R standard error |
| --- | ---: | ---: |
| Calluna vulgaris | 0.9248830793 | 0.0468069771 |
| Poaceae | 0.0574176519 | 0.0154854693 |
| Cyperaceae | 0.0070182004 | 0.0053428636 |
| Corylus avellana | 0.0057102699 | 0.0033637021 |
| Ericaceae | 0.0017690736 | 0.0016103483 |

The 31 means sum to one to numerical precision. The largest absolute
R/native difference at this window is `4.77e-15` for a mean and `8.90e-16`
for a standard error. Across WHH05's eight supported windows, the maxima
are `1.39e-14` and `1.66e-15`. We therefore accept this example as a
bounded numerical correspondence of the declared R and native calculations.
These fractions are modeled local cover, not measured vegetation.

## Every released example site

We retained the [fresh execution report](../../../docs/report/publication-replay/landclim-example-reexecution/report.json)
and checked its per-site finite-value counts against the
[governed mean/SE ledger](../../../docs/report/publication-replay/landclim-author-example-correspondence/README.md).
Each supported site-window has 31 paired means and 31 paired standard errors.
The table gives the number of supported windows out of the 25 author labels
and the maximum absolute R/native residual in fractional-cover units.

| Grid | Site | Supported windows | Mean residual | SE residual |
| --- | --- | ---: | ---: | ---: |
| 512 | BROADOWN | 17 | 2.13e-14 | 3.74e-15 |
| 512 | CUTHILL2 | 13 | 4.00e-14 | 4.09e-15 |
| 512 | HANGINGS | 17 | 4.32e-14 | 5.36e-15 |
| 512 | HARESDOWN | 7 | 1.14e-13 | 1.59e-14 |
| 512 | LOBBSBOG | 7 | 1.04e-13 | 1.28e-14 |
| 512 | WHH05 | 8 | 1.39e-14 | 1.66e-15 |
| 512 | WHH11 | 4 | 1.31e-14 | 1.04e-15 |
| 512 | WINDMILL | 7 | 1.25e-13 | 1.50e-14 |
| 512 | WINNEYS | 17 | 2.69e-14 | 3.03e-15 |
| 562 | BECKHAM | 11 | 1.80e-14 | 4.82e-15 |
| 562 | COMERSLA | 16 | 3.42e-14 | 5.72e-15 |
| 562 | EXEBRID | 10 | 7.18e-14 | 7.00e-15 |
| 562 | GOURTEMIRES | 9 | 5.53e-14 | 6.22e-15 |
| 562 | LARKBARR | 9 | 4.90e-14 | 6.59e-15 |
| 562 | LONGBREACH | 15 | 9.73e-14 | 2.35e-14 |
| 562 | MOLECHAM | 7 | 1.84e-13 | 5.38e-14 |
| 562 | NTWITCHEN | 10 | 1.66e-13 | 1.35e-14 |

We therefore have 97 supported site-windows in grid 512 and 87 in grid 562:
184 of 425 possible site-windows, with 241 source-unavailable windows. The
184 supported windows contribute 11,408 matched site-level mean and SE
values. All pass the declared numerical tolerances. The separate regional
rows bring the two-grid correspondence to 14,074 values.

We have no authenticated archived site-level pair for these example rows, so
the residuals above compare the released author R function with the installed
native calculation only. They do not compare either one with a published
site-level estimate.

## Recheck the source-to-estimate link

Our [one-site integration test](../../../packages/bijux-pollenomics-dev/tests/essd_reproduction/test_one_site.py)
authenticates the private WHH05 source slice, joins its grid/site/window
identity to the 62 governed mean/SE rows, and checks the independent
execution receipt. Supply the intact external author-reference capsule:

```sh
mkdir -p artifacts/jobs/landclim-site-check
BIJUX_LANDCLIM_AUTHOR_REFERENCE=/path/to/author-reference \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/pytest -q \
  -o cache_dir=artifacts/jobs/landclim-site-check/cache \
  --basetemp=artifacts/jobs/landclim-site-check/tmp \
  packages/bijux-pollenomics-dev/tests/essd_reproduction/test_one_site.py
```

Without that private source variable, the ten source-dependent checks skip
explicitly. The test consumes the retained R/native result; the separate
[execution report](../../../docs/report/publication-replay/landclim-example-reexecution/README.md)
documents how to run those calculations again.

## What remains open

The released raw-to-prepared replay matched all 17 author example files and
15,028 prepared cells, but [source taxon support](../../../docs/report/source-relations/landclim/author-example-taxon-support/README.md)
still distinguishes formatter-filled zero rows from observed absences. We
have not identified the historical source revisions and chronology decisions
for the archive's 1,128 sequences, authenticated its PFT/LCT transformation,
or obtained independent measured vegetation for these site outputs. The
[publication account](../publication-correspondence.md) records the matched
TW2 archive differences and the exact questions those differences raise.
Source redistribution and scientific parameter approval also remain open.

We retain the WHH05 chain as an author-example calculation witness and the
17-site table as its declared numerical support. We keep the broader
publication reproduction and Nordic LRA admission open until their own
source evidence is available.
