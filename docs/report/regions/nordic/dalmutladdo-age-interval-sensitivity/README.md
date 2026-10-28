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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/dalmutladdo-lra-input/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/dalmutladdo-lra-input/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
