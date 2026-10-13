# What we predicted from Nordic pollen on the 31 author targets

We asked how observed pollen transfers to a country excluded from training.
In our [source-bound study](../../docs/report/regions/nordic/author-target-pollen/report.json),
we used the 31 non-excluded targets in the authors' exact 10,788-row
[LandClim II taxonomy lookup](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv).
We kept the same selected Danish, Finnish and Norwegian Neotoma/EPD samples
and 500-cal-BP bins as the [16-label study](../../docs/report/regions/nordic/direct-pollen/RESULTS.md).
For each excluded country, we trained on three Swedish EPD lake profiles and
the other two Nordic countries. We removed the target country from every
training input. The [input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json)
hashes six predictor inputs and three separate [target-outcome files](../../docs/report/regions/nordic/author-target-pollen/sealed-outcomes).
The predictor read only the six files in [inputs](../../docs/report/regions/nordic/author-target-pollen/inputs).
We saved and SHA-256-identified [predictions](../../docs/report/regions/nordic/author-target-pollen/predictions)
before opening target counts for [scoring](../../docs/report/regions/nordic/author-target-pollen/scores.csv).
We stored the large input, target and prediction tables as deterministic
gzip-compressed JSON with checked identities.

| Target country | Sites | Selected samples | Native NISP assigned to author targets | Scored site-bins / attempted | Refused bins | Best fixed baseline by site-macro MAE; Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998 / 129,768 (94.78%) | 24 / 24 | 0 | nearest site: 0.023242; 0.342996 |
| Finland | 28 | 1,797 | 1,229,019 / 1,260,281 (97.52%) | 435 / 435 | 0 | nearest site: 0.017335; 0.268166 |
| Norway | 52 | 3,544 | 2,018,295 / 2,286,020 (88.29%) | 1,084 / 1,178 | 94 | inverse distance squared: 0.019459; 0.303587 |

We used three fixed methods: training mean, nearest site and inverse distance
squared. All **1,543** scored site-bins have the same three methods, giving
**4,629** [method scores](../../docs/report/regions/nordic/author-target-pollen/scores.csv). The 94 refused Norwegian bins have
fewer than two training site groups with positive 31-target counts. The
[coverage ledger](../../docs/report/regions/nordic/author-target-pollen/coverage.csv) retains every attempted target. We first averaged eligible bins within each physical site; the
[site scores](../../docs/report/regions/nordic/author-target-pollen/site-scores.csv) and [taxon diagnostics](../../docs/report/regions/nordic/author-target-pollen/taxon-diagnostics.csv)
retain the contributing units. We selected no candidate using target outcomes.

We treat this as exploratory: we had inspected country outcomes in the
16-label analysis before designing the broader response. Our 31 targets
aggregate native pollen names. We kept author-excluded and unmapped NISP
outside the scored subcomposition and accounted for them in the
[taxonomy ledger](../../docs/report/regions/nordic/author-taxonomy-mass/README.md). Its MAE cannot be
compared numerically with the 16-label MAE as though the target fractions had
the same denominator or axis. Denmark has one site, so the Danish score does
not establish between-site Danish skill. Site-center distances are used;
age-specific basin support was not asserted. These are observed-pollen
predictions, not REVEALS/LOVE outputs or independent vegetation validation.
We admitted **zero samples to LRA** through this study.

For Dalmutladdo, we also applied a
[strict LegacyAge interval screen](../../docs/report/regions/nordic/dalmutladdo-author-target-age-interval/README.md)
to the already frozen Norway-excluded 31-target predictions. Only two of
72 samples have their full reported 95% age interval inside their original
500-year bin. Six predictions across those two bins remain scored; 20 of
22 originally scored Dalmutladdo bins have no eligible sample. Inverse
distance squared has a two-bin MAE of 0.006445, compared with 0.006341
for the parent's complete outcome compositions on those same bins. The
sample-matched nominal score is identical to the strict score because
neither retained sample changes bin. These small support-dependent numbers
do not establish temporal transfer skill or admit LRA inputs.

For Solsø, our separate [31-author-target strict-interval study]
(../../docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/README.md)
keeps 15 of 91 comparable samples in eight of the parent's 24 bins. We
reused 24 frozen Denmark-excluded predictions without refitting. The
nearest-site MAE is 0.025673 on the retained author-assigned counts, compared
with 0.025513 on complete parent counts in the same bins. The source-count
replay reconciles all 24 original bins, including excluded and unmapped NISP.
This exposed one-lake sensitivity uses a different axis and denominator from
the 16-label Solsø study; its scores cannot be pooled with that study or
interpreted as LRA or independent temporal skill.

We retained derived target counts and predictions without copying the private
author source or raw Neotoma transports. We recorded the source identities and
author lookup hash in the input manifest. Our
[Neotoma](../../docs/public/pollenomics-data/sources/neotoma.md) and
[LandClim](../../docs/public/pollenomics-data/sources/landclim.md) reviews
record the separate source and attribution boundaries.

The current ten prepared source products reproduce through the qualified
preparation entry point below. It authenticates the complete retained author
snapshot before reading and before publication, and requires an absent output
beneath repository `artifacts/`. The checked-in source manifest now binds the
current direct-pollen and author-count inputs. The nine compressed matrices,
sample membership, taxon axis and count denominators retain their earlier bytes.
Qualification establishes source custody; source-use rights and LRA admission
remain separate.

The retained prediction study used product revision
`6cf0e1134193174f214cd280a96e60b08fadf22f`. Rebinding the preparation and
score provenance did not rerun predictions or model fitting. The subsequent
prediction and scoring commands show the original study recipe for a deliberate
new computation; they are separate from preparation-only reproduction. For a
score-only replay, use the existing frozen prediction directory and an absent
score destination.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic.author_target_preparation \
  --repository . \
  --source-root "$SOURCE_STORE" \
  --source-descriptor configs/ci/qualified-report-sources/landclim-author-snapshot.json \
  --output artifacts/jobs/nordic-author-target-pollen-prepared-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_author_target_pollen predict \
  --prepared artifacts/jobs/nordic-author-target-pollen-prepared-replay \
  --output artifacts/jobs/nordic-author-target-pollen-predictions-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_author_target_pollen score \
  --prepared artifacts/jobs/nordic-author-target-pollen-prepared-replay \
  --predictions artifacts/jobs/nordic-author-target-pollen-predictions-replay \
  --output artifacts/jobs/nordic-author-target-pollen-scored-replay
```


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Fixed 31-author-target observed-pollen country-held-out predictions and score/refusal accounting.

**Unsupported claim.** Between-site Danish or Nordic vegetation skill.

**Actual verification performed.** Retained sealed prediction hashes, source taxonomy ledger and score report are cited; index did not rerun prediction.

**Remaining input or review.** 31-target country-held-out pollen scores are development evidence; Denmark has one target site, source age bins and closed taxon mass do not validate LRA or measured vegetation. Resolver: Independent cohort owner and qualified pollen/vegetation reviewer Reopen when: A fresh site-grouped cohort and independently matched measured cover are qualified before target outcomes are opened.

**Cause category.** comparability|qualified review

**Consequence.** Do not pool this 31-target denominator with the 16-label study or interpret pollen error as cover accuracy.

**Precise next acceptance route.** A fresh site-grouped cohort and independently matched measured cover are qualified before target outcomes are opened. Then update reports/science/pollen-prediction.md.

**Negative or refused result.** 94 Norway bins refused; zero LRA or measured-vegetation scores evaluated.

**Matched denominator.** DK 1 site/24 of 24 bins; FI 28/435 of 435; NO 52/1,084 of 1,178; assigned/native NISP recorded per country.

Retained evidence: [docs/report/regions/nordic/author-target-pollen/report.json](../../docs/report/regions/nordic/author-target-pollen/report.json), [docs/report/regions/nordic/author-taxonomy-mass/README.md](../../docs/report/regions/nordic/author-taxonomy-mass/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 48d076306e9ded340024a797d269f2c8541ddc22d075152117c6cb59d86ce036 -->
<!-- scientific-authored-source-sha256: 392ab7a45887311d27d4ba407962114b02c80d44d57d3faa91a1a6ee78416769 -->
<!-- scientific-verification-and-limits:end -->
