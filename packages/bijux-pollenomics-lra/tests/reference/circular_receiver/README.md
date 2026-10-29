# Circular receiver reference

This reference compares one independently declared numerical operator: an isotropic GPM displacement law averaged over a uniformly weighted circular receiver, with homogeneous emitting land in an exterior annulus. It is separate from the historical author lake algorithm. The three-case comparator below consumes controlled parameter tuples. The Nordic adapter described later uses saved conditional pooled counts.

Let the receiver radius be `R`, with `0 <= R <= inner < outer`. Distances are metres; fall and wind speeds are metres per second. With `p = gamma / 2`, `a = 4 * fall / (gamma * wind * sqrt(pi) * D)`, the displacement survival is `S(d) = exp(-a * d^p)`. The source's `D` uses its empirical metre-based GPM convention; it is not independently asserted to be an SI diffusivity. The factor is dimensionless.

For a displacement of length `d`, the fraction of receiver area within a target disk of radius `r` is its circle-intersection area `A(R, r, d) / (pi * R^2)`. Subtracting the inner disk from the outer disk and changing variable to `q = a * d^p` gives:

```text
K = integral exp(-q) * [A(R, outer, (q/a)^(1/p))
                       - A(R, inner, (q/a)^(1/p))] / (pi * R^2) dq
```

The displacement density becomes `exp(-q) dq` and integrates to one. The geometrical integrand is zero outside `inner-R <= d <= outer+R`. This is an independent one-dimensional integration order for the same bounded nonnegative indicator used by the maintained receiver/angular calculation. At `R=0`, bounded convergence gives the analytic point limit `S(inner)-S(outer)`; the implementation handles it directly.

The R reference splits at the four tangencies, uses absolute tolerance `1e-11`, relative tolerance `1e-10` and at most 1000 subdivisions per segment, and reports an omitted probability bound if its hazard integration is capped at 700. Its adaptive error estimates are nonrigorous. Circle-lens subtraction can lose precision for thin annuli or extreme scale ratios; raw factors and refusals are retained.

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
