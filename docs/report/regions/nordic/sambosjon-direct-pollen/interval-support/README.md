# Sämbosjön pollen prediction on contained age support

How much does the fixed observed-pollen score change when samples whose reported age interval crosses a nominal 500-cal-BP boundary are excluded? This sensitivity retains **53 of 111** selected source samples in **21 of 22** candidate bins. The primary inverse-distance-squared prediction has equal-bin MAE **0.023054** and Hellinger distance **0.185741**. The original observations on these same 21 bins have MAE **0.022881** and Hellinger distance **0.183698**. This small descriptive difference does not estimate an age posterior or establish ecological accuracy.

## Source support and count denominator

The physical site, SAMBOTOT core, pollen dataset and selected MADCAP chronology are those in the [parent study](../README.md). The [source age-bound screen](../age-bounds/README.md) provides younger and older marginal bounds, with no stated confidence level. We retain a sample only when its interval has positive-width overlap with just its nominal bin. An older endpoint exactly touching the next bin contributes no width there, matching that source screen. No crossing sample is reassigned. Point ages, training sites, labels and the [66 frozen predictions](../frozen/predictions.json) stay fixed; no method is fitted or selected after scoring.

The [111-row sample ledger](samples.csv) partitions 393,822 native NISP pollen counts into 185,150 retained and 208,672 crossing-sample counts. Retained samples contribute 108,163 counts on the fixed 16-label axis and 76,987 outside it; excluded samples contribute 116,128 and 92,544 respectively. These four masses close to the parent's 224,291 closed-axis and 169,531 outside-axis counts. The fraction scores concern the retained closed pollen subcomposition, rather than all pollen or vegetation.

The [coverage ledger](coverage.csv) keeps all 22 attempted bins. Bin 1 (500–1000 cal BP) has no wholly contained sample and is explicitly refused; its three method rows have null scores. Bins 2–22 supply 63 scored method/bin pairs. Refused bins are neither zero-error observations nor omitted successes.

## Compare the same bins and predictions

| Fixed method | Paired bins | Contained MAE | Original MAE, same bins | Contained Hellinger | Original Hellinger, same bins |
| --- | ---: | ---: | ---: | ---: | ---: |
| Inverse distance squared, primary | 21 | 0.023054 | 0.022881 | 0.185741 | 0.183698 |
| Nearest site | 21 | 0.026731 | 0.026545 | 0.238368 | 0.235900 |
| Training mean | 21 | 0.037673 | 0.037562 | 0.285562 | 0.284419 |

[All 66 score/refusal rows](scores.csv) and the [machine report](report.json) retain the full precision, original paired scores and exact input identities. Every nominal-bin count denominator and score was reproduced exactly before calculating the restricted response. Equal-bin means weight each supported bin equally; there is no between-site uncertainty estimate from this single core. The original all-22-bin primary MAE of 0.022991 answers a different support question and is not the matched comparator above.

These counts and parent outcomes had already been exposed. This is a one-site development sensitivity. Marginal containment cannot represent correlated age uncertainty, a confidence interval, an untouched confirmation, Nordic LRA or an independent vegetation comparison. The nearby LandClim SAM point remains a refused core-identity join. Source attribution and reuse conditions remain those of the parent Neotoma/EPD study.

## Reproduce this sensitivity

The `bijux_pollenomics_dev.source_completion.pollen_age_support.sambosjon` producer verifies ten pinned parent/age-screen inputs, the preparation/freeze relations and original source-part hashes before reading target counts. It refuses changed inputs, duplicate predictions, altered physical-site exclusion, unusable contained count support and parent-score disagreement. It writes the four numeric files into a previously absent directory:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_age_support.sambosjon \
  --repository . --output artifacts/jobs/sambosjon-interval-support/reproduction
```

A second independent invocation reproduced all four retained files byte for byte. Focused checks exercise matched-bin scores, count-mass closure, refused/null outcomes, duplicate prediction and sample-support rejection, input drift before count reads, and the source-screen boundary convention. Qualified scientific review and a collaborator reading exercise remain outstanding.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained sensitivity keeps53wholly contained samples and fixed predictions, comparing the same21supported bins against the original full-bin response.

**Unsupported claim.** It is not an age posterior, refit, independent confirmation, NordicLRA or measured vegetation comparison; the original22-bin score answers a different support question.

**Actual verification performed.** Executed the maintained source-owned contained-age replay without refitting on the frozen source candidate. All 111 native sample IDs and 66 frozen predictions were reaggregated; all three CSV files and every report scientific value match the retained account exactly. Only the producer identity changed. The maintained verifier accepted the fresh result and refused a 1e-9 summary alteration and incorrect producer hash. No chronology model, fit, ecological validation or human scientific review was performed.

**Remaining input or review.** Current-source contained-age correspondence is established for the frozen inputs; scientific chronology qualification and collaborator review remain outstanding.

**Cause category.** Conditional marginal age support; chronology and qualified review remain unresolved.

**Consequence.** Withholding crossing samples alters count composition and slightly worsens the fixed primary paired score without implying a model-selection result.

**Precise next acceptance route.** Obtain source-qualified chronology support and qualified review of the same-bin comparison. If source samples, frozen predictions or producer behavior change, repeat the named contained-age consumer and preserve all refusals before changing the claim.

**Negative or refused result.** 58crossing samples remain excluded; bin1has three refused/null method rows, rather than zero error or omitted failure.

**Matched denominator.** 53of111samples in21of22bins;63scored of66method/bin rows;185,150retained native NISP/108,163closed-axis; primaryMAE0.023054versus0.022881on the same bins.

Qualified authored reader SHA-256: `f310296f6d26888737c96f14c4848d91518980f34105a12ba0056bdee7ed6fb2`.

- [Retained qualification evidence: docs/report/regions/nordic/sambosjon-direct-pollen/interval-support/report.json](report.json) (SHA-256 `89d33e6a2a0f5a352764093972c02e29f4c7d9eef1988fbff3fb3029a71326dc`).

- [Canonical scientific account: reports/science/sambosjon-direct-pollen.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sambosjon-direct-pollen.md) (source SHA-256 `7de581e27ffefb4ac8d99403a1ac6d8fedf97971ab5886e4f28a63a954e0366a`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
