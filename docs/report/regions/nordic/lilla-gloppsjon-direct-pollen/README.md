# Lilla Gloppsjön observed-pollen prediction freeze

The [protocol](protocol.json) fixes Neotoma/EPD site `3234` at 14.62333° E,
59.80167° N, its `LGLOPPSJ` core `4071`, and pollen dataset `4200`
([dataset DOI](https://doi.org/10.21233/vpnw-pv89)). This is a lake-center
distance prediction with the existing 16 literal pollen labels, 500-cal-BP
point-age bins, and fixed training mean, nearest-site, and inverse-distance-squared
baselines. It has **no target pollen score or composition**. The source site is
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
outcomes. That historical parsing limits an untouched-lockbox claim.

The [prediction file](frozen/predictions.json) contains **69 prediction rows**:
all three fixed methods for each of **23 age-candidate bins**. Every bin has
at least two positive-count training physical sites (38–73 across bins), so the
fixed training-support rule refused zero bins. These are training-site support
figures; target pollen-positive support is unknown. The deterministic
[freeze](frozen/freeze.json) is SHA-256
`bc89f334d95b727d2a051efaa794a131f1d13eee0613f1c32f6e6ace67a6e997`;
the predictions SHA-256 is
`844db7dd47a93eba5d0630719df992d211ced59464e917314e2b5ff131d36a17`.
The frozen primary method is inverse distance squared. No method or support
rule has been selected using this target's pollen outcomes.

The separate [scoring protocol](scoring-protocol.json) was declared against
these fixed prediction bytes before target observations were opened for this
study. It fixes the 16-label count admission, equal-bin MAE and Hellinger
metrics, paired comparison support, and explicit bin refusals. Scoring remains
pending here; the protocol does not supply a result.

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
workspace sibling path. Neither command reads target observations or scores
predictions:

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
```

This is a prediction freeze for one newly targeted physical site. It is neither
an independent observed-pollen confirmation nor LRA or measured-vegetation
validation. A separately governed scoring stage would first verify this freeze
and source identity, then open target pollen counts and retain every attempted,
scored and refused bin.
