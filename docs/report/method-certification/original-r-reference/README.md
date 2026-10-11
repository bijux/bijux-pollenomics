# Original R reference and current Python replay

The [reference bundle](reference-bundle/certificate.json) preserves the complete authenticated DISQOVER 0.9.14 numerical certificate produced on the original source commit `56997bbcfb5fcf7088035a16080b6a9416acc6e5`. Its 124 members include raw R vectors, executed scripts, shared inputs, manifests, dependency and runtime identities, command outcomes, and Python expectations explicitly distinguished from R outputs. The bundle is 1,536,418 bytes and its certificate SHA-256 is `881c1f65b62c890fbb583c499493c21318f21857960998ca662fbb1cf2b94ae3`.

The [current replay](report.json) evaluates the current Python implementation against those original R vectors. It first checks the pinned certificate, exact bundle inventory, source lock and actual original execution outcomes. It requires matching shared setup, R case expressions, case labels, modes and prospective tolerances. Decimal and hexadecimal literals compare by their exact binary64 values; strings and integer suffixes remain distinct. Every source-domain parameter and ring geometry remains matched.

## Results and scope

- 66 current cases considered: 48 evaluated, 48 passed, zero numerical failures, and 18 refused because the original bundle contains no R result for them.
- All 25 original core cases match, covering dispersal kernels, deterministic and supplied-draw REVEALS, analytical LOVE, optimized candidate replay, and objective intermediates. All 23 distinct source-domain/corrected-forward cases match. Source refusals remain distinct from corrected matrix behavior.
- Maximum absolute numerical difference: `3.197442310920451e-14`. Each case retains its original tolerance and any current exact-coordinate assertions. NaN and infinity positions cannot become zero or disappear.
- The current-source replay was refreshed after the LRA facade, configuration, and regional reconstruction inputs changed. It passed 48/48 cases with the same maximum difference; the report now hashes all 84 current inputs, including the fixed-site and joint-draw modules. The deterministic REVEALS cases `C0015`–`C0017`, supplied-draw REVEALS `C0018`, and analytical LOVE `C0023` all pass with their declared labels, modes, and tolerances.
- Four focused regression tests passed; strict mypy and Ruff check/format passed for both producer and tests.

The 18 absent results belong to three newer prospective optimized-LOVE fixtures, each with six intermediate, axis, wrapper and nonfinite/refusal checks. Their absence is specific to this historical certificate. Separate [current native R](../current-r-oracle/README.md) and [source-closed Linux R](../linux-r-oracle/README.md) runs executed all 43 core cases, including those 18, and all 23 source-domain cases with zero failures. Neither run changes the original certificate's 25-case denominator. Candidate replay establishes objective evaluation and selected-candidate parity, without an optimizer trajectory or global-convergence claim.

No fresh R execution occurred during this replay. The retained Linux R runtime and library remain local, while the Docker daemon was unavailable at inspection. This result is a current Python comparison to historical authenticated R outputs, not a current source-commit release certificate, independent vegetation validation, or complete publication replay. The original certificate continues to identify its original source commit and runtime.

## Reproduction

From the repository root, choose an absent output below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.lra_validation.reference_replay \
  --repository . \
  --bundle docs/report/method-certification/original-r-reference/reference-bundle \
  --output artifacts/jobs/retained-r-reference/reproduction
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/reference_replay.py) validates the original bundle before computation, records its current dependency hashes and installed numerical versions, and rechecks the hashes afterward. Failed numerical comparisons remain in the denominator. A changed source expression or altered reference certificate refuses reuse.

The bundled original DISQOVER source archive and its license remain governed by the [LRA NOTICE](../../../../packages/bijux-pollenomics-lra/NOTICE). Preserving this bounded certificate transfers numerical evidence out of disposable run directories; it does not copy the installed R runtime or library into the repository.
