# Dalmutladdo pollen prediction under strict LegacyAge age intervals

We tested the [frozen Norway-excluded direct observed-pollen predictions](../direct-pollen/RESULTS.md)
against a conservative age support rule for Neotoma dataset 20034 (DALMUT).
This is a **prior-exposed development sensitivity**, not a new held-out fit, LRA
reconstruction, or vegetation validation. The response remains the parent's
closed subcomposition of **16 literal pollen labels**. Its denominator is the
sum of those labels' native NISP counts, not all pollen or total vegetation.

The independent [LegacyAge S5 depth join](../../../source-relations/neotoma/legacyage-chronology/README.md)
provides 95% age ranges at exact sample depths. We retained a sample only when
its **entire** reported interval fits inside the original half-open 500-cal-BP
bin. The 95% endpoints are treated as a range, with no inferred posterior
probability or draw. An upper endpoint exactly on a bin edge fails this rule.
No age interpolation was made for the 4.5 cm sample.

| Support decision | Samples |
| --- | ---: |
| Parent Dalmutladdo cohort | 72 |
| Exact LegacyAge S5 depth match | 71 |
| Full interval inside original bin | 2 |
| Refused because interval crosses a bin boundary | 69 |
| Refused because no exact S5 depth exists | 1 |

The two retained samples are `175359` in bin 1 (500–1,000 cal BP) and `175366`
in bin 3 (1,500–2,000 cal BP). Their LegacyAge ranges are respectively
604–982 and 1,528–1,965 cal BP. Both stay in their source-selected Neotoma
point-age bins. The parent had 22 scored Dalmutladdo bins; 20 have no sample
under this rule. All 70 sample refusals are recorded in
[sample-support.csv](sample-support.csv). All eight reused predictions, four
fixed methods for two bins, remain in [predictions.json](predictions.json).

| Fixed method | Strict two-bin MAE | Parent MAE, same bins | Strict Hellinger | Parent Hellinger, same bins |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.038759 | 0.038960 | 0.352103 | 0.348078 |
| Nearest site | 0.001746 | 0.001831 | 0.079432 | 0.066567 |
| Inverse distance squared | 0.005701 | 0.005698 | 0.155724 | 0.148674 |
| CLR/RBF ridge | 0.003165 | 0.003102 | 0.103466 | 0.094985 |

These are **one-site, two-bin descriptive means**, with no independent site
uncertainty interval. The strict scores use only the two retained sample count
profiles. The paired nominal score on those same samples is identical because
neither sample changes bins. The parent columns use its complete original
outcome composition for bins 1 and 3 (six and three samples, respectively).
Differences between those columns reflect the changed sample support, not an
age-driven reassignment or an improved model. The [score ledger](scores.csv)
keeps each method and bin visible.

The [protocol](protocol.json) pins the parent prediction bytes, source join,
count axis and interval rule. `freeze` reads the age claims and existing
predictions but no target pollen observations; `score` subsequently opens the
source observations and checks all 22 reconstructed nominal bin denominators
against the parent scores. The [machine report](report.json) records the source
identities and result denominators. To replay from the repository root into a
new disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/regions/nordic/dalmutladdo-age-interval-sensitivity/replay.py \
  freeze --repository . --output artifacts/jobs/dalmutladdo-age-interval-check
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/regions/nordic/dalmutladdo-age-interval-sensitivity/replay.py \
  score --repository . --output artifacts/jobs/dalmutladdo-age-interval-check
```

The source does not identify these LegacyAge ages as the historical LandClim
ages. Two supported samples cannot establish Nordic transfer quality or
chronology robustness over the other 20 bins.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The prior-exposed16-label sensitivity reuses frozen Norway-excluded predictions on two samples whose entire95%LegacyAge intervals fit their original500-cal-BP bins.

**Unsupported claim.** Two-bin support cannot establish Nordic transfer quality, a joint age posterior, historical LandClim chronology, LRA or independent vegetation accuracy.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Historical study chronology and a source-qualified joint age model remain missing for those stronger claims; independent site support is absent.

**Cause category.** Conditional age-bound sample restriction on exposed development data.

**Consequence.** Differences from complete parent-bin scores follow excluded samples; the two retained samples do not change bins or imply an improved model.

**Precise next acceptance route.** Replay freeze then score with the same16labels and frozen predictions, retain all72sample decisions and compare the same two bins before any broader chronology claim.

**Negative or refused result.** 69crossing samples and one missing exact-depth join are refused;20of22parent bins have no supported sample.

**Matched denominator.** One site/dataset20034;72parent samples,71exact joins,two contained samples,two bins,four fixed methods/eight prediction rows; own response denominator is16-label NISP.

Qualified authored reader SHA-256: `a985c7dfcd8f7d581878f17a653203eecb4e1298987d7ef85798953dd18a3821`.

- [Retained qualification evidence: docs/report/regions/nordic/dalmutladdo-age-interval-sensitivity/report.json](report.json) (SHA-256 `80fcb5907888ba9983dbc32c6e19a4298947756a56fa8210fef6769e2a1ea33a`).

- [Canonical scientific account: reports/science/dalmutladdo-lra-input/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/dalmutladdo-lra-input/README.md) (source SHA-256 `93fb8bf7334d3919fbf25d2cc0d7a5f062bfe67fa23dfb0e69d0940494964702`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
