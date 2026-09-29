# Southern Sweden historical-map reference support

The [source-bound coverage table](coverage.json) reads [Cui et al. (2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4224531/) Table 1 and its Appendix S1 Table 1. The authors compared pollen-based REVEALS/LOVE estimates with independently interpreted modern and historical maps within 3 km of three bogs. The table records the exact published spatial map coverage and the one pollen sample per bog shared by the two modern map windows.

| Bog | Modern map coverage, TW1 and TW2 | TW3 reform-map coverage | TW4 Storskifte coverage | TW4 older-map coverage | Shared pollen sample, calendar year CE / count |
| --- | ---: | ---: | ---: | ---: | ---: |
| Stavsåkra | 100% | 75% | 24% | 10% | 1930 / 617 |
| Notteryd | 100% | 12% | 63% | 11% | 1993 / 841 |
| Storasjö | 100% | 77% | 59% | 0% | 1935 / 574 |

The two TW4 columns are distinct map-period categories in the appendix; their percentages are **not** added into a union. TW1 (1950–2010) and TW2 (1925–1950) each have complete mapped spatial coverage, but the article uses **the same pollen count** for both at each site. Calendar ages 1930 and 1935 fall in TW2, while 1993 falls in TW1. Thus, 100% map coverage does not establish independent pollen records for both windows or exact temporal alignment. The authors explicitly assumed undocumented historical map areas had the same vegetation composition as documented areas; TW3/TW4 are not complete observed landscapes.

The article and sole downloadable appendix publish maps and plotted comparisons, but no table of the four numerical class areas by site/window or the full distance-weighted map fractions. The underlying 10 m increment map extraction is not supplied. The source therefore supplies spatial coverage and published pollen anchors, **not an exact numerical vegetation label** for an independent accuracy score. Figure reading could support a separately bounded approximate graphical comparison, with digitization uncertainty, but cannot be substituted for original measured class areas. The article's site names also do not authenticate the exact Neotoma collection unit, count denominator, chronology, or source revision used in this repository's [Storasjö observed-pollen holdout](../../regions/nordic/swedish-neotoma-holdout/README.md). That holdout remains pollen-only.

The private source store retains the CC BY PMC article XML, its Appendix S1 PDF and PMC metadata. Their exact SHA-256 identities appear in `coverage.json`. The producer verifies these bytes, reads the article table as XML, extracts the appendix table from the PDF using Ghostscript `txtwrite`, and refuses changed source rows. Reproduce to a separate output from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/vegetation-reference/smaland-historical-maps/coverage.py \
  --source-root /path/to/private/reference-sources/smaland-historical-maps \
  --output artifacts/jobs/smaland-historical-maps/replayed-coverage.json
```
