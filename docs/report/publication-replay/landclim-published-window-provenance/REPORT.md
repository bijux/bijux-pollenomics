# ESSD published-window numerical provenance

The exact 100–350 BP author bin in grids 512 and 562 is paired across the independent author-R replay, installed LRA computation, and pinned PANGAEA 937075 published estimate. The 31 taxon mean and standard-error axes close in each grid (124 numerical values). Fractions from the author-R replay are multiplied by 100 before comparison with published percentage cover.

| Grid | Metric | Maximum absolute R–archive gap (percentage points) | Median absolute gap | Maximum Python–R gap | Largest-gap taxon |
| --- | --- | ---: | ---: | ---: | --- |
| 512 | mean | 9.19787 | 0.0214392 | 1.23800e-11 | Cyperaceae |
| 512 | standard_error | 3.21615 | 0.0114477 | 3.28900e-12 | Cyperaceae |
| 562 | mean | 10.5527 | 0.0322204 | 3.8700e-12 | Calluna.vulgaris |
| 562 | standard_error | 4.25814 | 0.0145312 | 3.42100e-12 | Calluna.vulgaris |

The shared 31-taxon means are summed without renormalization. L1 is the sum of absolute percentage-point gaps across those taxa; total variation is L1/200, and Hellinger uses the nonnegative percentage means divided by 100. Both vectors must sum to 100% within 0.000001 percentage points. These are modeled-product correspondence distances, not vegetation accuracy.

| Grid | Archive mean sum (pp) | Author R mean sum (pp) | Mean L1 gap (pp) | Total variation | Hellinger | Two largest-gap taxa | Share of L1 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 512 | 100.000000 | 100.000000 | 18.481237 | 0.092406 | 0.078055 | Cyperaceae, Calluna.vulgaris | 0.729 |
| 562 | 100.000000 | 100.000000 | 22.140770 | 0.110704 | 0.101288 | Calluna.vulgaris, Poaceae | 0.940 |

On this author example, the archive difference also appears in the independent R replay; it is not a Python-only numerical discrepancy. The 2016 author-example and June 2021 archive historical raw-input cohorts are not closed as identical. This does not reproduce the 1,128-row published study or evaluate measured vegetation accuracy.
