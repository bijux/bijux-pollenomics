# Conditional uncertainty on author example sites

The [source-bound result](report.json) uses the released LandClim II author
example's grid 512, 225 BP midpoint window. The six sites with source pollen
in that window are BROADOWN, HANGINGS, HARESDOWN, LOBBSBOG, WINDMILL and
WINNEYS. Their source radius values span 10–200; the calculation passes those
static values as metres to the source-compatible lake deposition function.
The [raw-to-prepared replay](../../source-relations/landclim/author-example-taxon-support/README.md)
has already reproduced all six selected prepared files byte-for-byte from
source raw rows. The report hashes the selected author files, 31-target PPE
and covariance tables, crosswalk, site list, lineage receipt and calculation
code. Its SHA-256 is
`415185927514de10a71b6a7ba6c26d7bc1fd3ed8cc140760ec2e3e9f58f1c243`.

The **ten taxa with positive prepared counts at every selected site** form an
exploratory closed subcomposition. Their site totals are 289, 293, 2,223,
2,786, 4,251 and 562 counts, respectively: 10,404 selected counts out of
10,747 on the author's full 31-target axis. Every selected site/taxon cell
is positive; no formatter-inserted zero is represented as an observed absence.
This selection was made after reading the example counts. Its denominator is
the sum of these ten taxa within each site/window, not the source's complete
pollen-counting denominator or total vegetation cover.

The reviewed fixed-site profile treats each site's selected count total as a
conditional multinomial draw and propagates the source PPE covariance. The
[joint draw identities](draws.json) retain 1,024 paired site bootstrap rows,
one multinomial count draw per original site and one shared positive PPE vector
per replicate. The PPE vectors use a lognormal distribution moment-matched to
the source mean/covariance; the selected source covariance has zero off-diagonal
entries. The [closed cover draws](cover-draws.csv) and both reported means and
standard errors are fractions on the ten-taxon axis. For example, Cyperaceae
has fixed-site SE 0.014250 and joint SE 0.121566; Poaceae has 0.011599 and
0.101076. The difference reflects site selection under this declared
bootstrap, not an estimate of vegetation accuracy. Six source sites are too
few for a broad population interval.

The source site's historical basin outline, radius changes, independent
vegetation truth and chronology uncertainty remain unverified. The author
example's numeric radius is a fixed method input, not an admitted
age-specific Nordic lake geometry. This result certifies a conditional
calculation on a deliberately restricted source example. It does not replace
the original 31-taxon author result, claim corrected parity with historical R
standard errors, or admit Swedish or four-country LRA predictions.

Replay into `artifacts/` and compare all governed outputs byte-for-byte:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 .venv/bin/python \
  docs/report/method-certification/author-site-uncertainty/replay.py \
  --source-root /path/to/landclim/author-reference --repository . \
  --output artifacts/jobs/author-site-uncertainty/replay
for name in report.json draws.json cover-draws.csv; do
  cmp "docs/report/method-certification/author-site-uncertainty/$name" \
    "artifacts/jobs/author-site-uncertainty/replay/$name"
done
```
