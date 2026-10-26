# ABBO conditional age, counting and shared-PPE moments

All 32,000 qualified saved joint age rows were consumed once. **2,668 rows (8.3375%) do not define all four five-taxon windows**, so the primary unconditional 20-component mean/covariance is refused. The separately named conditional-on-complete result uses 29,332 rows (91.6625%). Its conditioning cannot be removed when interpreting the estimates.

This is a new propagation of shared age membership and shared PPE moments, not another chronology fit. The earlier [fixed-age PPE study](../abborrtjarnen-ppe-dependence/README.md), original failed 8,000-state chronology experiment and separate [fixed-length chronology qualification](../../chronology/abborrtjarnen-bacon/README.md) remain unchanged. This calculation does not establish field calibration, historical reproduction, whole-vegetation composition or original core admission.

[protocol.json](protocol.json) was committed before the calculation. [result.json](result.json) exports the complete conditional means, six 20×20 covariance components, all 30 contrasts, support census, chain summaries and actual qualification. [components.csv](components.csv) contains the 20 mean/spread/variance rows; [contrasts.csv](contrasts.csv) contains every older-minus-younger contrast. Both CSVs explicitly carry the conditioning event and 32,000/29,332 denominators. No native count matrix or age matrix is copied into these exports. The complete 32,000-row ledger remains in repository artifacts.

## Source support and the defined event

The physical source is Neotoma dataset 19913, site 13338, collection unit 14910, ABBO. All 107 original samples were joined to the exact saved chronology sample/depth axis. The source has 99 complete literal five-taxon panels and eight with absent measurements:

| Native sample | Missing source taxon |
|---:|---|
| 173221 | Poaceae |
| 173225 | Juniperus communis |
| 173226 | Cyperaceae |
| 173251 | Juniperus communis |
| 173269 | Juniperus communis |
| 173277 | Juniperus communis |
| 173278 | Juniperus communis |
| 173279 | Cyperaceae |

The window population includes **every native member**, rather than silently selecting those 99 complete samples. A single member lacking a required taxon refuses that draw/bin. Measured zero remains valid; absence is not filled with zero. Known reported panel subtotals remain distinct from undefined complete panel masses. The ledger retains actual sample IDs, missing ID/taxon mappings, reported and omitted pollen NISP, each bin's status, every seed/native-row identity and per-bin cover where defined, even when the complete four-window event fails.

| Window | Half-open calibrated BP interval | Defined rows | Refused rows and reason |
|---:|---|---:|---|
| 3 | [1500, 2000) | 32000 | 0 |
| 4 | [2000, 2500) | 31999 | 1 empty native window |
| 5 | [2500, 3000) | 32000 | 0 |
| 9 | [4500, 5000) | 29333 | 2667 with a missing five-taxon member |

There were no nonempty zero-panel-mass bins. The one incomplete case from the earlier closed 16-label score consumer remains refused, and the five-taxon measurement requirement adds 2,667 missing-member cases. Thus that earlier consumer's 31,999 complete rows could not establish the five-taxon mask. All 32,000 rows remain in the probability denominator. The defined event C means that all four windows are nonempty, have complete measured panels for every member and have positive pooled panel mass. C is determined before hypothetical counting/PPE errors; conditioning on C changes the age-mixture population and is not an unconditional posterior result.

The two saved chains each contribute 16,000 rows, retaining original one-based native rows 3502–19501 and all 107 joint sample ages. Original 4,000-row prefixes occur once within each longer chain; failed 8,000-state outputs were not appended. Negative ages remain signed and outside positive study windows. Native point chronology 11516 is the fixed-age reference, while the mixture uses the separately declared Bacon model.

## Conditional working law

The literal native/public axis remains Betula (29), Cyperaceae (74), Juniperus communis (4416), Pinus sylvestris (1287), Poaceae (417). The same static 3 ha circular receiver, saved five response factors, 100 km extent, wind 3 m/s, empirical coefficient 0.12 and turbulence parameter 0.25 are fixed. No new physical integration, shoreline qualification or geometry uncertainty law is introduced. The original source-point case reproduces all four prior physical covers, counting covariances and PPE gradients with maximum absolute gap **0.0**.

For a joint age row A, the complete windows pool their explicit integer counts and use the existing inverse `c(A) = closure(n(A)/(K * PPE))`. Counting error has the same pooled-window fixed-total multinomial working law **conditional on A**, at the observed pooled plug-in composition. The working law declares independent conditional counting errors for windows with disjoint native sample memberships; disjointness alone does not establish independence of biological sources. This is not one age-independent raw-aliquot counting law or evidence of environmental/temporal independence.

One shared five-dimensional PPE perturbation is independent of A, and count/PPE errors are independent given A. Its baseline covariance Σ is the diagonal of the published SD squared, shared across all four windows. Source labels transfer literally; no PPE distribution shape or new PPE draw is invented. The original SD/SEM wording discrepancy remains recorded, with no square-root-of-sample-size conversion. Poaceae PPE 1 / SD 0 defines the relative reference, not zero field uncertainty.

With stacked 20×5 PPE gradient G(A), the first-order total covariance on C is

```text
Cov(Y | C) = Cov_C[c(A)]
           + E_C[C_count(A)]
           + E_C[G(A) Σ G(A)^T].
```

Population means/covariances divide by M_C = 29,332, not M_C − 1. The mean is the saved-age mixture of plug-in inverse covers; no second-order correction for nonlinear count/PPE errors is implied. The PPE component is further decomposed into `E[G] Σ E[G]^T` and the age/PPE interaction, their difference from `E[G Σ G^T]`. Taking only the mean gradient would omit that interaction. No old per-age sharp correlation extrema are averaged into a claimed globally attainable bound.

## Conditional results

Each table cell is conditional mean **(conditional standard deviation)** on the five-taxon closure. Fractions are not percentages or a complete terrestrial denominator.

| Taxon | Window 3 | Window 4 | Window 5 | Window 9 |
|---|---:|---:|---:|---:|
| Betula | 0.299424 (0.020682) | 0.388820 (0.019455) | 0.364286 (0.021010) | 0.408871 (0.029045) |
| Cyperaceae | 0.080781 (0.014203) | 0.059840 (0.008612) | 0.040870 (0.006566) | 0.026845 (0.006617) |
| Juniperus communis | 0.025990 (0.004047) | 0.017708 (0.002414) | 0.016664 (0.002343) | 0.008825 (0.002049) |
| Pinus sylvestris | 0.537539 (0.021815) | 0.493929 (0.017729) | 0.543689 (0.021459) | 0.529944 (0.027136) |
| Poaceae | 0.056266 (0.009409) | 0.039704 (0.006945) | 0.034490 (0.005514) | 0.025516 (0.005897) |

For the previously reported Betula window 3→9 example, the conditional mean contrast is 0.109446570 and its standard deviation is 0.028408661. Variance separates into age 0.000699428230, counting 0.0000986794895 and shared PPE 0.00000894432288, totalling 0.000807052043. These components concern the new conditional age population; they are not a calibrated change probability or a claim that the source native chronology was corrected.

Interaction size depends on the contrast. For Juniperus window 4→5, the shared-PPE variance is 7.817749925e−9: the mean-gradient term is 3.199850476e−9 and the interaction is 4.617899449e−9, about 59.07% of that PPE component. Its **total** variance is 1.163518701e−5, so that percentage must not be described as 59.07% of total uncertainty. All 30 contrasts and all six covariance components are retained, without selecting a favourable subset.

Seed 314159 has 14,695 complete rows; seed 271828 has 14,637. Their conditional means are exported separately. Subtracting the first array from the second gives the reported seed-271828-minus-314159 difference; the maximum absolute difference is 0.0007375372 in Betula/window 9. The complete-probability difference is −0.003625. Per-chain bin-status counts follow by grouping the ledger by seed and bin. These are descriptive checks of the saved populations, not a new convergence threshold or a Monte Carlo standard-error estimate. The rows remain autocorrelated MCMC states, and qualification of the original age/free-parameter diagnostics does not by itself establish convergence of every derived moment.

Covariances and contrast variance components remain raw, including signed numerical residuals. Only square roots use roundoff-only `max(0, variance)` after the frozen −1e−12 refusal criterion. Covers, contrasts and covariance matrices are not clipped or renormalized to remove numerical failures. Reported spreads are standard deviations of the conditional first-order mixture, **not standard errors of its mean**, normal intervals or coverage statements.

## Actual execution and independent observation

The producer code was committed at `09bc85194`; the actual run consumed HEAD `5c2a6306cfcfc3bf494a7a2b6e8bbdf4c1e32dd4`, including the committed independent observer. Owned session 78256 terminated with exit 0 in 8.829082167 s; producer time was 7.485233791 s, peak macOS RSS 143982592 bytes. The 2,961,320-byte ledger and 145,136-byte result total 3,106,456 bytes, within 180 s / 768 MiB posthoc / 20 MB. Exact command, explicit Python `-B`, bytecode suppression, one-thread environment, UTC bounds and input identities are retained in `artifacts/physical-core/abborrtjarnen-age-ppe/native-execution/execution.json`. Eight unrelated PDF export paths were dirty at launch; consumed scientific code and inputs were committed and frozen. No globally clean-worktree claim is made.

The native result SHA-256 is `fcb09d193986febb0a19140af7b443bd87879e0cb8083438bf254903c1097eac`; ledger SHA-256 is `c25fc35cdd416458c8332d30104159fa4d6211e85a161d96a428a6cdec0dc067`. Both files remain unchanged under `artifacts/physical-core/abborrtjarnen-age-ppe/native-run/`.

The separate committed independent observer (session 5933) terminated with exit 0 in 22.494802542 s, peak RSS 58900480 bytes, within its 120 s / 512 MiB / 1 MB bounds. It independently reconstructed all 107 source samples, all 32,000 memberships/ledger rows, 2,400 covariance entries and 30 contrasts with scalar derivatives and an independent interaction accumulator. Maximum ledger-cover gap was 1.1102230246251565e−16 and maximum moment gap 1.181693631835401e−14, within the frozen 1e−12 absolute tolerance. Its actual result and exact command are at `artifacts/method-certification/abborrtjarnen-age-ppe/independent-check.json` and adjacent `execution.json`. Fourteen producer controls and 22 observer controls, configured Ruff and strict mypy passed before the actual runs. No model fit, source acquisition or consumer rerun was performed.

Chronology authority retains the original report's literal `diagnostics_passed=false` / `diagnostics_pass=true` writer conflict and the independent qualification that explicitly checked it. The raw chronological report and earlier failed strict observer remain unchanged. The chronology remains conditional on its controls, artificial surface and broad bottom likelihood, priors, zero reservoir assumption, fixed calibration treatment and saved precision; successful sampler diagnostics are not chronology accuracy or field calibration.

Count attribution is to Neotoma, EPD and Thomas Giesecke, dataset [10.21233/2vzb-bg61](https://doi.org/10.21233/2vzb-bg61), with current CC BY 4.0 source evidence. Parameters are the literal public [LandClimII PANGAEA.937075](https://doi.org/10.1594/PANGAEA.937075) values and [Githumbi et al. 2022](https://doi.org/10.5194/essd-14-1581-2022) uncertainty context. LegacyAge controls/metadata retain their CC BY 4.0 attribution. The separate [PANGAEA.738429](https://doi.org/10.1594/PANGAEA.738429) CC BY-NC 3.0 file supplies only the previously qualified descriptive 3 ha area fact; its measurement table is not parsed or redistributed here. Static geometry, taxon/PPE transfer, transport, aquatic/marginal pollen contributions, overdispersion, site selection and field accuracy remain outside this conditional calculation.
