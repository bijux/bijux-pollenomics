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
`7da46aa0ca1c17b6915f6ee99e51c4911632472a244aefdc1a62828f1d4c41d4`.

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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The retained grid 512 example at 225 BP propagates selected-count, site-resampling and shared positive PPE draws for six sites and ten prepared taxa, conditional on fixed chronology, geometry and transport.

**Unsupported claim.** It supplies no historical source-R parity, calibrated field coverage, scientific admission of all 31 author targets or independent vegetation accuracy; shared author lineage is not independent evidence.

**Actual verification performed.** Executed the maintained author-site uncertainty replay on local main1180a97d7d7356d0f7a6b05d116f342587861997 and an independent complete three-product observer; both native stages exited zero. All 13 original private input identities, six sites, ten taxa, selected counts and 1,024 joint draw rows were authenticated. Every typed scientific value matched the retained result, and draws.json plus cover-draws.csv were byte-identical. Only replay-code byte/hash metadata and the moved joint-draw module path changed.

**Remaining input or review.** Current-source replay and the stale report reference are reconciled. Scientific use still needs source parameter, age-specific geometry and chronology justification, rights and independent scientific review; this replay supplies no historical source-R parity or ecological accuracy.

**Cause category.** Current-source conditional uncertainty replay with exact retained scientific values and shared-draw identities; scientific applicability remains separately qualified.

**Consequence.** The 1,024-draw calculation now binds its actual current code provenance and reader reference. It remains conditional on the selected ten-taxon denominator and fixed chronology, geometry and transport, without a new field-accuracy or scientific-release claim.

**Precise next acceptance route.** Use the adopted source-bound report and unchanged stored draw products for the maintained paired author-site profile comparison; qualify any scientific application against its original source, chronology, geometry, rights and independent review requirements.

**Negative or refused result.** Targets without selected positive prepared support are not silently treated as measured absences. Missing historical R parity and ecological accuracy remain explicit false claims.

**Matched denominator.** One grid/window, six sites, ten selected taxa from 31 prepared targets; selected site counts 289,293,2223,2786,4251,562 sum 10,404 against full 10,747; 1,024 explicit paired replicates.

Qualified authored reader SHA-256: `cdeba0e06615b0989e9f4822f45f4fd1ff63e7a6ae13873dea36c42a525020f4`.

- [Retained qualification evidence: docs/report/method-certification/author-site-uncertainty/report.json](report.json) (SHA-256 `7da46aa0ca1c17b6915f6ee99e51c4911632472a244aefdc1a62828f1d4c41d4`).

- [Retained qualification evidence: docs/report/method-certification/author-site-uncertainty/draws.json](draws.json) (SHA-256 `84da401dc862452bc329d11df074d2c6d7353b3e34b223892b5fd6702fae4390`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
