# Joint conditional covariance of reused counts and shared PPE

This calculation propagates a fixed count model and shared parameter covariance through closed literal-panel compositions. It does not estimate chronology, geography, ecological transfer or empirical error coverage.

For result r, let the positive fixed factor be K_ri and shared positive PPE be p_i. With nonnegative observed counts n_i and positive panel total N, define a_ri = 1/(K_ri p_i), w_ri = a_ri n_i, W_r = sum_i w_ri, and c_ri = w_ri/W_r. The closure Jacobian is B_r = I − c_r 1ᵀ. Differentiation gives the count derivative J_r = B_r diag(a_r)/W_r and the PPE derivative H_r = −B_r diag(c_r/p). Parameter columns are embedded by their exact shared native row identity, including parameters absent from a particular panel.

One authenticated native collection-unit/dataset/chronology/window/count-support identity defines one latent count vector. Reusing those observations with alternative receiving geometries does not create another independent observation. Under the conditional fixed-N multinomial model, C_ng = N_g[diag(f_g) − f_g f_gᵀ], where f_g = n_g/N_g. Stack each result's count derivative into G_g at that group's columns. Let H stack the PPE derivatives. Then

`C_joint = sum_g G_g C_ng G_gᵀ + H C_P Hᵀ`.

This sum assumes zero count–PPE cross-covariance. Count-correlated or endogenous PPE requires the omitted cross terms. Distinct native units and nonoverlapping fixed-point windows are independent count groups only under the separately declared working assumptions. Native identifiers establish distinct supports, not empirical temporal or environmental independence. Overlapping observations and alternate same-unit chronology/dataset projections are refused because their count cross-covariance is not supplied. Within the Nordic profile, C_P is the diagonal of eight literal native parameter-row SD² values, shared across every applicable result; unknown PPE off-diagonal correlation is not estimated.

Each C_ng is positive semidefinite by the multinomial variance identity. If C_P is positive semidefinite, every linear image in the sum is positive semidefinite. Also 1ᵀB_r = 0, so the covariance annihilates each panel's closure direction. Singular tangent covariance is expected. For a same-count geometry difference, a selector A places +I at the first result and −I at the second. Its covariance A C_joint Aᵀ equals C_rr + C_tt − C_rt − C_tr and remains positive semidefinite. Identical geometries have zero contrast variance because both count and PPE errors are shared.

An independently expressed route uses the panel fractions directly. Its derivative L_r = B_r diag(a_r)/sum_i(a_ri f_i) equals N J_r, and C_fg = [diag(f_g) − f_g f_gᵀ]/N_g. Consequently L_r C_fg L_tᵀ = J_r C_ng J_tᵀ. The retained independent Decimal50 consumer uses this fraction route and quotient differentiation for PPE, rather than calling the producer's count derivative implementation.

These are first-order conditional delta covariances at the observed plug-in fractions. Positive semidefiniteness, closure and scalar parity do not establish a calibrated confidence interval, joint posterior, empirical coverage, independent vegetation accuracy or historical reconstruction. A zero boundary plug-in covariance is not proof of absence.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The declared first-order joint delta covariance carries reused native counts and shared PPE through closed panel compositions. Its multinomial/PSD/closure identities explain conditional cross-result covariance and same-count geometry contrast variance.

**Unsupported claim.** Empirical independence of distinct native IDs/windows, chronology or geography accuracy, calibrated confidence intervals, field PPE correlation, joint age posterior, measured vegetation accuracy or proof of absence from zero plug-in variance.

**Actual verification performed.** The maintained mathematical derivation was inspected against its explicit count/PPE Jacobians, shared-row embedding and fractional alternative. It describes the independently expressed Decimal 50 fraction route used by retained numerical qualification; this reader contributes no new observation or numerical model execution.

**Remaining input or review.** The model assumes independent declared count groups and zero count–PPE covariance. The Nordic profile supplies only diagonal covariance for 8 native PPE rows; off-diagonal field covariance, temporal/environmental dependence and overlapping or alternative-chronology count coupling are not supplied.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Reusing observations under another geometry must retain their shared errors. Singular closure-direction covariance is expected; adding independent marginal SEs or treating alternate chronology supports as independent would invent an unsupported joint model.

**Precise next acceptance route.** Bind authentic native count supports and an explicit joint covariance model, including overlap/chronology, count–PPE cross terms or field parameter dependence where relevant, before extending paired uncertainty. Test empirical coverage against an independent matched reference before interpreting conditional delta covariance as calibrated uncertainty.

**Negative or refused result.** Overlapping observations and alternate same-unit chronology/dataset projections are refused when their cross-count covariance is absent. Identical same-count geometries have zero contrast variance; boundary zero covariance is not biological absence.

**Matched denominator.** One latent count vector per authenticated native collection-unit/dataset/chronology/window/count-support identity, with its own fixed panel N. The Nordic parameter profile shares 8 exact native PPE row identities across applicable results. This method reader adds 0 independent samples, fits or source measurements.

- [Retained qualification evidence: docs/report/pollen-reconstruction/nordic-static-basin-scenarios/report.json](report.json) (SHA-256 `50d2e11aa053f22afe8aeb2b0867c2ee3c00340ad002a6ece71c36aafdbbedfe`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
