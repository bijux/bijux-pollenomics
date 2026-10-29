# Circular receiver reference

This reference compares one independently declared numerical operator: an isotropic GPM displacement law averaged over a uniformly weighted circular receiver, with homogeneous emitting land in an exterior annulus. It is separate from the historical author lake algorithm. The three-case comparator below consumes controlled parameter tuples. The Nordic adapter described later uses saved conditional pooled counts.

Let the receiver radius be `R`, with `0 <= R <= inner < outer`. Distances are metres; fall and wind speeds are metres per second. With `p = gamma / 2`, `a = 4 * fall / (gamma * wind * sqrt(pi) * D)`, the displacement survival is `S(d) = exp(-a * d^p)`. The source's `D` uses its empirical metre-based GPM convention; it is not independently asserted to be an SI diffusivity. The factor is dimensionless.

For a displacement of length `d`, the fraction of receiver area within a target disk of radius `r` is its circle-intersection area `A(R, r, d) / (pi * R^2)`. Subtracting the inner disk from the outer disk and changing variable to `q = a * d^p` gives:

```text
K = integral exp(-q) * [A(R, outer, (q/a)^(1/p))
                       - A(R, inner, (q/a)^(1/p))] / (pi * R^2) dq
```

The displacement density becomes `exp(-q) dq` and integrates to one. The geometrical integrand is zero outside `inner-R <= d <= outer+R`. This is an independent one-dimensional integration order for the same bounded nonnegative indicator used by the maintained receiver/angular calculation. At `R=0`, bounded convergence gives the analytic point limit `S(inner)-S(outer)`; the implementation handles it directly.

The R reference splits at the four tangencies, uses absolute tolerance `1e-11`, relative tolerance `1e-10` and at most 1000 subdivisions per segment, and reports an omitted probability bound if its hazard integration is capped at 700. Its adaptive error estimates are nonrigorous. Partial circle intersections use normalized Heron factors, compensated radius differences and `atan2` segment areas to avoid cancellation near tangency and at extreme radius ratios. Thin-annulus subtraction and representability can still limit precision; raw factors and refusals are retained.

`test_receiver_overlap.R` checks 23 analytic geometry cases, including near-coincident circles, tangent limits, extreme radius ratios, scaling and symmetry, and retains an explicit overflow refusal. It takes three arguments: the current reference source, an earlier reference source for the well-conditioned comparisons, and an absent output directory under `artifacts/`. These controls complement the scalar laws and typed refusals in `test_receiver_reference.R`; they do not establish field accuracy.

The explicit Python comparator reads exactly three ordered R diagnostic rows: `inner_ring` (81–500 m), `outer_ring` (500–1000 m), and `combined_annulus` (81–1000 m). All use receiver 80 m, fall speed 0.03 m/s, wind speed 3 m/s, `D=0.12`, and `gamma=0.25`. It freshly calls the maintained `circular_receiver_annulus` for each tuple, with the maintained `1e-9`/`1e-8`/100 numerical settings. The absolute comparison tolerance is frozen at `1e-8`. Both numerical error estimates and the R raw factor/tail bound remain in the JSON; comparison tolerance is not an uncertainty interval.

## Explicit execution

Use an already qualified R installation with **base, stats and utils**. `utils` supplies `write.table`. No package installation, network, fit or optimizer is needed. Run both commands through the project's bounded numerical execution procedure; these examples do not enforce OS memory limits. Prepare only the parent directory, leaving the R output directory and comparison JSON absent.

```sh
mkdir -p artifacts/circular-receiver-reference
R_DEFAULT_PACKAGES=stats,utils R_LIBS_USER= R_LIBS_SITE= \
R_ENVIRON_USER=/dev/null R_PROFILE_USER=/dev/null \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 TZ=UTC LANG=C LC_ALL=C \
Rscript --vanilla \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/test_receiver_reference.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/receiver_reference.R \
  artifacts/circular-receiver-reference/r
```

Set `R_DIAGNOSTICS_SHA256` from the actual retained R product, `R_SOURCE_EPOCH` from that execution's source identity, and `PYTHON_SOURCE_EPOCH` from the qualified current source execution. Paths reject parent traversal and linked ancestors; the JSON must remain inside the explicit physical output root. Epochs are full lowercase Git identities; the comparator records them and the actual imported operator source hashes. The execution procedure must establish those identities; the CLI does not authenticate a checkout from a caller-supplied epoch alone.

```sh
PYTHONPATH=packages/bijux-pollenomics-lra/src \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 \
python packages/bijux-pollenomics-lra/tests/reference/circular_receiver/compare_reference.py \
  --diagnostics artifacts/circular-receiver-reference/r/numerical-diagnostics.tsv \
  --diagnostics-sha256 "$R_DIAGNOSTICS_SHA256" \
  --r-source-epoch "$R_SOURCE_EPOCH" \
  --python-source-epoch "$PYTHON_SOURCE_EPOCH" \
  --output-root artifacts/circular-receiver-reference \
  --output artifacts/circular-receiver-reference/comparison.json
```

Exit zero means all three comparisons meet the frozen absolute tolerance. A numerical mismatch writes all three comparisons and exits one. Malformed, nonfinite, incomplete or foreign diagnostics and implementation errors fail without being converted into successful or omitted cases. Ordinary pytest exercises the TSV reader and comparison plumbing with an explicitly supplied miniature evaluator; it never starts R or calls the real quadrature. Real R and fresh Python numerical evidence require the separate explicit commands.

Passing these controls establishes three same-formula scalar comparisons and the separately retained R mathematical/refusal controls. It does not establish original-author R parity, historical membership, publication-specific multisite/PFT results, covariance, calibrated field uncertainty, physical receiver radius, ecological transfer or measured vegetation accuracy.

## Nordic physical-window reference

`physical_windows.py` and `physical_windows.R` extend the declared circle-overlap operator to the saved Nordic conditional scenarios. The input is the existing [Nordic report](../../../../../docs/report/pollen-reconstruction/nordic-static-basin-scenarios/README.md), with nine static-basin cases, 23 distinct response tuples, 29 case/taxon uses, and 182 occupied windows. The adapter retains all 518 panel components and 1,762 covariance matrix positions. It exports pooled panel counts, PPE/SD, literal axes and physical parameters; the R process never reads the expected composition or covariance cells.

The R calculation differentiates the normalized estimator with respect to native counts. For `a_i = 1/(K_i PPE_i)`, `z = sum(a_i n_i)`, and `v_i = a_i n_i/z`, its count Jacobian is `D_ik = a_k (delta_ik - v_i)/z`. It propagates `diag(n) - n n^T/N`. The PPE Jacobian is `H_ik = -v_k (delta_ik - v_i)/PPE_k`, with the explicitly assumed diagonal covariance `diag(SD^2)`. Counting and PPE contributions are added; marginal SE is the square root of the diagonal. The R algebra controls include a hand-calculated two-taxon example, common scaling, count scaling, explicit zero counts and invalid-input refusals.

Each window is evaluated twice. The **saved-factor track** reuses the exact retained Python physical factors and compares 6,840 composition, direct fraction, SE and covariance cells at absolute-plus-relative tolerance `2e-12`. The **fresh-factor track** uses independently integrated R factors and compares the same 6,840 cells at absolute-plus-relative tolerance `1e-8`. Each of the 23 fresh physical factors is also compared at absolute tolerance `1e-8`. These thresholds are fixed in `physical-windows-protocol.json`; adaptive quadrature estimates are nonrigorous and comparison tolerances are not uncertainty intervals.

The explicit exporter and comparator accept authenticated source buffers, require the complete declared population, reject duplicate/missing/foreign or nonfinite cells, and record input/output hashes. The comparison writes numerical mismatches and exits one; malformed products refuse instead of disappearing from the population. Outputs must be absent and inside the explicit physical artifact root. Pytest covers controlled readers and handoffs without invoking R or quadrature.

To run the reference, use an already qualified Python and R runtime with base, stats and utils, one numerical thread, and bounded execution. Set `REPORT` to `docs/report/pollen-reconstruction/nordic-static-basin-scenarios/report.json` and `TUPLES` to its sibling `verification/physical-response-tuples.json`, with their actual SHA256 values. Set `EXECUTION_EPOCH` to the authenticated source checkout plus its separately recorded overlays. The commands below do not establish those identities or impose wall/RSS/storage limits themselves.

```sh
mkdir -p artifacts/nordic-physical-window-reference
python packages/bijux-pollenomics-lra/tests/reference/circular_receiver/physical_windows.py export \
  --report "$REPORT" --report-sha256 "$REPORT_SHA256" \
  --tuples "$TUPLES" --tuples-sha256 "$TUPLES_SHA256" \
  --execution-epoch "$EXECUTION_EPOCH" \
  --output-root artifacts/nordic-physical-window-reference \
  --output artifacts/nordic-physical-window-reference/inputs
R_DEFAULT_PACKAGES=stats,utils R_LIBS_USER= R_LIBS_SITE= \
R_ENVIRON_USER=/dev/null R_PROFILE_USER=/dev/null \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 TZ=UTC LANG=C LC_ALL=C \
Rscript --vanilla \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/physical_windows.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/receiver_reference.R \
  artifacts/nordic-physical-window-reference/inputs/tuples.tsv \
  artifacts/nordic-physical-window-reference/inputs/scenarios.tsv \
  artifacts/nordic-physical-window-reference/inputs/windows.tsv \
  artifacts/nordic-physical-window-reference/r
python packages/bijux-pollenomics-lra/tests/reference/circular_receiver/physical_windows.py compare \
  --report "$REPORT" --report-sha256 "$REPORT_SHA256" \
  --tuples "$TUPLES" --tuples-sha256 "$TUPLES_SHA256" \
  --execution-epoch "$EXECUTION_EPOCH" \
  --input-directory artifacts/nordic-physical-window-reference/inputs \
  --r-directory artifacts/nordic-physical-window-reference/r \
  --output-root artifacts/nordic-physical-window-reference \
  --output artifacts/nordic-physical-window-reference/comparison.json
```

The saved numerical report retains its original source epoch; a later R execution does not relabel that Python run. This comparison checks the declared marginal mathematics and numerical response for those saved conditional inputs. It does not recover historical LandClim membership or chronology, validate dated shorelines or parameter transfer, propagate joint cross-window uncertainty, establish empirical coverage or measured vegetation accuracy, or reproduce the original authors' R implementation. Unoccupied windows and missing age bounds remain outside this calculation.

## Swedish physical-window reference

`swedish_population.py`, `swedish_windows.py` and `swedish_windows.R` apply the same declared operator and marginal uncertainty equations to the saved Swedish conditional report. The complete population has four cores, 24 case/profile combinations, 462 windows and 45 distinct physical tuples. Its 385 full rows and 77 reduced zero-PPE control rows have different saved fields. Both the saved-factor and fresh-R-factor tracks compare only fields actually present: 16,868 saved-value comparisons in total. Another 2,572 R-only control cells are checked separately against baseline or exact-zero invariants; missing saved arrays are never filled in as observations.

Use `swedish_windows.py export` with the authenticated report and its source execution identity to prepare `tuples.tsv`, `scenarios.tsv`, `windows.tsv` and their manifest. Pass these three TSVs to `swedish_windows.R`, after its shared `physical_windows.R` source and the receiver reference. The R process receives counts, parameters and saved factors, without expected composition or covariance cells. Its two output files are `factors.tsv` and `values.tsv`.

The Python `compare` mode requires `--input-directory`, `--r-directory`, the report identity and an absent output inside `--output-root`. Bind the original export with `--input-export-manifest-sha256`, `--input-exporter-source`, `--input-exporter-source-sha256` and `--input-export-execution-epoch`. The exporter source is the exact retained source body that produced that manifest. `--execution-epoch` identifies the fresh R/comparison job separately; neither changing comparison code nor rerunning R relabels the original export or saved report. Use the same bounded runtime procedure as the Nordic reference, with separate owned output directories.

Physical factors use absolute tolerance `1e-8`; fresh-factor moments use absolute-plus-relative tolerance `1e-8`, and saved-factor moments use `2e-12`. Complete population, field membership, source identities and both tracks must pass. `test_swedish_windows.py` checks readers, mixed source epochs, numerical mismatches and malformed bindings without starting R or quadrature; `test_swedish_windows.R` checks the independent algebra. These checks establish conditional numerical parity, not historical LandClim reproduction, empirical uncertainty coverage or independent vegetation accuracy.

## Nordic conditional wind scalar reference

`nordic_wind.py` exports the 46 saved physical-response tuples from the conditional wind report and compares their factors with `nordic_wind.R`. The complete population comprises 18 case profiles and 58 case-to-tuple uses. This comparison uses the saved Python factors and does not rerun Python kernels or moments. The R driver uses the shared TSV parser in `physical_windows.R` and the independent operator in `receiver_reference.R`, with unchanged absolute/relative integration settings `1e-11`/`1e-10` and 1000 subdivisions. Scalar agreement uses the fixed absolute tolerance `1e-8`.

Use qualified Python and R runtimes, base/stats/utils, one numerical thread and the bounded execution procedure above. Set `REPOSITORY` to the physical repository root; set `WIND_REPORT` to the retained complete wind result and `WIND_PROTOCOL` to `docs/report/pollen-reconstruction/nordic-static-basin-scenarios/assumptions/transport-sensitivity.json`. Supply their authenticated SHA256 values and the separate current reference execution identity. Prepare only the parent artifact directory; leave both output directories and the comparison JSON absent. These commands do not establish source identities or enforce wall/RSS/storage limits themselves.

```sh
python packages/bijux-pollenomics-lra/tests/reference/circular_receiver/nordic_wind.py export \
  --repository "$REPOSITORY" --report "$WIND_REPORT" --report-sha256 "$WIND_REPORT_SHA256" \
  --protocol "$WIND_PROTOCOL" --protocol-sha256 "$WIND_PROTOCOL_SHA256" \
  --execution-epoch "$EXECUTION_EPOCH" --output-root "$REPOSITORY/artifacts/nordic-wind-reference" \
  --output "$REPOSITORY/artifacts/nordic-wind-reference/inputs"
R_DEFAULT_PACKAGES=stats,utils R_LIBS_USER= R_LIBS_SITE= \
R_ENVIRON_USER=/dev/null R_PROFILE_USER=/dev/null \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 TZ=UTC LANG=C LC_ALL=C \
Rscript --vanilla \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/nordic_wind.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/physical_windows.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/receiver_reference.R \
  "$REPOSITORY/artifacts/nordic-wind-reference/inputs/tuples.tsv" "$REPOSITORY/artifacts/nordic-wind-reference/r"
python packages/bijux-pollenomics-lra/tests/reference/circular_receiver/nordic_wind.py compare \
  --repository "$REPOSITORY" --report "$WIND_REPORT" --report-sha256 "$WIND_REPORT_SHA256" \
  --protocol "$WIND_PROTOCOL" --protocol-sha256 "$WIND_PROTOCOL_SHA256" \
  --execution-epoch "$EXECUTION_EPOCH" --output-root "$REPOSITORY/artifacts/nordic-wind-reference" \
  --input-directory "$REPOSITORY/artifacts/nordic-wind-reference/inputs" \
  --manifest-sha256 "$EXPORTED_MANIFEST_SHA256" --r-directory "$REPOSITORY/artifacts/nordic-wind-reference/r" \
  --output "$REPOSITORY/artifacts/nordic-wind-reference/comparison.json"
```

Set `EXPORTED_MANIFEST_SHA256` from the actual export. All adapter input and output paths must be normalized absolute paths without linked ancestors. Create the parent `$REPOSITORY/artifacts/nordic-wind-reference` before export. The exported manifest binds its exact exporter source bytes, so a retained export must be compared with those same bytes; renaming the source leaves that hash unchanged. A later canonical adoption does not relabel the earlier saved wind run or the artifact source used by its reference job. Keep the original saved, export and reference epochs distinct.

Complete agreement exits zero. Numerical mismatches, known typed R refusals and fatal/not-run dispositions retain all 46 rows and exit one; malformed or foreign handoffs refuse without a comparison output. `test_nordic_wind.py` runs complete artificial CLI and mixed-result/strict-reader controls without R or physical quadrature. Scalar numerical agreement does not establish original-author R parity, empirical wind support, chronology or physical uncertainty, field accuracy, historical reconstruction or complete scientific acceptance.

## Nordic regional cutoff reference

`regional_cutoff.py` uses the same explicit `export` and `compare` interface as the wind adapter for the saved conditional regional-extent result. It requires 46 distinct requests, 23 at each of 50 km and 200 km, with wind fixed at 3 m/s, `D=0.12` and `gamma=0.25`. Nine matched baseline cases contribute 58 case/taxon uses. The baseline extent is 100 km. These alternatives are numerical stress settings, not measured or source-supported bounds on regional pollen transport.

Supply the authenticated saved cutoff `analysis/report.json` and `docs/report/pollen-reconstruction/nordic-static-basin-scenarios/assumptions/regional-extent-sensitivity.json`. Use a fresh parent directory under `artifacts/`, and keep the original baseline, saved cutoff and current reference execution identities separate. Follow the wind export and comparison commands above with `regional_cutoff.py` and the cutoff input paths. The Python adapter authenticates its unchanged sibling `nordic_wind.py` before reusing its stateless input and path helpers; it retains separate cutoff population and case-binding predicates.

The R driver takes one additional source argument, the unchanged wind diagnostic adapter. Between export and comparison, use this argument order through the bounded execution procedure:

```sh
R_DEFAULT_PACKAGES=stats,utils R_LIBS_USER= R_LIBS_SITE= \
R_ENVIRON_USER=/dev/null R_PROFILE_USER=/dev/null \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 TZ=UTC LANG=C LC_ALL=C \
Rscript --vanilla \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/regional_cutoff.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/physical_windows.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/receiver_reference.R \
  packages/bijux-pollenomics-lra/tests/reference/circular_receiver/nordic_wind.R \
  "$EXPORTED_CUTOFF_TUPLES" "$ABSENT_CUTOFF_R_OUTPUT"
```

R receives only tuple identities and physical parameters. It uses the existing independent circle-overlap calculation and diagnostic helpers with the same `1e-11` absolute, `1e-10` relative and 1000-subdivision integration controls. The Python comparison retains all 46 outcomes at absolute tolerance `1e-8`; known refusals, fatal errors and subsequent unrun requests remain explicit and fail admission. Comparison tolerance is not an uncertainty interval.

`test_regional_cutoff.py` exercises the complete artificial handoff and malformed cutoff, case, epoch, helper, numeric and outcome cases without invoking R or physical quadrature. This scalar comparison does not recompute window moments or covariance, establish infinite-domain convergence, calibrate an empirical extent, recover historical author inputs or demonstrate field accuracy.
