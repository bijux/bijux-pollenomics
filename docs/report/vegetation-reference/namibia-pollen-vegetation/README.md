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
cover. We retain the publisher's ring-radius labels without assuming that the
100 m subset is the right pollen-source radius. The tables do not state exact
soil-sampling or satellite-image dates.

This is a source-row join for an out-of-domain modern development cohort. We
have not fitted a model, scored predictions, or validated Nordic vegetation
reconstruction with these rows.

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

The [producer](replay.py) refuses any source bytes differing from the pinned
SHA-256 hashes. Its output is deterministic and contains no local file paths.
