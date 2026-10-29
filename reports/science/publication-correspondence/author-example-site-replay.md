# Our LandClim II author-example site decision

We connected one released raw pollen sample to its prepared time window and
the independently executed author-R and current source-Python estimate for the same
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
| Calluna vulgaris | 0.9248830793 | 0.04680697708 |
| Poaceae | 0.05741765193 | 0.01548546932 |
| Cyperaceae | 0.007018200388 | 0.005342863595 |
| Corylus avellana | 0.005710269879 | 0.003363702138 |
| Ericaceae | 0.001769073577 | 0.00161034831 |

The 31 means sum to one to numerical precision. The largest absolute
R/Python difference in this window is `3.77476e-15` for a mean and
`9.90527e-16` for a standard error. Across WHH05's eight supported
windows, the maxima are `1.37668e-14` and
`1.6584e-15`. These are modeled local cover
fractions, without independent measured vegetation acceptance.

## Every released example site

We retained the [fresh execution report](../../../docs/report/publication-replay/landclim-example-reexecution/report.json)
and checked its per-site finite-value counts against the
[governed mean/SE ledger](../../../docs/report/publication-replay/landclim-author-example-correspondence/README.md).
Each supported site-window has 31 paired means and 31 paired standard errors.
The table gives the number of supported windows out of the 25 author labels
and the maximum absolute R/native residual in fractional-cover units.

| Grid | Site | Supported windows | Mean residual | SE residual |
| --- | --- | ---: | ---: | ---: |
| 512 | BROADOWN | 17 | 2.13163e-14 | 3.74353e-15 |
| 512 | CUTHILL2 | 13 | 3.9968e-14 | 4.09395e-15 |
| 512 | HANGINGS | 17 | 4.41869e-14 | 5.35683e-15 |
| 512 | HARESDOWN | 7 | 1.14131e-13 | 1.59031e-14 |
| 512 | LOBBSBOG | 7 | 1.03584e-13 | 1.28127e-14 |
| 512 | WHH05 | 8 | 1.37668e-14 | 1.6584e-15 |
| 512 | WHH11 | 4 | 1.31006e-14 | 1.04083e-15 |
| 512 | WINDMILL | 7 | 1.25455e-13 | 1.49811e-14 |
| 512 | WINNEYS | 17 | 2.69229e-14 | 3.0323e-15 |
| 562 | BECKHAM | 11 | 1.80411e-14 | 4.73753e-15 |
| 562 | COMERSLA | 16 | 3.41949e-14 | 5.71765e-15 |
| 562 | EXEBRID | 10 | 7.18314e-14 | 7.00134e-15 |
| 562 | GOURTEMIRES | 9 | 5.53169e-14 | 6.22419e-15 |
| 562 | LARKBARR | 9 | 4.89886e-14 | 6.59195e-15 |
| 562 | LONGBREACH | 15 | 9.7311e-14 | 2.35827e-14 |
| 562 | MOLECHAM | 7 | 1.83881e-13 | 5.38146e-14 |
| 562 | NTWITCHEN | 10 | 1.66089e-13 | 1.34875e-14 |

We therefore have 97 supported site-windows in grid 512 and 87 in grid 562:
184 of 425 possible site-windows, with 241 source-unavailable windows. The
184 supported windows contribute 11,408 matched site-level mean and SE
values. All pass the original declared numerical tolerances. Original R off-support
zero placeholders and Python missing values are both excluded by source
pollen support; they are not observations. The separate regional
rows bring the two-grid correspondence to 14,074 values.

We have no authenticated archived site-level pair for these example rows, so
the residuals above compare the released author R function with the current source
Python calculation only. They do not compare either one with a published
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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** WHH05 raw depth 16 is traced through 1500 BP preparation to a site estimate; all released example sites are checked.

**Unsupported claim.** That site’s exact historical archive membership or measured vegetation fraction.

**Actual verification performed.** The original author R and current source Python stages genuinely completed on commit e282e08d796528488b438edd3ea661fb94b97b5d. Their original third-observer refusal and whole-job exit1 remain unchanged. The complete saved-source observer on 2784d4eae839e4a4e43f80ec77fd26bd0172aff0 passed; the separate maintained correspondence writer on e1ca9def55e7cd3e68ac6f20270059e743373251 returned0, while its original observer and aggregate returned1. The corrected saved-ledger observer genuinely passed with terminal 71d5f761f80e074d30fb1b13c4c0d53a3d34c86f9d5fa3dfa9e045bfb1ffbf45, rejoining every one of 14,074 ordered mean/SE cells to original R/current Python and the complete source support. Published reexecution report SHA256 4deb4e836c9ef8b81d5c29809bc2df7aed4d9dadef208f1cd866466e17d8b99f; ledger SHA256 1380633da596cfa0a51ec94ef885a7e94eecc617e37d78d0ed7c4f22121f5029. All184 available and241 unavailable site-bins remain source-bound. Original R off-support zero placeholders remain excluded; Python off-support values remain missing. Original mean/SE tolerances,1000 exact shared bootstrap draws and all17 source sites remain retained. Historical9dd1 raw proof is unavailable and is not used. No new math is executed for publication and no full1128study, independent vegetation, Nordic, source-rights, human or official release acceptance is asserted.

**Remaining input or review.** WHH05 and 17 example sites have count-to-estimate traces; historical sequence membership, selected chronology/basin, full source rights and ecological parameter approval are still unbound. Resolver: LandClim source producer and qualified chronology/basin/taxon reviewer Reopen when: Versioned production row with sample ages, basin, parameter profile and rights binds the same published cell.

**Cause category.** data|assumption|access/rights

**Consequence.** Keep 0.924883 modeled Calluna cover distinct from the 297-grain count fraction.

**Precise next acceptance route.** Versioned production row with sample ages, basin, parameter profile and rights binds the same published cell. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** Four one-grain fields excluded from WHH05 prepared row; zero independent vegetation check.

**Matched denominator.** WHH05 301 raw grains/30 named fields to 297 prepared grains/31 targets; 17 example sites across two grids.

Retained evidence: [docs/report/publication-replay/landclim-example-reexecution/report.json](../../../docs/report/publication-replay/landclim-example-reexecution/report.json), [docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv](../../../docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 982e13272f80a381b616ce2674c9faa19982691d1939d537ff0f3031b7f24ac6 -->
<!-- scientific-authored-source-sha256: 96399eb2744394a8d67cc74f29754bce1c11f0d1c1350c98d81ad1d5a5caee6b -->
<!-- scientific-verification-and-limits:end -->
