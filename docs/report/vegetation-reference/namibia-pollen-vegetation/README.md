# Namibian modern pollen and vegetation source join

We paired the published soil-pollen counts with the published vegetation-area
rows for the same ten Namibian sites. The producer verifies the original TSV
bytes and matches event identifiers and displayed coordinates. The
[paired rows](paired.csv) preserve all 15 publisher radius labels, 100–1,500 m,
and five taxon values per site and radius: 750 taxon pairs. The 100 m subset has
50 taxon pairs. The same pollen count is repeated across a site's radius rows;
these are ten pollen samples, not 150 independent pollen samples. [The
report](report.json) records source identities and counts.

The original tables are [modern pollen, PANGAEA.931033](https://doi.org/10.1594/PANGAEA.931033)
and [vegetation, PANGAEA.931035](https://doi.org/10.1594/PANGAEA.931035),
published by Tabares, Ratzmann, Kruse, Theuerkauf, Mapani and Herzschuh (2021)
in [PANGAEA.931037](https://doi.org/10.1594/PANGAEA.931037). Both original TSV
headers declare CC BY 4.0. The source rows use pollen counts and calculated
vegetation area in square metres. The two fraction columns divide by the five
listed taxa only; they do not estimate total terrestrial pollen or total land
cover. The [parent PANGAEA description](https://doi.pangaea.de/10.1594/PANGAEA.931037)
says mean cover was calculated by 100 m rings. We retain the publisher's
ring-radius labels without assuming that the 100 m subset is the right
pollen-source radius. The tables do not state exact
soil-sampling or satellite-image dates.

This is a source-row join for an out-of-domain modern development cohort. We
have not fitted a model, scored predictions, or validated Nordic vegetation
reconstruction with these rows.

## Descriptive radius sensitivity

The [radius sensitivity report](radius-sensitivity.json) and [site-level
distances](radius-sensitivity.csv) compare the two five-taxon compositions at
each publisher `Ring sect radius [m]` label. At each site and label, the
distance is the Hellinger distance
`sqrt(sum((sqrt(p_i) - sqrt(v_i))²)/2)`, where `p_i` is the taxon's share of
the five pollen counts and `v_i` is its share of the five calculated vegetation
areas. Zero means identical conditional compositions; one is the maximum
distance. This is a descriptive composition mismatch, not a model prediction
score.

There are ten independent sites at each of the 15 labels; the same site pollen
sample repeats across labels. Mean distance across those ten sites is **0.3664**
at the 100 m label, **0.3427** at 400 m and **0.3777** at 1,500 m. The full
report gives all 15 mean, median and site-range values, and the CSV preserves
each of the 150 site-label distances. The publisher describes 100 m rings;
the exact paired areas contain nine decreases among 700 adjacent radius
comparisons across 50 site–taxon series, affecting eight series. Such decreases
cannot be cumulative nonnegative areas on the same fixed map. The JSON also
reports the ratio of each site's five listed areas to a hypothetical full
circular 100 m annulus for all 150 site–radius rows, treating each publisher
radius label as the outer radius. These ratios are geometry diagnostics, not
measured whole-cover fractions: exact ring-sector masks and taxon overlap are
not established here. None of this chooses an ecological pollen-source radius.
Pollen productivity and dispersal differ by taxon; exact pollen-sampling and
image dates are absent from these tables. The cohort remains outside the
Nordic lake target and is already exposed in development.

To reproduce from the two original PANGAEA TSV files, place
`PANGAEA.931033.tab` and `PANGAEA.931035.tab` in one source directory, then run
from the repository root:

```bash
python3 docs/report/vegetation-reference/namibia-pollen-vegetation/replay.py \
  --source-dir "$SOURCE_DIR" \
  --output-dir artifacts/jobs/namibia-pollen-vegetation-replay
cmp artifacts/jobs/namibia-pollen-vegetation-replay/paired.csv \
  docs/report/vegetation-reference/namibia-pollen-vegetation/paired.csv
cmp artifacts/jobs/namibia-pollen-vegetation-replay/report.json \
  docs/report/vegetation-reference/namibia-pollen-vegetation/report.json
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/vegetation-reference/namibia-pollen-vegetation/replay.py) refuses any source bytes differing from the pinned
SHA-256 hashes. Its output is deterministic and contains no local file paths.

The [radius sensitivity producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/vegetation-reference/namibia-pollen-vegetation/radius_sensitivity.py) consumes those same
pinned original tables through the source-row join. Reproduce its two governed
outputs from the repository root into an absent directory under `artifacts/`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 \
  docs/report/vegetation-reference/namibia-pollen-vegetation/radius_sensitivity.py \
  --source-dir ../bijux-pollenomics-data/vegetation/namibia-modern-pollen-vegetation \
  --output-dir artifacts/jobs/namibia-radius-sensitivity-replay
cmp artifacts/jobs/namibia-radius-sensitivity-replay/radius-sensitivity.csv \
  docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.csv
cmp artifacts/jobs/namibia-radius-sensitivity-replay/radius-sensitivity.json \
  docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named measured/mapped/published reference scope and unmatched temporal/taxon/observation/independence limits.

**Supported claim.** The retained source-row join aligns ten modern pollen samples with deposited five-taxon mapped areas and describes conditional compositional mismatch at every native radius label.

**Unsupported claim.** Joining source rows or computing Hellinger distances is not fitting a model, choosing an ecological pollen radius, measuring whole cover or validating Nordic reconstruction.

**Actual verification performed.** Read the exact source join, unit/ring/date caveats and retained radius-sensitivity account; bound both reports. No original TSV, join, distance or geometry calculation was rerun.

**Remaining input or review.** Exact soil/image dates, ring-sector masks, taxon overlap and broader pollen/cover denominators remain unresolved; independent target admission and reviewed physical interpretation are still needed.

**Cause category.** Out-of-domain modern source join with descriptive radius and geometry diagnostics.

**Consequence.** Ten repeated pollen samples remain ten samples across all radii; selected five-quantity closure cannot establish total pollen or landscape fractions.

**Precise next acceptance route.** Recover exact target masks, times and quantities, retain native ring labels and source hashes, and freeze a separate scientifically justified comparison before any accuracy or source-radius claim.

**Negative or refused result.** Nine decreases among 700 adjacent radius comparisons affect eight series and rule out treating them as cumulative nonnegative areas on one fixed map; hypothetical annulus ratios remain diagnostics.

**Matched denominator.** Ten sites×15 radius labels×five taxa=750 paired taxon rows; 100 m subset 50 pairs. There are 150 site/radius distances from ten pollen samples; mean Hellinger 0.3664 at 100 m, 0.3427 at 400 m, 0.3777 at 1500 m, not model scores.

- [Retained qualification evidence: docs/report/vegetation-reference/namibia-pollen-vegetation/report.json](report.json) (SHA-256 `7060e68eaa3a7f67f528dcc565a7cca6dc1963c5f5ccfc6e13fdfe356d926b67`).

- [Retained qualification evidence: docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json](radius-sensitivity.json) (SHA-256 `5a3caae7c491a020e1a1abc77e526a26ac95f1a2c7bc1084561fd6998ffeec0c`).

- [Canonical scientific account: reports/science/namibia-pollen-vegetation-paper.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/namibia-pollen-vegetation-paper.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
