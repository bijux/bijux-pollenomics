# Spatial-field forwarding between three physical places

The declared spatial IDW cover field produced all 18 held-place/window predictions and all 54 matched scores. Its equal-place MAE/TV was 0.204875686, compared with 0.205958107 for homogeneous centre-cover forwarding and 0.220493174 for direct pollen IDW. The spatial-versus-centre difference is **numerically unresolved** by the prespecified conservative step-bracket diagnostics. These are previously exposed development observations, not an independent vegetation benchmark or untouched confirmation.

[protocol.json](protocol.json) fixes the question, source identities, original sample IDs, geometry, three prediction families, metrics and resource budgets before execution. [result.json](result.json) exports the compact derived population, geometry and complete-family summaries. [scores.csv](scores.csv) retains every context/family identity, both predicted and observed fractions, both signed errors, all three scalar metrics and their numerical ranges. It contains 54 rows and no copied native count table. Full frozen predictions and the original terminal result remain in `artifacts/physical-core/spatial-field-forward/native-run/`.

The six native BP windows are [2700,3200), [3200,3700), [3700,4200), [4200,4700), [4700,5200), [5200,5700). Named source point ages remain fixed. AD 1950 is a declared reference interpretation; no CE conversion, chronology refit or age uncertainty was introduced. Every place is excluded from its own field construction, including all SOLSOE81 material from the SOLSOE83 physical place. Two other places supply each target's anchors. Prediction packets contain target geometry and sample identities without matching target counts; the producer closes `prediction-freeze.json` before the separate scorer opens it and receives the target observations. The score rows retain that prediction file's SHA-256.

| Core | Dataset / site / unit / chronology | Native / selected samples | Source panel N | Projected Betula/Ulmus N | Excluded source-panel N | All reported pollen NISP | Outside source axis N |
|---|---|---:|---:|---:|---:|---:|---:|
| BOKE | 54001 / 28872 / 39241 / 38422 | 52 / 20 | 5116 | 4385 | 731 | 18207 | 13091 |
| BUS | 53995 / 28869 / 39238 / 38418 | 69 / 21 | 1756 | 1756 | 0 | 22991 | 21235 |
| SOLSOE83 | 4446 / 3432 / 4304 / 25740 | 26 / 18 | 12367 | 4114 | 8253 | 19626 | 7259 |

All 147 native samples have an account: 59 belong to the frozen subset and 88 are outside the requested windows. No in-window sample was refused. The inherited completeness filters require BOKE's three-taxon, BUS's two-taxon and Solsø's six-taxon source panels before projection to Betula/Ulmus. This is not a claim to include every possible two-taxon-eligible sample. Original datum IDs explicitly pair Betula with 29 and Ulmus with 310; absence is never replaced by zero. Source-panel totals, projected totals and all reported pollen totals have distinct denominators.

The source-cover anchors use their **own** homogeneous receiver factors: `c_s = closure(n_s/(K_s*PPE))`. Interpreting these regional inversions as point anchors is an explicit two-stage hypothesis; it does not jointly fit a self-consistent landscape. The source fractions or source covers are interpolated with inverse squared Euclidean distance in each target's WGS84 azimuthal-equidistant metre frame. The spatial family integrates the same cover field over the land annulus and uniformly receiving disk; the centre-cover baseline forwards its centre value homogeneously. Direct pollen IDW uses the same anchors, windows and target observations.

Static circular radii 80, 69 and 89 m come from LandClimII workbook rows 977, 978 and 95 and its explicit metre definition. They are conditional geometry hypotheses. Native core GPS is null for all three units. BOKE and BUS use their native site Points; BUS's separate inventory point discrepancy remains unresolved. Solsø uses the saved qualified Nordic analysis centroid from planar longitude/latitude shoelace arithmetic, not a surveyed core position or a newly computed geodesic centroid. No historical shoreline or lake identity admission is asserted.

Literal public means/FSP are Betula 5.106 / 0.024 m/s and Ulmus 1.27 / 0.032 m/s. Wind 3 m/s, empirical GPM coefficient 0.12, turbulence parameter 0.25 and 100 km extent are fixed. There is no count/PPE/geometry/field uncertainty law, basin vegetation, anisotropy or separate regional background. Source transfer and two-component closure remain conditional assumptions.

| Family | Equal-place MAE = TV | Conditional numerical range | Hellinger | Conditional numerical range |
|---|---:|---:|---:|---:|
| Direct pollen IDW | 0.220493174 | point only | 0.193455357 | point only |
| Centre cover IDW + homogeneous forward | 0.205958107 | point only | 0.181866295 | point only |
| Spatial cover IDW + receiver integration | 0.204875686 | [0.202579820, 0.206656333] | 0.181110167 | [0.179262935, 0.182597856] |

Signed errors are prediction minus observation. MAE averages absolute errors over the two components; TV is half their sum and coincides here. Hellinger uses the maintained stable implementation. Each place averages its six windows equally, then the three places receive equal weight. All families and metrics remain reported; there was no score-based parameter or metric selection.

| Target | Direct MAE/TV | Centre MAE/TV | Spatial MAE/TV | Spatial numerical range |
|---|---:|---:|---:|---:|
| BOKE | 0.251166705 | 0.247605383 | 0.244295509 | [0.238551446, 0.248463109] |
| BUS | 0.253346274 | 0.253097684 | 0.253160184 | [0.252016940, 0.254334158] |
| SOLSOE83 | 0.156966544 | 0.117171252 | 0.117171366 | [0.117171073, 0.117171732] |

Direct-minus-spatial aggregate MAE/TV is 0.015617488 with diagnostic range [0.013836841, 0.017913354]; its Hellinger difference is 0.012345190 with range [0.010857501, 0.014192422]. Centre-minus-spatial MAE/TV is 0.001082421 with range [-0.000698226, 0.003378287]; Hellinger is 0.000756127 with range [-0.000731562, 0.002603359]. The latter comparisons remain unresolved. Direct-minus-centre differences are 0.014535068 MAE/TV and 0.011589063 Hellinger, conditional on fixed homogeneous factors. These descriptive numerical comparisons do not establish ecological accuracy.

Six count-free primary integrals used fixed absolute/relative settings 1e-9/1e-8. Six standalone homogeneous responses keep the baselines independent of new-method failure. Forty-eight unchanged homogeneous ring calls produce the independent eight-log-annulus step brackets. All geometries passed the frozen domain, partition and bracket checks. Maximum absolute partition residual was 2.273181642920008e-13; maximum weighted adaptive error estimate was 2.355850376029061e-10. The full coefficient brackets, widths and separate homogeneous/ring error estimates are exported in `result.json`.

The step brackets condition on computed homogeneous ring factors. Their widths do not certify the primary tolerance, and adaptive quadrature estimates are nonrigorous. Normalization can enlarge the set of physically compatible coefficients. Probability and score endpoints are conservative diagnostics, not ecological confidence limits or guaranteed true-integral bounds; endpoints need not be physically attainable. The same geometry is shared across six windows, so aggregate endpoints do not identify one jointly attaining model. Printed digits do not establish finer accuracy.

The sole native execution consumed commit `dbe099e7df3718098d0dc13b1412335d44702af5`. Owned tool session 33773 terminated with exit 0 in 4.918875041 s; producer time was 3.009508042 s and geometry time 2.431124708 s. macOS `/usr/bin/time -l` reported peak RSS 295665664 bytes. The two scientific outputs total 350969 bytes, within the 180 s overall / 120 s geometry / 768 MiB posthoc / 10 MB budgets. Exact command, one-thread environment, UTC boundaries and input identities are retained in `artifacts/physical-core/spatial-field-forward/native-execution/execution.json`; stdout and literal time/stderr accompany it.

The actual invocation used inline `signal.alarm(180)` and the committed module CLI but omitted explicit Python `-B` and the bytecode environment override. This execution deviation was disclosed during the run; no rerun was made. A timestamp audit identified exactly the new spatial `__main__` and `sources` bytecode files created within the run; only those two were removed. Preexisting spatial and engine caches were preserved. The audit/removal observations remain beside the execution account. Working-tree controlled checks and their corrected fixture/list-versus-tuple failures are separately retained; the native run had no scientific refusal and no model fit.

The separately committed independent checker at `7deffa682499d0763b5c06f66b7aac77c962266c` verified all 147 original samples, 59 selected samples, 18 contexts and 54 scores, including native IDs/panel denominators, disjoint folds, frozen prediction identities, all three prediction formulas, Hellinger and equal-place summaries. It used direct angular quadrature at 256/512 nodes, an ellipsoidal distance/azimuth reconstruction of the projection, and the unchanged homogeneous receiver primitive rather than the new angular reduction as its oracle. Scalar ledger/angular comparisons used absolute allowances of 2e-12 with `rel=0`; projected-vector comparison used 1e-5 m absolute plus 1e-12 relative. Maximum angular-resolution discrepancy was 3.3306690738754696e-16, estimated ring-mass error 3.22655967175272e-9 and independent coefficient bracket width 0.002801955587572096. These are separate numerical diagnostics, not verification of true accuracy to the primary tolerance. All three centre-versus-spatial pair/metric differences remain numerically unresolved. Owned session **91200** exited zero: **one test passed in 5.45 s**, **6.18 s** process wall time and **313,229,312 bytes** peak RSS, with no skips or model/producer rerun. Both saved scientific files and all original input identities remained unchanged. The command, compact numerical summary and stdout/stderr are retained in `artifacts/spatial-field-forward/independent-check/`, within the predeclared 180-second, 768-MiB posthoc and 1-MB verification-output bounds.

Its exact command was:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /usr/bin/time -l .venv/bin/python -B -m pytest -c configs/pytest.ini \
  packages/bijux-pollenomics-dev/tests/source_completion/pollen_reconstruction/spatial_field_forward/test_result.py::test_saved_spatial_study_matches_originals_and_independent_arithmetic \
  --basetemp=artifacts/spatial-field-forward/independent-check/pytest \
  --timeout=180 --maxfail=1 -s -q
```

Use a fresh basetemp for another invocation so completed-run evidence remains retained.

Count attribution is to Neotoma, the European Pollen Database and the original investigators: Marie-José Gaillard-Lemdahl (BOKE, [A5HN-WW50](https://doi.org/10.21233/A5HN-WW50), [0msh-1a51](https://doi.org/10.21233/0msh-1a51)); Joachim Regnéll (BUS, [PQFT-GY26](https://doi.org/10.21233/PQFT-GY26), [mhqn-eq25](https://doi.org/10.21233/mhqn-eq25)); Bent V. Odgaard (Solsø, [mtmk-d772](https://doi.org/10.21233/mtmk-d772)). All native DOI strings and retained publication metadata remain in the terminal native result. Current Neotoma/EPD CC BY 4.0 policy evidence is bound in the protocol. Public parameters/site metadata are attributed to [LandClimII PANGAEA.937075](https://doi.org/10.1594/PANGAEA.937075), CC BY 4.0. Reusing the old normalized count bodies does not recover their original HTTP wire custody or establish current provider-value parity. No private author count table was consumed or redistributed.


## Finer conditional radial envelope

The original eight-ring point comparison above remains unchanged and numerically unresolved in its original context. A separate [fixed refinement protocol](radial-envelope/protocol.json) asks how a finer partition and complementary anchor factors bound the same exposed comparison. It adds no fit, inversion, new point prediction, parameter search, count input or age input.

Each original ring is split into sixteen logarithmic subrings, preserving every old boundary: 128 rings for each of six taxon/place geometries, or 768 homogeneous ring calls. Each returned positive binary64 mass is treated as an exact conditional constant. The new total is their exact rational sum, `K_refined`; it is not substituted for an old total in an old result. An exact circle-mean identity and its fixed-sign radial derivative give monotone endpoint bounds. Integer-square-root inequalities on a fixed 96-bit lattice enclose angular values. Positive ring masses then bound the first anchor coefficient, with the second exactly complementary to `K_refined`. Sign-aware affine deposition and positive two-component closure give prediction ranges.

All eighteen count-free ranges were saved and closed before the old scored observations were parsed. Scoring retains both finite observed components without forcing their sum to one. MAE/TV bounds use the absolute-error minimizer interval; Hellinger uses its constrained stationary point and constructive square-root difference intervals. Every original family/context remains present, with six windows per place and equal weights across three places. Old baseline scores are fixed finite references; their exact means are kept distinct from old printed aggregate rounding. Interval endpoints across contexts need not be jointly attainable.

| Quantity | Refined conditional range, approximately |
| --- | ---: |
| Spatial equal-place MAE / TV | [0.204811632, 0.204937641] |
| Spatial equal-place Hellinger | [0.181063648, 0.181155224] |
| Centre minus spatial MAE / TV | [0.001020466, 0.001146475] |
| Centre minus spatial Hellinger | [0.000711071, 0.000802647] |

These displayed decimals are rounded illustrations; the saved rational endpoints carry the certificates. All three family pairs are separated for all three metrics **only within this new conditional finite-mass context**. Spatial forwarding remains poorer than centre forwarding at BUS: MAE/TV [0.253148169, 0.253172351] versus 0.253097684. It is also slightly poorer at SOLSOE83: [0.117171357832, 0.117171373525] versus 0.117171252466. BOKE supplies the aggregate improvement: [0.244115368, 0.244469197] versus 0.247605383. There is no universal place-level improvement or measured vegetation validation.

All 768 calls returned positive finite masses without refusal. All eighteen old point vectors pass componentwise membership, all old spatial scalar scores lie in the new ranges, and all six geometry/taxon mass diagnostics pass. The largest absolute difference across refined-versus-old standalone, primary homogeneous and primary partition totals is about 3.550e-13. Maximum first-coefficient width is 0.000171683 (BOKE/Betula), versus the earlier diagnostic width 0.002801956. The largest sum of adaptive ring error estimates is 1.556e-9. Those error estimates remain nonrigorous: the exact certificates concern the finite returned masses, not true physical integrals, quadrature accuracy or historical basin geometry. Componentwise membership does not prove joint feasibility of an exactly closed old vector or of its old coefficient pair.

The producer (`9d7f47065`) and independent checker (`aec105a2d`) were committed before actual execution; both actual jobs consumed frozen HEAD `aec105a2dae494c3abd09dc2df12300aee1706e2`. The producer ran once, session 99069 / terminal cc573b, exit zero in 10.11 s, peak RSS 140,607,488 bytes. Its closed `prediction-ranges.json` and `result.json` total 533,256 bytes under `artifacts/physical-core/spatial-field-forward/radial-envelope/native-run/`. Exact command, one-thread environment, input identities and terminal facts are adjacent under `radial-envelope/native-execution/`. Result SHA-256 is `2ceed22d2e30fe32e20fff76982e81ea01c2606c5a6185d6f7b2b98e129f3807`.

The independent original-algebra/rational observer read those closed outputs once without repeating ring integration. Terminal a94c12 exited zero in 0.395 s with 53,788,672 bytes RSS; its 797-byte check and execution facts remain under `artifacts/wetland-source-review/radial-envelope/`. It verifies every ring outcome, angular certificate, complementary coefficient, affine/closure calculation, eighteen held-place contexts, all fifty-four scores and complete summaries. Independent literal-circle Gauss–Legendre orders 256/512 give maximum angular correspondence gap 2.220e-16 and resolution gap 3.331e-16; geodesic/projection correspondence differs by at most 3.420e-9 m. Both actual jobs fit the 180 s, 768 MiB posthoc and 5 MB budgets, with unchanged consumed inputs and HEAD/index. Unconsumed register-retirement edits existed separately; no whole-worktree-clean execution is claimed. Twenty-nine producer controls and seventy-one independent synthetic controls passed, with configured lint and strict types. Initial fixture/import/typing corrections remain recorded with their controlled attempts; neither actual scientific job required a retry.

This resolves a conditional finite-mass numerical separation question. It does not convert the original unresolved diagnostic into a true-integral certificate, prove ecological ordering, supply independent measurements, or close the broader physical reconstruction and qualified-review outcomes.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Matched whole-place-excluded forward predictions of a two-anchor cover field against direct-pollen IDW and homogeneous centre-cover forwarding, with frozen prediction bytes, all family metrics and conservative numerical-resolution accounting.

**Unsupported claim.** Measured or jointly fitted vegetation field, genuine untouched confirmation, resolved superiority of spatial over centre forwarding, rigorous true-integral bounds, jointly attaining aggregate endpoints, qualified historical basin/core geometry or field accuracy.

**Actual verification performed.** Producer dbe099e7d saved predictions before scoring all 18 contexts/54 outcomes and met resource bounds. Independent checker 7deffa682 compared all 147 original samples, 59 selected samples, exact source IDs/denominators, folds, prediction identities, all formulas and scores. Direct 256/512-node angular quadrature and independent ellipsoidal projection checks passed; maximum angular-resolution discrepancy was 3.3306690738754696e-16 and bracket width 0.002801955587572096. The checker exited zero in 6.18 s. The disclosed missing-bytecode-flag deviation was retained without a model rerun.

**Remaining input or review.** Three exposed physical places and six fixed windows support a declared two-anchor spatial hypothesis, not measured vegetation or untouched validation. Static radii, BUS coordinate ambiguity, inherited panel completeness and two-stage anchor inversion remain assumptions; step brackets condition on computed ring factors and do not resolve the centre-versus-spatial score differences. Resolver: Analyst for a predeclared numerical/spatial model question; source and vegetation-reference experts only for historical geometry, ecological accuracy or an admitted field interpretation. Reopen when: A finer numerical claim requires prespecified independent integration/refinement, while historical/field accuracy requires exact core/geometry support and an independent measured target. Do not select parameters or source masks from current target scores.

**Cause category.** assumption|algorithm/numerical|comparability

**Consequence.** Retain the full matched development comparison and numerical ranges; keep per-context and aggregate endpoints conservative and the common geometry dependence explicit.

**Precise next acceptance route.** Read all current families/metrics on their fixed support. Any next integration-resolution or empirical prediction question must declare its protocol and independent input before scores; do not erase unresolved comparisons or interpret static source geometry as historical basin acceptance.

**Negative or refused result.** No context/family was dropped or refused; all 54 scores remain. Every aggregate centre-versus-spatial metric comparison is numerically unresolved under the conditional brackets. No response rescaling, point correction, target-score tuning or ecological winner was adopted.

**Matched denominator.** Three physical places BOKE/BUS/SOLSOE83; 147 native accounts, 59 selected and 88 outside six frozen windows. Inherited source panels of three/two/six taxa are projected to literal Betula/Ulmus on the same 18 target contexts, producing 54 outcomes across three families.

Retained evidence: [reports/science/pollen-reconstruction/spatial-field-forward/result.json](result.json), [reports/science/pollen-reconstruction/spatial-field-forward/scores.csv](scores.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
