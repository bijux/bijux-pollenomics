# ABBO conditional age, counting and shared-PPE moments

Two separately named count profiles use the same 32,000 qualified saved joint age rows. The original **`neotoma_explicit_five_taxon`** profile defines all four windows on 29,332 rows (91.6625%). The later local noncommercial **`pangaea_recorded_zeros_local_nc`** profile uses independently qualified original recorded zeros and defines 31,999 rows (99.996875%). **Both primary unconditional 20-component means/covariances remain refused**: the strict native profile has 2,668 undefined rows, and the source-supported profile retains one empty-window row. Each conditional result must retain its own population label and denominator.

This is a new propagation of shared age membership and shared PPE moments, not another chronology fit. The earlier [fixed-age PPE study](../abborrtjarnen-ppe-dependence/README.md), original failed 8,000-state chronology experiment and separate [fixed-length chronology qualification](../../chronology/abborrtjarnen-bacon/README.md) remain unchanged. This calculation does not establish field calibration, historical reproduction, whole-vegetation composition or original core admission.

The original strict native [protocol.json](protocol.json) was committed before that calculation. Its unchanged [result.json](result.json) exports the complete conditional means, six 20×20 covariance components, all 30 contrasts, support census, chain summaries and actual qualification. [components.csv](components.csv) contains the 20 mean/spread/variance rows; [contrasts.csv](contrasts.csv) contains every older-minus-younger contrast. Both CSVs explicitly carry the conditioning event and 32,000/29,332 denominators. No native count matrix or age matrix is copied into these exports. The complete 32,000-row strict native ledger remains in repository artifacts. The separately named source-supported result below does not replace these files.

## Strict native source support and the defined event

The physical source is Neotoma dataset 19913, site 13338, collection unit 14910, ABBO. All 107 original samples were joined to the exact saved chronology sample/depth axis. The current native representation has 99 complete literal five-taxon panels and eight with absent native measurements:

| Native sample | Missing native datum |
|---:|---|
| 173221 | Poaceae |
| 173225 | Juniperus communis |
| 173226 | Cyperaceae |
| 173251 | Juniperus communis |
| 173269 | Juniperus communis |
| 173277 | Juniperus communis |
| 173278 | Juniperus communis |
| 173279 | Cyperaceae |

In the strict native profile, the window population includes **every native member**, rather than silently selecting those 99 complete samples. A single member lacking a required taxon refuses that draw/bin. Measured zero remains valid; absence is not filled with zero. Known reported panel subtotals remain distinct from undefined complete panel masses. The ledger retains actual sample IDs, missing ID/taxon mappings, reported and omitted pollen NISP, each bin's status, every seed/native-row identity and per-bin cover where defined, even when the complete four-window event fails.

| Window | Half-open calibrated BP interval | Defined rows | Refused rows and reason |
|---:|---|---:|---|
| 3 | [1500, 2000) | 32000 | 0 |
| 4 | [2000, 2500) | 31999 | 1 empty native window |
| 5 | [2500, 3000) | 32000 | 0 |
| 9 | [4500, 5000) | 29333 | 2667 with a missing five-taxon member |

There were no nonempty zero-panel-mass bins. The one incomplete case from the earlier closed 16-label score consumer remains refused, and the five-taxon measurement requirement adds 2,667 missing-member cases. Thus that earlier consumer's 31,999 complete rows could not establish the five-taxon mask. All 32,000 rows remain in the probability denominator. The strict native defined event C_native means that all four windows are nonempty, have complete measured panels for every member and have positive pooled panel mass. This event is determined before hypothetical counting/PPE errors; conditioning on it changes the age-mixture population and is not an unconditional posterior result.

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

Population means/covariances divide by M_C, not M_C − 1: M_C_native = 29,332 for the strict native case, and M_C_source = 31,999 for the separately reported source-supported case. The mean is the saved-age mixture of plug-in inverse covers; no second-order correction for nonlinear count/PPE errors is implied. The PPE component is further decomposed into `E[G] Σ E[G]^T` and the age/PPE interaction, their difference from `E[G Σ G^T]`. Taking only the mean gradient would omit that interaction. No old per-age sharp correlation extrema are averaged into a claimed globally attainable bound.

## Strict native conditional results

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

## Strict native actual execution and independent observation

The producer code was committed at `09bc85194`; the actual run consumed HEAD `5c2a6306cfcfc3bf494a7a2b6e8bbdf4c1e32dd4`, including the committed independent observer. Owned session 78256 terminated with exit 0 in 8.829082167 s; producer time was 7.485233791 s, peak macOS RSS 143982592 bytes. The 2,961,320-byte ledger and 145,136-byte result total 3,106,456 bytes, within 180 s / 768 MiB posthoc / 20 MB. Exact command, explicit Python `-B`, bytecode suppression, one-thread environment, UTC bounds and input identities are retained in `artifacts/physical-core/abborrtjarnen-age-ppe/native-execution/execution.json`. Eight unrelated PDF export paths were dirty at launch; consumed scientific code and inputs were committed and frozen. No globally clean-worktree claim is made.

The native result SHA-256 is `fcb09d193986febb0a19140af7b443bd87879e0cb8083438bf254903c1097eac`; ledger SHA-256 is `c25fc35cdd416458c8332d30104159fa4d6211e85a161d96a428a6cdec0dc067`. Both files remain unchanged under `artifacts/physical-core/abborrtjarnen-age-ppe/native-run/`.

The separate committed independent observer (session 5933) terminated with exit 0 in 22.494802542 s, peak RSS 58900480 bytes, within its 120 s / 512 MiB / 1 MB bounds. It independently reconstructed all 107 source samples, all 32,000 memberships/ledger rows, 2,400 covariance entries and 30 contrasts with scalar derivatives and an independent interaction accumulator. Maximum ledger-cover gap was 1.1102230246251565e−16 and maximum moment gap 1.181693631835401e−14, within the frozen 1e−12 absolute tolerance. Its actual result and exact command are at `artifacts/method-certification/abborrtjarnen-age-ppe/independent-check.json` and adjacent `execution.json`. Fourteen producer controls and 22 observer controls, configured Ruff and strict mypy passed before the actual runs. No model fit, source acquisition or consumer rerun was performed.

Chronology authority retains the original report's literal `diagnostics_passed=false` / `diagnostics_pass=true` writer conflict and the independent qualification that explicitly checked it. The raw chronological report and earlier failed strict observer remain unchanged. The chronology remains conditional on its controls, artificial surface and broad bottom likelihood, priors, zero reservoir assumption, fixed calibration treatment and saved precision; successful sampler diagnostics are not chronology accuracy or field calibration.

Count attribution is to Neotoma, EPD and Thomas Giesecke, dataset [10.21233/2vzb-bg61](https://doi.org/10.21233/2vzb-bg61), with current CC BY 4.0 source evidence. Parameters are the literal public [LandClimII PANGAEA.937075](https://doi.org/10.1594/PANGAEA.937075) values and [Githumbi et al. 2022](https://doi.org/10.5194/essd-14-1581-2022) uncertainty context. LegacyAge controls/metadata retain their CC BY 4.0 attribution. For the strict native run above, the separate [PANGAEA.738429](https://doi.org/10.1594/PANGAEA.738429) CC BY-NC 3.0 file supplied only the previously qualified descriptive 3 ha area fact; that run did not parse or redistribute its measurement table. The later source-supported profile below additionally uses eight qualified original recorded zeros under its separate local noncommercial scope. Static geometry, taxon/PPE transfer, transport, aquatic/marginal pollen contributions, overdispersion, site selection and field accuracy remain outside this conditional calculation.


## Source-supported original recorded-zero profile

The [source-supported protocol](source-supported-counts/protocol.json) defines
`pangaea_recorded_zeros_local_nc` separately from the unchanged strict native
protocol and outputs above. The [original-count source account](../../abborrtjarnen-source-method.md)
qualified an exact 107-to-107 depth correspondence across 535 five-taxon slots:
all **527 reported native counts match**, and all **eight absent native cells
are literal original recorded zeros**, with no blank or invalid cells. Five
concern Juniperus-type, two Cyperaceae and one Gramineae/Poaceae. This is source
measurement support, not a general missing-to-zero rule or evidence of
biological absence.

Only those eight qualified original zeros enter a separate analytical panel.
Every native omission remains explicit in the sample accounts and ledger; all
527 reported integers, native reported subtotals and omitted pollen NISP are
unchanged. Full source correspondence, independently verified raw ownership,
exact source-data digests and the exact missing-slot set are required before
that panel is available. All 107 samples have five-axis analytical source
support, but empty and nonempty zero-mass windows still refuse. No original
matrix or eight-row source-candidate dump is added to Git.

The analytical use of Giesecke's original EPD/PANGAEA counts is **local
noncommercial research under CC BY-NC 3.0**, distinct from the Neotoma CC BY 4.0
release. Attribution remains to Thomas Giesecke, EPD and PANGAEA. Original
Juniperus-type, Pinus diploxylon-type and Gramineae comments remain distinct
from the native/public parameter labels; literal taxon/PPE transfer is still
the declared assumption. Exact scaled depths and count agreement qualify
exported-series correspondence, not independent measurements, unrecorded
native depth units, species equivalence, a historical core selection or field
admission. The original source-method account owns these source limits.

### Changed complete-event population

| Population | Strict native C_native | Source-supported C_source |
| --- | ---: | ---: |
| Saved joint age rows, all-draw denominator | 32,000 | 32,000 |
| Complete four-window rows | 29,332 | 31,999 |
| Complete probability | 0.916625 | 0.99996875 |
| Undefined rows | 2,668 | 1 |
| Primary unconditional 20-component moments | Refused | Refused |

All **2,667** newly complete rows change only the window-9 missing-panel status
to defined. Windows 3 and 5 remain defined on all 32,000 rows; window 4 remains
empty on one row; window 9 is now defined on all 32,000. The full seed/native-row
comparison records 29,332 common-complete rows, 2,667 native-undefined to
source-complete rows, one common-undefined row and **zero lost native-complete
rows**. The remaining empty-window row is not dropped or repaired. Each chain
still has 16,000 saved rows; their source-complete counts are 16,000 and 15,999.

The age rows, four bins, geometry, PPE values and shared diagonal covariance,
conditional pooled-window multinomial law and first-order total-covariance
calculation are unchanged. The producer reproduces the old mean, all six
covariance components, gradients, spreads and all 30 contrasts on exactly the
29,332 common native-complete rows with **maximum gap 0.0**. The different
source-complete conditioning population accounts for the reported comparison;
it is not a changed measurement or stochastic law within C_native.

The largest absolute conditional mean change is **Betula/window 9**:
0.40887104876414226 on C_native versus 0.409853930446087 on C_source, a difference
of **0.000982881681944714 cover fraction** (about 0.09829 percentage points).
Its conditional standard deviation is 0.029044716405780293 versus
0.02855345276531486. These are different conditional mixtures, not an estimate
of field accuracy or a calibrated gain in ecological precision. The local
result retains every 20-component mean, all six 20×20 matrices, all 30 contrasts
and their profile differences, rather than only this largest change.

### Actual source-supported execution and check

The producer was committed at `14a5c0fcf`; its single actual run consumed
**`3c89475195629a8afb7c1cc79752d84aee6d6e3c`**. Owned session **80087** terminated
with exit **0** in **13.247065916 s**; producer time was 11.921294958 s and peak
macOS RSS was **149,307,392 bytes**. The 3,111,265-byte ledger and 261,785-byte
result total **3,373,050 bytes**, within 180 s / 768 MiB posthoc / 20 MB. Exact
argv, six one-thread/bytecode environment overrides, Python `-B`, the 180-second
signal alarm, UTC bounds, source/input identities and owned tool handles are in
`artifacts/physical-core/abborrtjarnen-age-ppe/source-supported-counts/native-execution/execution.json`.
The existing module CLI selected `--count-profile pangaea_recorded_zeros_local_nc`
with repository `/Users/bijan/bijux/bijux-pollenomics`, shared source root
`/Users/bijan/bijux/-bijux-pollenomics-data` and its fresh `native-run` destination.
There was no fit, new age/PPE draw, geometry integration or repeated producer.

Full outputs remain local under
`artifacts/physical-core/abborrtjarnen-age-ppe/source-supported-counts/native-run/`:
`result.json` SHA-256 is
`4ff4fb0978144c6e86671bd8a6cc4219f1f28ff8124cc60f6c1a95e268c8fc62`;
`draw-ledger.csv.gz` SHA-256 is
`8f97e8f74072bfcf25bef117f35850cdc4e51b70e1dbbced02179eced8b50f9c`.
Neither full source-supported output is committed or substitutes the original
strict native exports. Both were fixed before independent observation.

The first independent check, owned terminal chunk **48d95e**, exited **1** in
0.401641708 s **before ledger traversal**, with `KeyError: 'draw_ledger'`. It
expected a native result locator in the governed strict-result wrapper, whose
actual ledger locator is under `scientific_outputs`. The failed command,
traceback and resource facts remain in
`artifacts/raa-reconciliation/abborrtjarnen-age-ppe/source-supported-counts/`.
Only the maintained wrapper-shape/pin adapter and its controls were corrected;
producer output, sources, model, settings and tolerance were unchanged.

The corrected observer at
**`4bc6ab0f211c179aa332dc848f954c6773aeae00`**, session **36453**, then exited **0**
in **44.215523333 s**, peak RSS **66,519,040 bytes**, producing a 1,054-byte check
within 120 s / 512 MiB / 1 MB. Its independently reconstructed source check
covers all 107 owners, 535 slots, 527 shared counts, eight original zeros and
32,000 joint-age identities. Scalar derivatives and independent moment
accumulators check 2,400 covariance entries, all 30 contrasts, and every
old/new support transition. Maximum source-moment gap is
**1.2989609388114332e−14**; common-native moment gap
**1.181693631835401e−14**; profile-difference gap
**3.122502256758253e−16**; ledger-cover gap **1.1102230246251565e−16**.
All meet the unchanged 1e−12 absolute tolerance; common-ledger cover gap is 0.0.

Its exact existing-module `--result`/`--output` invocation, Python `-B`,
120-second alarm, one-thread settings, source commits and terminal handles are
in `artifacts/raa-reconciliation/abborrtjarnen-age-ppe/source-supported-counts/governed-reference-check/execution.json`,
with `independent-check.json`, stdout and stderr alongside. Thirty-six producer
controls passed with configured Ruff/strict typing. Independent controls passed
across scoped checks: 44 earlier controls, including the 22 unchanged strict
controls, plus six wrapper-shape/pin controls; the affected 15 moment/binding
controls were rerun after the correction and passed in 1.60 s. This does not
claim a fresh 50-test aggregate after repair. The original failed checker and
all strict-profile scientific outputs remain unchanged.

The source-supported result resolves these eight native-panel omissions for
this explicitly named analytical use. One undefined row still prevents the
unconditional quantity. Age-model dependence, static geometry, taxon/PPE
transfer, source morphology, pooled-count assumptions and lack of independent
field calibration remain. No canonical observation, selected chronology,
scientific core/species/PPE approval or field admission has changed.


## One PPE covariance shared across the saved age mixture

The separate [common-covariance protocol](common-covariance/protocol.json)
asks how unknown PPE correlation changes uncertainty when **one covariance
matrix is shared across every age state and window**. It uses only the qualified
source-supported result, saved cover ledger and independent check above. The
conditioning event remains C_source with 31,999 complete rows and one undefined
row among all 32,000 saved identities. Conditional means, age variances and
counting variances stay fixed. There is no new count-table or age-array read,
fit, random draw or physical integration.

For each of the 20 components and 30 older-minus-younger contrasts, the producer
forms `Q = D E_C[g(A) g(A)^T] D` on the four positive-PPE-SD parameter axes.
Here D contains their reported SDs, and a contrast's gradient is differenced
**before** forming its outer product. PPE variance is `trace(Q R)`, where one
correlation matrix R satisfies `R positive semidefinite, diag(R) = 1` across
all saved states. Taking the outer product of the mean gradient omits age/PPE
interaction. Averaging separately optimized per-age extrema permits a different
R at each age and answers another question: gradients (1,1) and (1,−1) in two
equally weighted ages give variance exactly 2 for every common R, although
averaged per-age extrema span 0–4. Poaceae's reference-parameter SD of zero
removes its parameter axis; it does not remove Poaceae output uncertainty from
the compositional closure.

The prospective calculation retained the identity matrix, eight rank-one sign
Grams and eight fixed SLSQP starts for each endpoint, without random starts or
outcome-driven tuning. Solver outputs are candidates. Exact rational unit-Gram
witnesses supply attainable inner values; diagonal duals checked through all
15 exact principal minors supply outer bounds. The frozen padding sequence
and Gershgorin fallback preserve loose certificates rather than forcing a
success. Certificates apply to the **saved finite binary64 Q interpreted
exactly**, not an ideal unrounded source integral. Ledger-to-Q correspondence
is checked numerically and separately. No clipping, symmetrization, eigenvalue
repair or tolerance-based PSD certificate is used.

All **50 scalars / 100 endpoints** have `tight_global_enclosure`: each endpoint's
certified gap divided by trace(Q) is at most the predeclared 1e−6. The largest
is exactly **1/4194304 ≈ 2.38419e−7**; 81 endpoint gaps are exactly zero and
19 are positive. All 800 optimizer attempts succeeded and remain recorded;
their success alone supplies no global certificate. Every saved Q also passes
its own 15 exact principal-minor checks. The diagonal correspondence gap is
at most **2.4716421400880484e−18**, below the frozen 1e−12 absolute bound.

The table gives illustrative **total conditional SD displays**, after adding
the separately retained age and counting terms to the PPE-variance endpoints.
All 50 component/contrast results remain in the local numerical output.

| Quantity | Shared diagonal PPE baseline | Common-correlation outer SD display |
| --- | ---: | ---: |
| Pinus sylvestris, window 4 | 0.01772510875 | 0.00929343266–0.02469231106 |
| Cyperaceae, window 9 minus window 3 | 0.01512764520 | 0.01485581411–0.01552336720 |
| Poaceae, window 9 | 0.00595415724 | 0.00589988673–0.00601484530 |

Pinus/window 4 has the largest relative component sensitivity: about −47.57%
to +39.31% versus its diagonal baseline. Cyperaceae/9−3 has the largest relative
contrast sensitivity: about −1.80% to +2.62%. These are parameter-dependence
sensitivities under the same conditional working law. The square roots are
explicitly **approximate numerical displays**, not directed rigorous intervals,
confidence intervals or field coverage. Signed exact total-variance bounds and
square-root domain/refusal states are preserved. All 50 actual displays have
`approximate_square_root_enclosure`; no negative lower-bound domain refusal
occurred. A different R may attain each scalar extremum: the result does not
claim one covariance jointly attains all 50 extrema or adopt a PPE distribution.

The producer was committed at `539da7a13`; the actual producer and independent
observer both consumed **`19feb79bf25917431abfd05b9b5f6b474f358a81`** with
HEAD, index and consumed inputs fixed until observation terminated. Producer
session **89250** exited zero in **4.584395375 s** (producer 3.192316334 s),
with peak macOS RSS **150,650,880 bytes**, within 180 s / 768 MiB posthoc /
10 MB. Its **1,210,684-byte** result is at
`artifacts/physical-core/abborrtjarnen-age-ppe/common-covariance/native-run/result.json`,
SHA-256 `b4e91111c603f46afc54325f1f0122d671b7877f1fa768e1a6e5185c11a82d62`.
Exact argv, Python `-B`, bytecode suppression, five one-thread backend overrides,
input pins, UTC bounds and tool handles are in the adjacent
`native-execution/execution.json`. The module command is
`python -B -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence --repository . --output <fresh-native-run>`;
the retained actual command additionally installs the 180-second signal alarm.

Independent session **69905** exited zero in **1.70 s** (observer
1.476662042 s), RSS **264,077,312 bytes**, within 180 s / 512 MiB posthoc /
5 MB. It reconstructed Q through a separate vector formulation, checked all
32,000 identities and 31,999 complete rows, all 100 exact certificates and
**1,500 dual principal minors**, without repeating candidate optimization.
Maximum independent Q difference was **2.710505431213761e−19**, within the
frozen abs1e−18 + relative1e−11 criterion. Its command, environment and result
are under `artifacts/method-certification/abborrtjarnen-age-ppe/common-covariance/`;
`independent-check.json` is 1,119 bytes, SHA-256
`073f9d80e7718723c8e33c671ceb1471165c37c45373412dd8cba621f1d08760`.
The CLI is
`python -B -m tests.source_completion.pollen_reconstruction.test_abborrtjarnen_age_ppe_dependence_result --repository . --result <native-result> --output <fresh-check>`.
Before actual execution, 31 author controls and 40 independent controls passed,
including analytical shared-age counterexamples, exact rank-two certificates,
solver failures, retained loose bounds and signed square-root domains;
configured Ruff and strict mypy passed for both changed source sets.

Full numerical outputs remain local noncommercial derivatives under the
original count source's CC BY-NC 3.0 scope. This sensitivity does not change
either earlier profile, remove the remaining undefined state, establish Monte
Carlo precision of derived means, validate taxonomy/geometry/chronology or
supply measured vegetation, historical reproduction or original core admission.


## Simulation precision of conditional mean estimates

The separate [Monte Carlo protocol](monte-carlo/protocol.json) addresses a
different uncertainty from the mixture SDs above. The finite saved-ledger means
are exactly defined empirical summaries, subject to ordinary numerical error.
Under an invariant sampler target π, the same saved ratios estimate
`mu_pi = E_pi[I_C c] / P_pi(C)`. The following MCSEs estimate simulation error
relative to that conditional target, under the declared mixing/CLT and ratio
delta-method assumptions. They are not uncertainty about the definition of the
finite empirical average, field error or another age/count/PPE mixture spread.

Each original 16,000-state chain is partitioned into **125 contiguous batches
of 128 saved states**, with native rows 3502–19501 and seed order preserved.
This fixed choice is near the square root of the chain length; it is not an
optimal or empirically selected batch size. The method uses nonoverlapping
batch means as described by [Flegal and Jones (2010), section 3, equation 6](https://arxiv.org/pdf/0811.1729),
with the ratio and independent-chain pooling algebra declared in the protocol.
Batch length and number would both need to grow for an asymptotic consistency
argument; this one finite partition cannot establish adequate mixing.

For every original state, `U = (I_C, I_C c)` retains the complete-event indicator
and 20 numerators. The undefined state has a zero **numerator**, never an
observed zero cover. The joint batch covariance and ratio Jacobian retain the
random denominator and cross-window dependence. Pooling weights use the original
chain lengths, and pooled influences are centered separately within each chain.
All 30 contrasts are differenced before the producer's squared batch products;
their uncertainty is not the sum of independent component variances. There is
no complete-case reindexing, tail removal, thinning, extra burn-in, batch search,
fit, new draw or raw count/age-array read.

All 20 component and 30 contrast records are retained for each chain, the pool
and the seed-271828-minus-314159 difference: **200 scalar records** and four
20×20 MC covariance matrices. The empirical means reproduce the earlier
qualified summaries with maximum absolute gap **2.8976820942716586e−14**,
below the fixed 1e−12 bound. No scalar has zero estimated batch variance.

| Pooled quantity | Empirical mean | Estimated MCSE | Earlier total mixture SD |
| --- | ---: | ---: | ---: |
| Betula, window 9 | 0.40985393045 | 0.00031754800 | 0.02855345277 |
| Betula, window 9 minus window 5 | 0.04570857882 | 0.00037228466 | 0.02738855924 |

Pooled component MCSEs range from 0.0000100046 to 0.000317548; contrast MCSEs
range from 0.0000148823 to 0.000372285, all in cover fractions. Across the 50
pooled quantities, MCSE divided by the earlier diagonal-law total mixture SD
ranges from about **0.00358529 to 0.0135927**. These descriptive ratios compare
different uncertainty quantities; they are not a new acceptance threshold.

The largest absolute retained chain discrepancy is **Pinus/window 5 minus
window 3**: seed 271828 minus 314159 is **+0.001247081210472123**, with estimated
independent-chain difference MCSE **0.0004900842126172119**. No significance
test, interval or new convergence gate is applied. The pooled estimate and its
within-chain MCSE can miss between-mode nonconvergence or initialization bias.
The result does not certify that all derived means agree or have converged.

Chain 314159 has an empirically constant complete indicator, p=1 and estimated
indicator MCSE=0, explicitly labeled insufficient observed transitions. Chain
271828 has p=0.9999375 and estimated MCSE=0.0000625; the pool has p=0.99996875
and estimated MCSE=0.00003125. Those p values are observed finite frequencies.
**One undefined state cannot establish rare-refusal mixing or precision.**
The earlier unconditional-moment refusals remain. MCSE interpretation assumes
positive target P(C), applicable CLT/delta regularity and independent chains
with the same invariant target; bounded covers and earlier Coda diagnostics
do not prove those conditions.

Producer `42ff45df7` and independent observer `cc9bf8482` were committed before
the single actual calculation at **`cc9bf84824c52c59f3541a9be03c8d523af0354f`**.
HEAD/index/consumed sources and three qualified inputs stayed fixed until both
terminated. Producer session **86603** exited zero in **2.10 s** (internal
0.802726542 s), peak macOS RSS **156,844,032 bytes**; its 168,228-byte result
has SHA-256 `ec9198c80fc8c6c83dc07d3320033ab7ced7ccfc395211eadc0c8a923f9cf167`.
It remains local under
`artifacts/physical-core/abborrtjarnen-age-ppe/monte-carlo/native-run/`.
The module is
`bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_monte_carlo`,
with `--repository . --output <fresh-native-run>`. Exact argv, input pins,
Python `-B`, bytecode suppression, five one-thread backend settings, 120-second
alarm and tool/resource facts are in adjacent `native-execution/execution.json`.

Independent session **64001** exited zero in **2.403730459 s** (verifier
2.221993125 s), peak RSS **255,115,264 bytes**. Its separate masked residual
formulation checks all 32,000 identities, 31,999 complete rows, 250 native
batches, 1,600 covariance cells and 200 scalar records, without producer imports.
Maximum independent covariance/variance gap is **1.3976043629695956e−20**,
within the frozen abs1e−18 + relative1e−10 criterion. The command
`python -B -m tests.source_completion.pollen_reconstruction.test_abborrtjarnen_monte_carlo_result --repository . --result <native-result> --output <fresh-check>`
and execution facts are under
`artifacts/method-certification/abborrtjarnen-age-ppe/monte-carlo/`.
Its 984-byte check has SHA-256
`e67696e5ba329d9198d8f0d411e9e778a36668c72b67b2de9730acb7ef954a71`.
Both runs met 120 s / 512 MiB posthoc / 5 MB bounds. Before execution,
35 author and 29 independent controls, configured Ruff and strict mypy passed,
including exact masked-ratio arithmetic, unequal complete weights, correlated
contrast cancellation, native ordering and signed/nonfinite/domain refusals.

Full numerical outputs retain the existing local noncommercial source scope.
The original failed chronology experiment, raw chronology flag conflict and
qualified longer chains remain unchanged. This finite diagnostic supplies no
model retuning, calibrated coverage, chronology accuracy or field admission.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** First-order total-covariance propagation on explicit complete-event populations, including shared age/count/PPE interaction and all 30 contrasts. Separate source-supported recorded zeros expand the defined population while reproducing all native-complete estimates unchanged. A separate saved-age calculation certifies finite-Q variance extrema over one common PPE correlation matrix for all age states, on the same source-supported population. A separately declared fixed-batch ratio diagnostic estimates Monte Carlo error relative to conditional invariant-target means, preserving native order, the undefined indicator state, per-chain discrepancies and all 200 scalar records.

**Unsupported claim.** Unconditional 20-component moments across undefined rows, 32,000 independent observations, certified Monte Carlo precision or error in an exactly defined finite-ledger mean, nonlinear full-PPE posterior or calibrated interval coverage, whole vegetation, corrected chronology or original core admission. No single covariance jointly attains all scalar extrema; approximate square-root displays are not rigorous directed intervals or field coverage.

**Actual verification performed.** Strict producer/observer qualification is retained. Source-supported producer at 3c8947519 and corrected independent observer at 4bc6ab0f2 both exited zero. The observer checked all 107 owners, 535 source slots, 527 reported count pairs, eight recorded zeros, 32,000 saved identities, support transitions, 2,400 covariance cells and 30 contrasts. Common-native, source and difference gaps are 1.1817e-14, 1.2990e-14 and 3.1225e-16 under 1e-12 absolute tolerance. Producer 36 controls and independent 44 earlier plus six wrapper controls passed across affected selections; no fresh aggregate, age fit or PPE draw is claimed. Common-covariance producer and independent observer at 19feb79bf both exited zero: 50 scalars, 100 exact endpoint certificates, 1500 dual principal minors and all 32000 saved identities. Maximum independent Q gap 2.7105e-19; largest normalized certified gap exactly 1/4194304, below the frozen 1e-6 criterion. All 800 candidate attempts are retained. Thirty-one author and forty independent controls, configured Ruff and strict mypy pass. Actual producer 4.5844 s/RSS150650880 B; observer 1.70 s/RSS264077312 B. Mean-precision producer and independent observer at cc9bf8482 both exited zero within 120 s/512 MiB/5 MB: all 32000 identities, 250 contiguous native batches, 1600 MC covariance cells and 200 scalar records. Independent residual covariance/variance gap is 1.3976e-20 under abs1e-18 plus relative1e-10; qualified empirical-mean gap 2.8977e-14 under 1e-12. Thirty-five author and twenty-nine independent controls plus configured lint/types pass; no fit or new draw.

**Remaining input or review.** Strict native counts leave 2,668 undefined age rows; independently qualified original recorded zeros support a separately named local profile with one undefined empty-window row. Both unconditional quantities remain refused. Conditional moments retain declared age, pooled-count, shared diagonal-PPE, static physical and taxon-transfer assumptions without field calibration. Resolver: Analyst preserving each named source/conditioning population; source and field expertise for any broader taxon, physical-support or accuracy claim. Reopen when: A different unconditional quantity requires a declared estimand and genuinely defined support; a different uncertainty or field claim needs its own source/evidence protocol without relabelling either existing result.

**Cause category.** data|assumption|comparability

**Consequence.** Keep undefined probability mass and conditional-on-complete labels on every scientific summary; retain all covariance components and contrasts without promoting successful arithmetic to scientific or field admission.

**Precise next acceptance route.** Read each named conditional result under its own source rights, count support and conditioning event. Preserve both refused unconditional quantities and the original strict exports. Any different estimand or field interpretation needs its own defined support and evidence; do not silently change masks, bins, taxon transfer or stochastic laws.

**Negative or refused result.** Strict unconditional moments remain null for 2,668 rows; the separate source-supported profile remains null for one empty bin-4 row. The failed first observer stopped before ledger traversal on its wrapper-shape assumption and is preserved; only its adapter/controls changed. No missing-value rule, row drop, clipped covariance, replacement chronology or field significance was adopted. The common-covariance study retains signed bounds and predeclared loose/solver/domain refusal behavior; all actual 100 endpoints are tight, with 81 zero gaps and 19 positive gaps. It does not remove the undefined source-supported age row. Largest retained chain difference is Pinus/window 5 minus 3: +0.00124708121 with estimated difference MCSE0.00049008421; no derived convergence or agreement is certified. One empirically constant indicator chain and one observed refusal cannot establish rare-event mixing or true zero uncertainty.

**Matched denominator.** All 107 native samples, 99 native-complete panels and eight native omissions; the separate original-source profile has 107 analytically supported panels. Both retain two chains of 16,000 states and all 32,000 probability-denominator rows. C_native has 29,332 rows; C_source has 31,999: 2,667 newly complete, one jointly undefined, zero lost native-complete. Each conditional population retains all 20 components, six covariance matrices and 30 contrasts. Common-covariance sensitivity uses the same C_source, 20 components and 30 contrasts, with one parameter covariance shared across states; it introduces no new observation or draw. The mean-precision diagnostic retains two ordered 16000-state chains, each with 125 batches of 128 states, and 50 scalar records per chain, pooled and chain-difference group (200 total). These are dependent simulation states, not independent field observations.

Retained evidence: [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/result.json](result.json), [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/components.csv](components.csv), [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/contrasts.csv](contrasts.csv), [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/source-supported-counts/protocol.json](source-supported-counts/protocol.json), [reports/science/abborrtjarnen-source-method.md](../../abborrtjarnen-source-method.md), [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/common-covariance/protocol.json](common-covariance/protocol.json), [reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/monte-carlo/protocol.json](monte-carlo/protocol.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
