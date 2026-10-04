# Native R reference and retained comparisons

The authenticated native macOS R 4.6.0 capture passed **43 core cases**, **23 source-domain cases** and **48 comparisons against the original R reference**. The capture identifies the executed Python source revision `064d1237fd743d957538fff2cbae74db06e17338`, the locked DISQOVER 0.9.14 source, the R runtime and the exact dependency versions. All 97 numeric CSV files matched the previously retained values byte for byte. The capture is a bounded numerical comparison, with no ecological accuracy or Linux release certification claim.

The native source packet at `data/method-certification/native-r/capture/capture.json` independently binds 138 raw members, the actual execution receipt, five locked public dependency archives and their acquisition metadata. Nine additional raw scripts and process logs remain in that packet. The core run report retains its actual elapsed time. These immutable records are preserved as source evidence; rebuilding a comparison does not execute R again or reproduce process timing.

The [comparison report](report.json) and [source account](source-replay.json) are derived from the native capture and the [original authenticated R bundle](../original-r-reference/reference-bundle/certificate.json). Their `native_capture_source_revision` identifies the actual native execution. The governed comparison identifies its consumer through deterministic code and data digests; the execution Git revision remains in the preserved run evidence. Both explicitly state that R and the captured 43 Python expectation vectors were not newly executed for this comparison. A changed protected scientific input refuses reuse of the capture and requires a new native execution decision.

The 18 prospective optimized LOVE cases have native R results in this capture. The original reference contains 25 core cases and 23 source-domain cases; it contains no R results for those 18 later cases. The separate [current Python account](../original-r-reference/report.json) compares current Python with the historical reference and must retain those missing historical results explicitly. Neither comparison establishes stochastic optimizer trajectory parity, a global optimum or uncertainty calibration.

## Recompute the retained comparison

From an installed development environment at the repository root, choose an absent destination below `artifacts/` whose parent is named `producer-output`:

```sh
mkdir -p artifacts/jobs/native-r-comparison/producer-output
python -m bijux_pollenomics_dev.source_completion.method_certification.native_r_comparison \
  --repository . \
  --output artifacts/jobs/native-r-comparison/producer-output/source-products
```

The mapped output contains only `report.json` and `source-replay.json`. Its sibling `native-comparison/` preserves the ordinary comparison output, including all 138 raw members and its actual execution revision. The command authenticates the native packet before and after, validates the original reference and checks the captured scientific source hashes against the physical repository. It never consumes the tracked comparison JSONs as producer input. The configured report owner runs the same producer in independent reference and replay lanes.

## Reproduction

A new native execution uses the maintained `bijux_pollenomics_dev.lra_validation.live_reference` producer, the locked R runtime, Fortran toolchain and dependency archives. The [source lock](../../../../configs/ci/lra-r-source-lock.v1.json) identifies the exact archive bytes. The public acquisition metadata at `data/method-certification/native-r/public-acquisition.json` records fresh public retrieval; the producer's existing cache-path label does not establish historical private archive provenance. Toolchain, source, environment and input custody must be qualified for each new execution before its results replace this capture.

A new run requires the qualified R, Rscript and Fortran executables. Set
`BIJUX_R`, `BIJUX_RSCRIPT` and `BIJUX_FORTRAN` to their physical executable
paths, then use an absent destination:

```sh
python -m bijux_pollenomics_dev.lra_validation.live_reference \
  --repository . \
  --output artifacts/jobs/native-r-reproduction \
  --r "$BIJUX_R" --rscript "$BIJUX_RSCRIPT" \
  --fortran "$BIJUX_FORTRAN" \
  --source-cache data/method-certification/native-r/source-archives
```

## Optimized LOVE objective and bounded search

The capture's 18 prospective optimized LOVE cases cover declared intermediates,
taxon and ring axes, supplied-candidate wrapper replay and refusal behavior.
They extend the original 25 core cases; they do not supply the missing 18
historical original-R results or pair stochastic optimizer search trajectories.
The maintained solver and optimized-profile checks remain available separately:

```sh
python -m pytest -q \
  -o cache_dir=artifacts/jobs/love-optimizer-acceptance/cache \
  --basetemp=artifacts/jobs/love-optimizer-acceptance/products \
  packages/bijux-pollenomics-lra/tests/unit/optimization/test_solver.py \
  packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_optimized_profile.py
```

## Scientific and release boundary

The [source replay verifier](verify_source_replay.py) checks the retained numeric identities and current declared source closure. This verifier and the retained comparison provide separate evidence from fresh native execution. Neither supplies the locked Linux release certificate, provider rights, independent vegetation observations or full scientific acceptance.
