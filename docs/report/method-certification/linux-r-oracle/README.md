# Local Linux R oracle execution

The [source-bound report](report.json) records a fresh local Linux ARM64 execution of source-built R 4.6.0 and the locked DISQOVER 0.9.14 library. All **43 core cases**, including 18 declared optimized LOVE cases, and **23 source-domain cases** passed. A separate observer decoded the saved R and Python vectors and compared all 66 cases with Decimal arithmetic and the original case tolerances. This is numerical correspondence evidence; it is not an ecological accuracy score or a hosted release certificate.

The [retained execution capture](../../../../data/method-certification/linux-r-source-capture/capture.json) contains the complete **2,148 executable source files**, three source provisioning files, 140 retained execution files, actual native terminal and independent numerical review. The 137 governed report outputs are exact projections of that capture. The [core](oracle/report.json) and [source-domain](source-domains/report.json) directories retain executed R scripts, manifests, original inputs, individual vectors, completion statuses and session information. Saved Python expectations are identified separately from R goldens.

The execution used a source snapshot exported from commit `6d8f1c5beffc2627b14e3330f8567e60f0fc8c36`. The host repository identity and protected input bytes were checked before and after both actual stages. The snapshot was not a Git checkout, and no in-container Git `HEAD` observation is claimed. The [context](context.json) binds the generated report and its captured source bytes. Later metadata admission retains this execution epoch; it does not relabel the run as a later commit. The maintained capture consumer also checks that the 127 LRA package and numerical reference source members, and the R dependency lock, remain unchanged.

An older result described 1,661 executable source files and post-run observations of commits `44c89c7c77f720166a86dc73b750b3e9223945d2` and `a862468a8ad93cc2e522bdf0173f81f6b84e8cc9`. Four original source bodies remain unavailable for that historical epoch. Its four metadata outputs and source-recovery refusals are retained separately in the capture. The fresh execution does not repair or certify those missing historical bytes. Of the current 137 report outputs, 133 are byte-identical to the older result; the four changed JSON files record the new execution and source identities. Every CSV, NPY, NPZ, R script, text result and log in that correspondence remains byte-identical.

## Runtime and private custody

The run reused a source-built Linux R prefix and its qualified private package library. The producer authenticated 38 source archives, the build and provision receipts, **1,227 runtime files**, **2,784 library files**, the package-version closure and the DISQOVER archive. The source, runtime and library were mounted read-only into a local container with one CPU, 4 GiB memory and no network. The runtime was R 4.6.0 on `aarch64-unknown-linux-gnu`; its exact image, Python and numerical dependency identities remain in the report.

The private `lra-reference/` store retains the runtime, package library, 37 R/CRAN archives plus the separately governed DISQOVER archive, image identity and Dockerfile. Its `linux-arm64-oracle/custody.json` SHA-256 is `0398b643a2124ce44d9854a6979b1939c6c93337ddea30d1e030439de44d3575`. The retained custody also identifies 130 acquisition, build and provisioning process files. The public source capture does not redistribute those private binaries or an image archive. DISQOVER remains governed by the [LRA NOTICE](https://github.com/bijux/bijux-pollenomics/blob/main/packages/bijux-pollenomics-lra/NOTICE).

## Reproduction

Restore the exact qualified private store and local image. Set `BIJUX_LRA_CUSTODY_ROOT` to its `lra-reference/` directory, use the project development environment, and run the [maintained producer at the executed source revision](https://github.com/bijux/bijux-pollenomics/blob/6d8f1c5beffc2627b14e3330f8567e60f0fc8c36/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/linux_reference.py) with absent output destinations:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.lra_validation.linux_reference \
  --repository . \
  --output artifacts/jobs/linux-r-oracle/reproduction \
  --retained artifacts/jobs/linux-r-oracle/reproduction-retained \
  --runtime-tree "$BIJUX_LRA_CUSTODY_ROOT/linux-arm64-oracle/runtime" \
  --provision-tree "$BIJUX_LRA_CUSTODY_ROOT/linux-arm64-oracle/provision" \
  --source-cache "$BIJUX_LRA_CUSTODY_ROOT/source-cache" \
  --image-id-path "$BIJUX_LRA_CUSTODY_ROOT/linux-arm64-oracle/image.id" \
  --dockerfile "$BIJUX_LRA_CUSTODY_ROOT/linux-arm64-oracle/Dockerfile"
```

The producer checks every archive, receipt and installed file before execution. Another machine must restore the exact image or qualify a replacement; a changed runtime or library also needs its own qualification. A new execution belongs to its own captured source and runtime epoch. Reading or transporting the retained public capture performs no R execution.

## Release boundary

This result is **local Linux ARM64 numerical evidence**. The locked release job requires Ubuntu 24.04 on x86_64, a matching GitHub run and attempt, committed source revision and uploaded artifact digest. Those hosted records remain absent. The [release gate](../reference-release-gate/README.md) must assess its own actual same-attempt certificate. The two explicit release refusals remain preserved. Numerical parity does not establish stochastic optimizer trajectory parity, independent vegetation accuracy, ecological propagation accuracy or qualified human acceptance.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** Actual source-closed localLinuxARM64 R4.6/DISQOVER execution passed43core and23source-domain cases with complete2148executable source files,3source provisioning files and independentDecimal50 original-tolerance comparison. The exact137current report outputs are transported by an authenticated retained-source capture.

**Unsupported claim.** No lockedUbuntu24.04x86_64 hosted run/attempt/artifact, in-containerGitHEAD observation, stochasticoptimizer trajectory, independent vegetation/ecological accuracy, rights or qualifiedhuman release acceptance is supplied.

**Actual verification performed.** Actual native43+23 run and independent numerical observer both exited0 at source commit 6d8f1c5beffc2627b14e3330f8567e60f0fc8c36; hostGit/protected inputs stable before/after. Metadata-only assembly independently authenticated2311retained members plus capture. Strict137transport/current127source-and-metadata/Rlock guards passed controlled positive and tamper cases; no R was rerun for reader publication.

**Remaining input or review.** Official hosted release admission still requires its own matching locked platform/provider/run/attempt/source/artifact certificate. Four source bodies remain missing for the distinct original1661file historical epoch; that gap does not certify or replace the fresh complete source execution at commit 6d8f1c5beffc2627b14e3330f8567e60f0fc8c36.

**Cause category.** Complete bounded local numerical/source custody; hosted release-provider evidence absent and older source-gap epoch retained separately.

**Consequence.** The current137outputs have exact retained-source numerical authority. They remain local method correspondence evidence and do not become a hosted release or ecological accuracy certificate.

**Precise next acceptance route.** Use the maintained source-capture transport for exact current report bytes and unchanged scientific implementation; collect a genuine locked same-run/attempt hosted certificate for official release admission. A changed numerical source/dependency requires its own qualification; no historical relabelling.

**Negative or refused result.** The prior changed-source run and original1661source four-file gap remain explicit. local_linux_arm_is_not_locked_ubuntu_x86_64_ci and github_run_attempt_and_artifact_absent remain refused; neither44c nor a862postrun observation is substituted for execution-time identity.

**Matched denominator.** 43core+23source-domain cases;2148executable+3source provisioning files;140retained execution files and137report outputs;127current LRA/reference source-and-metadata members plus unchanged Rlock;1227runtime/2784library files/38archives. Zero new hosted runs.

Qualified authored reader SHA-256: `63016d0a6da3e146ebe6a769616b94a3da9a7622983a3dedf585c0246b1a3b34`.

- [Retained qualification evidence: docs/report/method-certification/linux-r-oracle/report.json](report.json) (SHA-256 `e67f3d4fb6316094f37b6d3a4a4db7bdb604dba5d564b54522b825ffe62ee1f7`).

- [Retained qualification evidence: docs/report/method-certification/linux-r-oracle/context.json](context.json) (SHA-256 `b535e12bfd2121a74dcb9bd98067659e878829d8551bd8e63d2e00942fa84cba`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
