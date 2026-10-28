# Conditional compositional point estimator

Fix one native ring label and a held-out overlap group. For every remaining site s, let p_s and v_s be the strictly positive five-taxon pollen and deposited calculated-area compositions. Let M be the number of nonempty training groups and n_G the sites in group G. Set w_s = 1/(M n_G); all weights are positive and sum to one. Nothing here assumes that the source campaign or the groups are probabilistically independent.

Define closure C(x) = x / sum(x), and clr(x)_i = log(x_i) - mean_j(log(x_j)). Let z_s = clr(v_s) - clr(p_s). The centered correction solves

```text
minimize L(b) = sum_s w_s ||z_s - b||²
subject to sum_i b_i = 0.
```

Every z_s is centered. Consequently bar_z = sum_s w_s z_s is centered and feasible. Expanding the squared norm gives

```text
L(b) = sum_s w_s ||z_s - bar_z||² + ||b - bar_z||²,
```

because sum_s w_s(z_s - bar_z) = 0 and sum_s w_s = 1. The second term is nonnegative and vanishes only at b = bar_z. Thus bar_z is the unique centered minimizer. This statement also holds if there is only one training group, provided its weights are positive and normalized.

The implemented raw offset is delta_i = sum_s w_s log(v_si/p_si). Linearity of centering gives bar_z = center(delta). For a positive held-out pollen composition p,

```text
C(p * exp(delta)) = C(p * exp(center(delta))),
```

since subtracting a common log offset multiplies all components by one common positive factor that closure cancels. The uncentered least-squares mean delta is itself unique for its raw log-ratio objective. Only the closed prediction loses the common-offset information; this does not make the raw least-squares mean nonunique.

The training mapped baseline follows the same calculation with z_s = clr(v_s): its prediction is C(exp(sum_s w_s log(v_s))). The identity baseline is p. All three predictions are positive and sum to one under the source positivity and finite arithmetic conditions. Actual numerical positivity, normalization and saved predictions were qualified by the separate native Decimal implementation; this derivation does not substitute for that result.

Training minimizes the stated centered log-residual objective. Held-out evaluation uses prespecified squared Hellinger loss, a different objective. No choice of radius, held-out target, tuning factor or pseudocount enters the estimator. The target outcomes were already exposed, and fitting exclusion alone does not establish untouched confirmation.

This proof concerns a conditional point estimator for five listed source quantities. It supplies no stochastic likelihood, uncertainty distribution, calibrated chronology, taxonomy equivalence, physical transport, identifiable PPE/ERV parameter or environmental validity theorem.

Exact source authority: experiment protocol SHA256 `a1662a4d5327e13e1d59cc1492ebdfdfcaccb8ffa67558ed6bbf51b4539a34ea`; prediction source `16cf4a30e8702202c81f56d2cd543492ba05c0931412d74306e0893a14c82ec8`; native ledger `0fa469e4cf60708ee958edff9188393d90a0f21f7f8312c6e7be26bb98b962c9`. The [saved-result qualification](source-account.json) retains source and actual numerical authority separately.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named measured/mapped/published reference scope and unmatched temporal/taxon/observation/independence limits.

**Supported claim.** Under strictly positive five-quantity compositions and normalized positive training weights, the centered weighted least-squares log-compositional objective has the unique mean residual minimizer; closure removes its common raw offset.

**Unsupported claim.** This conditional point-estimator theorem supplies no stochastic likelihood, uncertainty coverage, physical transport, identifiable PPE/ERV, taxonomy equivalence or environmental validity.

**Actual verification performed.** Read and checked the displayed completed-squares identity, centering and closure-invariance argument against the retained experiment/source account. No fit, score or numerical oracle was rerun.

**Remaining input or review.** The proof assumes source positivity and normalized weights; finite numerical behavior has separate retained verification and real environmental interpretation still needs admitted targets and review.

**Cause category.** Conditional deterministic estimator theorem distinct from empirical and stochastic validity.

**Consequence.** Uniqueness in the centered gauge supports the implemented point calculation; the raw least-squares mean remains unique even though closed predictions discard a common offset.

**Precise next acceptance route.** Preserve the positive normalized-weight assumptions and separate squared-Hellinger held-out scores from the training log-residual objective; qualify a new target independently before ecological use.

**Negative or refused result.** The theorem does not erase the correction’s poorer held-out contrasts or turn exposed group-held-out outcomes into untouched confirmation.

**Matched denominator.** One five-axis point-estimator theorem for a fixed radius and held-out group, with eight remaining nominal training groups in this experiment; no additional observations, fits, uncertainty intervals or independent environmental checks.

- [Retained qualification evidence: docs/report/vegetation-reference/namibia-grouped-mapped-area/report.json](report.json) (SHA-256 `a19f533e08c589507698cc9bfa89d97f2ac210f5c85db6eed3f7967b32d2b499`).

- [Retained qualification evidence: docs/report/vegetation-reference/namibia-grouped-mapped-area/source-account.json](source-account.json) (SHA-256 `00c21f87b989dfce82e7a74fe7bb6fd89a4b7b3e52de072e83b0d224addab2b7`).

- [Canonical scientific account: reports/science/namibia-pollen-vegetation-paper.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/namibia-pollen-vegetation-paper.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
