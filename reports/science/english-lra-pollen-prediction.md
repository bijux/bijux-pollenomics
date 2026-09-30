# Our constrained LOVE study on author source pollen

We asked whether a real REVEALS/LOVE reconstruction could produce held-out
pollen predictions from an admitted author source profile. We selected 15
English sites in the 1250–1750 BP source window. Their 31-target author pollen
counts total 20,732 NISP. We excluded `Filipendula` (159 NISP, 0.767%)
because its published 0.006 m/s fall speed falls outside the selected
optimized LOVE transport contract. We kept that excluded mass and the
original count denominator with the exact source hashes. Our resulting
**30-target closed composition** is neither whole pollen nor whole vegetation.

We used the published remaining PPE and fall speeds, the declared homogeneous
author-example basin and ring assumptions, deterministic REVEALS and
ring-taxon-preserving LOVE. We chose one uniform-start SLSQP search that keeps
local cover nonnegative and closed. Its limits were 300 iterations, 16,000
objective evaluations and a `1e-8` objective tolerance, with no convergence
waiver. Our initial 120-iteration full-fold run produced 149 of 195 training
products but no fold predictions because 46 training fits refused. We raised
the limit in response to those training failures before opening any target
pollen. This is a development comparison with our analytical and
differential-evolution attempts. The original R source uses a different
optimizer.

We held out one physical site per outer fold and recomputed regional REVEALS
and training-site LOVE from the remaining pollen. We opened target pollen only
after publishing and authenticating each prediction product. The predicted
vegetation comes from LRA; we have no independent measured vegetation for an
accuracy score. This English experiment does not admit Swedish or four-country
LRA inputs.

## What the three LOVE routes established

We keep the method and taxon changes visible when comparing our development
runs. They are different requests on previously exposed author source, not a
paired ranking of algorithms on one admitted response:

| Route and source axis | Attempted support | Retained outcome |
| --- | --- | --- |
| [Analytical LOVE](../../docs/report/pollen-reconstruction/author-lra-development/README.md), all 31 author taxa | 15 whole-site folds; 195 training items | All 15 folds refused `invalid_composition`; every one of 54 local ring rows had a negative fraction. No held-out prediction or score. |
| [Differential-evolution optimized LOVE](../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md), 30 taxa after excluding 159 `Filipendula` counts | One selected regional/local training pair; two bounded requests | Neither request converged; no valid LRA product or held-out score. |
| Our constrained SLSQP LOVE, the same declared 30-taxon subcomposition | 15 whole-site outer folds; 195 training items | Fourteen folds yielded 42 frozen forward-pollen predictions; BECKHAM refused because three training fits did not converge. |

The analytical equation replay agrees with its saved ring outputs to
`2.67e-15`; it confirms the negative values are produced by that equation,
not that they describe a physical landscape. The differential-evolution
pilot refused within its stated limits on one pair, while the SLSQP run supplied
usable closed-cover predictions on most folds. We cannot infer that SLSQP is
generally the best LOVE solver, that excluding `Filipendula` improves ecology,
or that a different budget would settle the refused sites.

## Source-bound result

Our [retained report](../../docs/report/pollen-reconstruction/author-lra-constrained/report.json)
binds the source, prediction and score manifests. We rotated all 15 sites as
targets. Fourteen folds produced three predictions each. We refused the
BECKHAM fold because training LOVE fits for CUTHILL2, HANGINGS and
LONGBREACH did not converge: 192 of 195 training items completed and three
refused. The same three requests refused in a bounded 600-iteration check.
We inspected the 300-iteration item receipts to locate the failure inside the
optimizer rather than treating the fold as missing source pollen:

| Training site in BECKHAM fold | SLSQP stop message | Iterations | Evaluations | Objective |
| --- | --- | ---: | ---: | ---: |
| CUTHILL2 | Positive directional derivative for linesearch | 147 | 4,898 | 0.823089 |
| HANGINGS | Positive directional derivative for linesearch | 129 | 4,210 | 1.116182 |
| LONGBREACH | Positive directional derivative for linesearch | 156 | 5,123 | 0.587412 |

The three item receipts have SHA-256 values
`a265301a4fce6cf39fb07e2004e5fc35477223b058657efdd03508acd24ba946`,
`644a038e5b620792357d7c72cb7d39f7f6aeda13ee0034c1aa979c85e45cc561`
and `f110eab284b6713a12721a92ba1f392e4315222551e7943f11ada1ca2b3abef1`
in the table's row order. Their original run products remain under
`artifacts/jobs/author-lra-slsqp-development/withheld-predictions-300/`.

All three stopped below both declared caps. This points to a local search
failure rather than exhaustion of the 300-iteration or 16,000-evaluation
budget; it does not prove that another solver can certify the same fit. We
retain the complete-fold refusal and do not score BECKHAM as if the three
training reconstructions existed.

We preserved full-precision closed cover fractions because four-decimal
rounding had yielded a `1.0002` sum that the consumer correctly rejected.

We froze all 42 predictions before opening the 14 target pollen rows and
verified that no target record enters its prediction input closure. The
[fold table](../../docs/report/pollen-reconstruction/author-lra-constrained/folds.csv),
[30-taxon vegetation and forward-pollen predictions](../../docs/report/pollen-reconstruction/author-lra-constrained/predictions.csv),
and [held-out scores](../../docs/report/pollen-reconstruction/author-lra-constrained/scores.csv)
retain every method row and the BECKHAM refusal. Site-mean pollen MAE across
the 14 scored sites is 0.026273 for the LRA training mean, 0.021132 for
nearest training site and 0.021088 for inverse-distance-squared interpolation
(fractions of the closed 30-target pollen composition). We treat these as
development scores on previously exposed examples with overlapping training
folds. We cannot infer vegetation accuracy, an uncertainty interval or broad
spatial generalization from them.

We [compared direct observed-pollen prediction](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/comparison.json)
with the same three fixed spatial methods on these exact 14 sites and 30
taxa. We retained its prediction manifest and all 45 unscored site-method
[prediction rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/predictions.json)
before opening direct target outcomes. We excluded BECKHAM from the
[paired scores](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/matched-scores.csv)
to match LRA support. Direct-pollen MAE is 0.020496
versus LRA 0.026273 for training mean, 0.019552 versus 0.021132 for nearest
site, and 0.018579 versus 0.021088 for inverse-distance-squared. All three
fixed direct-pollen baselines score lower on this matched development support.
We compared pollen prediction under the declared center-distance geometry:
direct prediction used all 14 training pollen sites, while LRA used one
regional anchor and 13 local reconstruction predictors. This does not measure
vegetation accuracy or constitute an independent final test.

We [checked site influence](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/site-sensitivity.json)
against the published comparison and 42 SHA-256-bound score rows. Direct pollen has lower MAE
at 13/14 sites for training mean, 7/14 for nearest site, and 10/14 for
inverse-distance-squared interpolation. The nearest-site median paired
direct-minus-LRA difference is **+0.000244**, despite its negative mean of
**−0.001580**; the mean advantage is concentrated in sites with larger direct
gains. Omitting any one scored site leaves all three mean differences negative.
We retain the individual directions because these correlated English sites
and overlapping training folds cannot support a sampling confidence interval
or spatial-transfer claim. We exclude BECKHAM throughout because its LRA fold
refused.

For our [matched Hellinger result](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger.json),
we reopened the same 14 raw target rows after both prediction sets were
frozen. We bound the source experiment, direct prediction manifest, LRA
prediction identities and LRA score table. We used the original observed
30-taxon composition without smoothing target counts. Site-macro distances
are:

| Fixed method | Direct pollen | LRA forward pollen | Sites favoring direct |
| --- | ---: | ---: | ---: |
| Training mean | 0.282082 | 0.360671 | 14/14 |
| Nearest site | 0.255767 | 0.286001 | 7/14 |
| Inverse-distance-squared | 0.243673 | 0.285415 | 11/14 |

We treat these as descriptive distances on prior-exposed English support. The
14 sites provide neither a sampling interval nor independent vegetation truth.

We [rechecked site influence](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger-sensitivity.json)
against the Hellinger report and omitted each site in turn. Every omitted-site
mean direct-minus-LRA difference remains negative: training mean
`[-0.082443, -0.070006]`, nearest site `[-0.035318, -0.018215]`, and
inverse-distance-squared `[-0.046139, -0.034002]`. Nearest site still favors
direct at only 7/14 individual sites, so the negative average alone does not
say every site agrees. We report influence accounting here, not an independent
confidence interval or a vegetation score.

## Basin radius in the forward consumer

We tested the effect of the declared author-example lake radius on the
forward-pollen calculation. We kept all 42 published LRA vegetation estimates,
regional cover values, PPE, fall speeds and training fits fixed, and changed
each target's circular radius to 80% or 120% of its declared value. The
[prediction freeze](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/frozen/predictions.json)
contains 126 projections for the 14 scored sites and three fixed methods.
At the original radius, all 42 pollen fractions reproduce exactly. We then
opened the observed target counts and retained the
[126 paired scores](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/scored/scores.csv)
and [method summaries](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/scored/report.json).

For inverse-distance-squared vegetation, we observed site-macro MAE of 0.021032 at 80%,
0.021088 at the declared radius and 0.021457 at 120%; Hellinger is 0.283976,
0.285415 and 0.289825. The nearest-site method follows the same aggregate
direction, while training-mean MAE changes in the opposite direction and its
Hellinger result is mixed. Individual site directions also differ. We treat
this as a forward-transport sensitivity on already exposed English outcomes,
not radius selection or a refitted LRA score. The original basin circles are
model assumptions; the diagnostic cannot transfer a radius to a Swedish core
or establish age-specific basin geometry. The
[governed method account](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md)
gives all method values and reproduction commands.

We then paired those radius scores with the already published direct-pollen
scores using the exact target observation identity. Across all three fixed
methods and all three radius factors, site-macro direct-pollen MAE and
Hellinger remain lower than fixed-vegetation LRA forward pollen. The
[126 paired rows](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired/paired-scores.csv)
show site exceptions: nearest-site direct MAE is lower at 6, 7 and 7 of 14
sites for 80%, 100% and 120% radius, respectively. We keep the difference in
training information and prior outcome exposure visible; this does not
select a model for Nordic cores.

## Reproduce our result

From the repository root, use the private author source capsule and an absent
output destination:

```sh
source_root=/path/to/private/landclim/author-reference
job=artifacts/jobs/author-lra-constrained-reproduction
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root "$source_root" --output "$job/source-inputs"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/prepare.py \
  --source "$job/source-inputs" --destination "$job/constrained-inputs"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_run \
  --inputs "$job/constrained-inputs" --cache-root "$job/cache" \
  --output "$job/predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/score.py \
  --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --destination "$job/scores" \
  --prediction-manifest-sha256 "$published_prediction_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/report.py \
  --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --scores "$job/scores" --destination "$job/report" \
  --prediction-manifest-sha256 "$published_prediction_sha256" \
  --score-manifest-sha256 "$published_score_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py predict \
  --inputs "$job/constrained-inputs" --destination "$job/direct-predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py compare \
  --inputs "$job/constrained-inputs" --direct-predictions "$job/direct-predictions" \
  --lra-scores "$job/report/scores.csv" --destination "$job/direct-comparison" \
  --prediction-manifest-sha256 "$published_direct_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py site-sensitivity \
  --matched-scores "$job/direct-comparison/matched-scores.csv" \
  --comparison "$job/direct-comparison/comparison.json" \
  --output "$job/site-sensitivity.json"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py hellinger \
  --inputs "$job/constrained-inputs" \
  --direct-predictions "$job/direct-predictions" \
  --lra-predictions "$job/report/predictions.csv" \
  --lra-scores "$job/report/scores.csv" \
  --lra-report "$job/report/report.json" \
  --comparison "$job/direct-comparison/comparison.json" \
  --output "$job/paired-hellinger.json"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py hellinger-sensitivity \
  --hellinger "$job/paired-hellinger.json" \
  --output "$job/paired-hellinger-sensitivity.json"
```

Set `published_prediction_sha256` to the digest printed by the prediction
command, and `published_score_sha256` to the digest printed by the score
command. Set `published_direct_sha256` to the digest printed by the direct
prediction command. Retain each before invoking its consumer.

The execution command requires the repository's installed package environment;
the local package source roots can be supplied through `PYTHONPATH` when using
an editable source checkout.
