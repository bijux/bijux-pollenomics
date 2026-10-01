# Lilla Gloppsjön observed-pollen transfer

The [protocol](protocol.json) fixes Neotoma/EPD site `3234` at 14.62333° E,
59.80167° N, its `LGLOPPSJ` core `4071`, and pollen dataset `4200`
([dataset DOI](https://doi.org/10.21233/vpnw-pv89)). This is a lake-center
distance prediction with the existing 16 literal pollen labels, 500-cal-BP
point-age bins, and fixed training mean, nearest-site, and inverse-distance-squared
baselines. The prediction freeze contains **no target pollen composition**;
scoring is a separate stage below. The source site is
distinct from the four earlier Swedish targets. A same-name LandClim point is
0.396271 km away, but the governed site comparison does not establish physical
identity or permit its radius to be transferred.

The single source core has **86 samples**. The protocol names all 86 sample IDs,
the exact **84** comparable calibrated sample-age claim IDs selected from
chronology `neotoma:chronology:4071:29939`, and the two refused claims. The
refused samples have negative younger bounds. The selected point ages span
94–11,082 cal BP; all 84 have source younger and older bounds, whose confidence
level is not stated. The calibrated chronology is the Giesecke et al. 2014
MADCAP smooth spline using IntCal09 and 14 source controls. The collection-unit
reference points instead to radiocarbon-year chronology `29938`; the protocol
explicitly refuses that chronology for calibrated bins.

The [prepared metadata](inputs/metadata.json) and
[input manifest](inputs/input-manifest.json) lock the allowed metadata read set
and reuse the previously governed deterministic gzip profile of 84 distinct
training sites. It contains no site `3234`, dataset `4200`, or target site-name
alias. The historical source-validation screen that made that training profile
parsed the full Neotoma observation partitions, including this future target,
but selected only 81 DK/FI/NO and three other Swedish physical-site profiles
for training. This study does not open target taxon observations or count
outcomes during prediction preparation. That historical parsing limits an
untouched-lockbox claim.

The [prediction file](frozen/predictions.json) contains **69 prediction rows**:
all three fixed methods for each of **23 age-candidate bins**. Every bin has
at least two positive-count training physical sites (38–73 across bins), so the
fixed training-support rule refused zero bins. These are training-site support
figures; target pollen-positive support was unknown at the freeze. The deterministic
[freeze](frozen/freeze.json) is SHA-256
`bc89f334d95b727d2a051efaa794a131f1d13eee0613f1c32f6e6ace67a6e997`;
the predictions SHA-256 is
`844db7dd47a93eba5d0630719df992d211ced59464e917314e2b5ff131d36a17`.
The frozen primary method is inverse distance squared. No method or support
rule has been selected using this target's pollen outcomes.

The separate [committed scoring protocol](scoring-protocol.json), SHA-256
`e3ebc64b8804a6583d72d542beb9550f7046d735f92f2a6817a60eb18f545e51`,
fixed the source read order, count denominator, equal-bin MAE and Hellinger,
paired support, and refusal handling before target outcomes were interpreted.
The scorer verified the committed freeze, prepared metadata, training receipt,
relational manifest, and every recorded metadata and observation part hash
before parsing target counts. The [sample-count table](scored/sample-counts.csv),
[bin coverage](scored/coverage.csv), [scores](scored/scores.csv), and
[machine report](scored/report.json) preserve the result.

All **86 source samples** have admitted direct pollen count rows. The 84
age-selected samples contribute 123,384 native NISP, of which 54,929 are on
the exact 16-label axis and 68,455 are outside it. The two age-refused samples
remain visible with 3,643 native, 709 closed-axis, and 2,934 outside-axis NISP.
Across all 86 samples, native NISP is **127,027**, closed-axis NISP **55,638**
(43.80%), and outside-axis NISP **71,389**. These are observed pollen count
denominators, not vegetation fractions. The source has 1,946 admitted direct
count rows and 579 other target observation rows excluded by the declared
count rule.

All **23 candidate bins** had positive target closed-axis counts and were
scored by all three frozen methods on identical support. There were zero
missing, zero-axis, training-support-refused, or failed bins. Mean absolute
error and Hellinger are equal-bin means for this single site:

| Fixed method | Scored bins | MAE | Hellinger |
| --- | ---: | ---: | ---: |
| Inverse distance squared, frozen primary | 23 | 0.017295 | 0.237576 |
| Nearest site | 23 | 0.020000 | 0.228724 |
| Training mean | 23 | 0.016272 | 0.256392 |

The frozen primary method is not the lowest on either metric here: training
mean has the lowest MAE, and nearest site has the lowest Hellinger. This one
site is descriptive development evidence and does not justify changing the
fixed method. Source age bounds are not propagated through point-age bins.

The retained primary-publication response identifies Almquist-Jacobson, H.
(1994), *Interaction of the Holocene climate, water balance, vegetation, fire,
and cultural land-use in the Swedish Borderland*, Lund University doctoral
dissertation, LUNDQUA Thesis 30:1–82. The provider response is
`bijux-pollenomics-data/neotoma/publication-links/2026-09-29/responses/dataset-4200-publications.json`
at SHA-256 `1a13124e576effcbd1f95d5db4b9b7cbda65baf92ab679381b161f209319d471`.
[Neotoma's 2025 Data Use and Embargo Policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
permits available data under CC BY 4.0 with Neotoma, EPD, original-investigator,
primary-publication and dataset-DOI attribution. The relational source manifest
is SHA-256 `6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b`.

Replay from the repository root into absent directories under `artifacts/`;
the external Neotoma publication-link source store must be present at the
workspace sibling path. Preparation and prediction do not interpret target
observations; the final command verifies the source read set before scoring:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen prepare \
  --repository . --output artifacts/jobs/lilla-gloppsjon-freeze/inputs
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen predict \
  --repository . --prepared artifacts/jobs/lilla-gloppsjon-freeze/inputs \
  --output artifacts/jobs/lilla-gloppsjon-freeze/frozen
shasum -a 256 artifacts/jobs/lilla-gloppsjon-freeze/inputs/*.json \
  artifacts/jobs/lilla-gloppsjon-freeze/frozen/*.json
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.lilla_gloppsjon_direct_pollen_scoring \
  --repository . --prepared artifacts/jobs/lilla-gloppsjon-freeze/inputs \
  --frozen artifacts/jobs/lilla-gloppsjon-freeze/frozen \
  --freeze-sha256 bc89f334d95b727d2a051efaa794a131f1d13eee0613f1c32f6e6ace67a6e997 \
  --output artifacts/jobs/lilla-gloppsjon-freeze/scored
shasum -a 256 artifacts/jobs/lilla-gloppsjon-freeze/scored/*
```

This is a new-site direct observed-pollen development result with a prior
all-part source-validation parse. It is neither an untouched independent
confirmation nor LRA, measured-vegetation accuracy, basin-buffer validation,
or broad Swedish generalization.
