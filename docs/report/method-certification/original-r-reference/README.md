# Original R reference and current Python replay

The [reference bundle](reference-bundle/certificate.json) preserves the complete authenticated DISQOVER 0.9.14 numerical certificate produced on the original source commit `56997bbcfb5fcf7088035a16080b6a9416acc6e5`. Its 124 members include raw R vectors, executed scripts, shared inputs, manifests, dependency and runtime identities, command outcomes, and Python expectations explicitly distinguished from R outputs. The bundle is 1,536,418 bytes and its certificate SHA-256 is `881c1f65b62c890fbb583c499493c21318f21857960998ca662fbb1cf2b94ae3`.

The [current replay](report.json) evaluates the current Python implementation against those original R vectors. It first checks the pinned certificate, exact bundle inventory, source lock and actual original execution outcomes. It requires matching shared setup, R case expressions, case labels, modes and prospective tolerances. Decimal and hexadecimal literals compare by their exact binary64 values; strings and integer suffixes remain distinct. Every source-domain parameter and ring geometry remains matched.

## Results and scope

- 66 current cases considered: 48 evaluated, 48 passed, zero numerical failures, and 18 refused because the original bundle contains no R result for them.
- All 25 original core cases match, covering dispersal kernels, deterministic and supplied-draw REVEALS, analytical LOVE, optimized candidate replay, and objective intermediates. All 23 distinct source-domain/corrected-forward cases match. Source refusals remain distinct from corrected matrix behavior.
- Maximum absolute numerical difference: `3.197442310920451e-14`. Each case retains its original tolerance and any current exact-coordinate assertions. NaN and infinity positions cannot become zero or disappear.
- The current-source replay passed 48/48 cases with the same maximum difference and hashes all 85 current inputs, including the fixed-site and joint-draw modules. Nine previously recorded code inputs changed and one new native-parity module entered the source set; the numerical case outcomes remained identical. The deterministic REVEALS cases `C0015`–`C0017`, supplied-draw REVEALS `C0018`, and analytical LOVE `C0023` all pass with their declared labels, modes, and tolerances.
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

The bundled original DISQOVER source archive and its license remain governed by the [LRA NOTICE](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-lra/NOTICE). Preserving this bounded certificate transfers numerical evidence out of disposable run directories; it does not copy the installed R runtime or library into the repository.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** The original certificate supplies a 124-member immutable historical reference bundle and supports 48 evaluated retained R comparisons, distinct from 18 cases with no historical R values.

**Unsupported claim.** A historical certificate cannot certify all later source inputs, extend its case population or establish scientific source validity, ecological accuracy or a current hosted release certificate.

**Actual verification performed.** Reviewed the retained report, original certificate identity and attempted/evaluated/refused case partition; bound exact public account bytes. This qualification generated no R output, Python expectation or new reference certificate.

**Remaining input or review.** Later source correspondence requires named current-source consumers and actual case scope. Missing historical 18-case outputs remain missing rather than being reconstructed from later software and relabeled original.

**Cause category.** Historical immutable reference correspondence with explicit incomplete case support.

**Consequence.** The 48 evaluated comparisons can be cited within their tolerance and nonfinite contracts; attempted 66 does not mean 66 reproduced historical cases.

**Precise next acceptance route.** Preserve the original bundle unchanged, replay its retained comparison against exact current dependencies when required, and report later native-R extensions separately before hosted publication admission.

**Negative or refused result.** 18 attempted cases remain refused for absent historical R values; zero failures among 48 evaluated cases does not close those 18 or prove ecological validity.

**Matched denominator.** 124 original members/1,536,418 bytes;66 attempted,48 evaluated and passed, zero failed,18 refused; evaluated scope is 25 core plus 23 domain cases.

- [Retained qualification evidence: docs/report/method-certification/original-r-reference/report.json](report.json) (SHA-256 `329c9281ca334a82091120f9872b314d4a31b6b46867b65f569bbaf5e9f0c9f9`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
