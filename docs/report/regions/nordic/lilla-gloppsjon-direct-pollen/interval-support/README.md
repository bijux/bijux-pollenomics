# Lilla Gloppsjön pollen scores on contained age intervals

The [original study](../README.md) scored 23 nominal 500-cal-BP bins using
point ages from Neotoma/EPD site `3234`, core `4071`, dataset `4200` (DOI
`10.21233/vpnw-pv89`). This sensitivity keeps a sample only when both source
age bounds fall inside its point-age bin. It reuses the same 69 frozen
predictions, three fixed methods, 16 literal pollen labels and count rule.
Nothing is refitted or assigned to a neighboring bin.

The [sample ledger](samples.csv) partitions all 86 source samples: 42 of the
84 selected calibrated-age samples are wholly contained, 42 cross a bin
boundary, and two retain their original negative-bound age refusal. The 42
contained samples carry 61,647 native pollen NISP, of which 28,310 are on the
closed 16-label response. The crossing samples carry 61,737 native and 26,619
closed-axis NISP. The two age-refused samples carry 3,643 native and 709
closed-axis NISP. All three groups sum to the original 127,027 native and
55,638 closed-axis NISP. Counts outside the response remain visible.

The [coverage](coverage.csv) retains all 23 candidate bins. Twenty contain
positive closed-axis counts from at least one wholly contained sample and
score all three methods; bins 20–22 have no contained sample and are refused.
The [69 method/bin rows](scores.csv) preserve each attempted status, count
denominator, contained score and original full-bin score. On the same 20 bins:

| Fixed method | Contained MAE | Original full-bin MAE | Contained Hellinger | Original full-bin Hellinger |
| --- | ---: | ---: | ---: | ---: |
| Inverse distance squared, frozen primary | 0.019316 | 0.018367 | 0.249632 | 0.242217 |
| Nearest site | 0.020786 | 0.021199 | 0.230690 | 0.229585 |
| Training mean | 0.017497 | 0.016489 | 0.263196 | 0.257241 |

These are paired by bin and method, while the pollen composition inside a bin
changes when boundary-crossing samples are withheld. The original 23-bin score
is a different denominator. The source bounds have no stated confidence level
or joint age posterior, so this is a conditional marginal-bound sensitivity,
not a probabilistic age correction or a forward-time score. The target was
already exposed in the original descriptive development study. This result
does not measure vegetation, admit LRA inputs or rank methods generally.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/interval-support/replay.py) verifies the committed prediction and scoring
protocols, every declared Neotoma source part, selected source age-claim values
and bounds, and byte-reproduces the original sample, score and coverage files
before computing this sensitivity. The [machine report](report.json) retains
the source, freeze and original-score identities. Replay into an absent
directory under the repository's `artifacts/` root and compare all four output
files byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/interval-support/replay.py \
  --repository . --output artifacts/jobs/lilla-gloppsjon-interval-support/replay
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/lilla-gloppsjon-direct-pollen.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/lilla-gloppsjon-direct-pollen.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
