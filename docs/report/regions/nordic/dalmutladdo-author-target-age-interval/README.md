# Dalmutladdo age support on the 31 author pollen targets

We applied the [strict LegacyAge age-support screen](../dalmutladdo-age-interval-sensitivity/README.md)
to the separate [Nordic author-target observed-pollen study](../author-target-pollen/README.md).
This is a **prior-exposed development sensitivity**. It reuses the original
Norway-excluded predictions for the authors' **31 taxonomy targets**, whose
denominator is author-assigned native pollen NISP. The 16-literal-label study
uses another response and denominator; its scores are not pooled with these.

The [source age ledger](sample-support.csv) retains all 72 Dalmutladdo
samples: 71 have exact LegacyAge S5 depth joins, two have a full 95% age
interval inside their original 500-cal-BP bin, 69 cross a bin boundary, and
one lacks an exact model depth. The two retained samples are `175359` in bin 1
(604–982 cal BP) and `175366` in bin 3 (1,528–1,965 cal BP). Both remain in
their original Neotoma point-age bins. The parent has 22 scored site bins; 20
have no sample under this rule. The [protocol](protocol.json) pins the source
age screen, author lookup, country-excluded training inputs and six selected
prediction rows. `freeze` opens no target pollen observations.

| Fixed method | Strict two-bin MAE | Parent MAE, same bins | Strict Hellinger | Parent Hellinger, same bins |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.013300 | 0.013359 | 0.254225 | 0.246448 |
| Nearest site | 0.012786 | 0.010550 | 0.174777 | 0.155460 |
| Inverse distance squared | 0.006445 | 0.006341 | 0.112556 | 0.107032 |

These are one-site, two-bin descriptive averages. [Scores](scores.csv) show
each bin and method. Strict-interval and matched-sample nominal scores are
identical because the retained samples do not change bins. The original
parent columns use all samples in bins 1 and 3, respectively six and three.
Their differences from the strict scores reflect sample exclusion, not age
reassignment or a new fit. No independent-site uncertainty or model ranking
can be inferred from this two-bin support.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/regions/nordic/dalmutladdo-author-target-age-interval/replay.py) maps the original Neotoma observations through the
exact author taxonomy lookup after predictions are frozen. It verifies all
22 reconstructed nominal bins against the parent's sealed author-target
counts and excluded/unmapped mass. The [machine report](report.json) records
the input hashes, coverage and score values. Replay from the repository root
into a new disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/regions/nordic/dalmutladdo-author-target-age-interval/replay.py \
  freeze --repository . --output artifacts/jobs/dalmutladdo-author-age-check
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/regions/nordic/dalmutladdo-author-target-age-interval/replay.py \
  score --repository . \
  --author-source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/jobs/dalmutladdo-author-age-check
```

These ages do not establish the historical LandClim chronology, basin
geometry, PPE suitability or LRA admission. The result is directly observed
pollen prediction on a closed author-target count subcomposition.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/dalmutladdo-lra-input/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/dalmutladdo-lra-input/README.md) (source SHA-256 `93fb8bf7334d3919fbf25d2cc0d7a5f062bfe67fa23dfb0e69d0940494964702`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
