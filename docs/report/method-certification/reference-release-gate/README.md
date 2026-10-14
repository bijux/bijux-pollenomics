# Locked R release profile

The locked [certificate producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/certification.py) and [bundle validator](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py) require **43 core cases plus 23 source-domain cases** for a new same-attempt release certificate. The additional 18 core cases bind the frozen three-fixture optimized LOVE declaration by its exact input hashes, case IDs, API/mode, prospective tolerance, axes, wrapper replay exact coordinates and nonfinite/refusal behavior. Missing or substituted cases cannot pass by retaining the old 25-case total.

The [original 25-case certificate](../original-r-reference/reference-bundle/certificate.json) remains verifiable for its historical source commit without an expected CI run. It cannot meet the new same-attempt release gate. The [current native R result](../current-r-oracle/README.md) ran all 43 + 23 cases and preserved raw output, but its macOS R runtime is distinct from the locked source-built Linux release runtime. The new gate requires the source-built Linux runtime and complete private library file inventory, current committed source identity, matching GitHub run/attempt and exact artifact bytes. No current Linux release certificate is claimed here.

The release check also requires a successful native/live-R parity job from that same run attempt. It retrieves the parity artifact by provider digest and verifies its 43 case IDs, input and Python expectation hashes, source lock, and live-R certificate hash against the certified R bundle. A successful R job alone cannot satisfy this release check. The parity receipt is retained beside the release evidence for an accepted candidate.

The focused certificate and release-gate selection passed **56 tests** in 1.12 seconds. The full `lra_reference` test package then passed **90 tests** in 1.03 seconds. Strict mypy passed for the changed source/test files; Ruff check and formatting passed after formatting the adjacent R comparison reporter. The tests cover old-certificate preservation, a complete 43-case synthetic validator fixture, missing prospective cases, changed input declaration, missing exact-coordinate evidence, missing bundle members and stale/forged release artifacts. Synthetic fixtures are validator tests; only an actual locked CI R execution can create a release certificate.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** This reader describes the required release admission contract:43 core plus 23 domain R cases and a linked native-parity artifact from the same hosted run, attempt and source revision.

**Unsupported claim.** A documented gate or passing synthetic gate tests is not an actual hosted Linux certificate, scientific source endorsement, measured accuracy result or authority to publish.

**Actual verification performed.** Reviewed the authored gate contract and stable correspondence accounts and bound their bytes. This reader qualification executed no hosted job, R process, gate test or publication action.

**Remaining input or review.** Actual completed same-revision hosted Linux/R certification, native parity, provider identity and all publication-gate inputs remain required at the real release candidate.

**Cause category.** Required release evidence contract with absent current hosted admission.

**Consequence.** Local numerical and contract evidence can prepare admission inputs; official LRA release remains unqualified until the actual artifacts pass the maintained gate.

**Precise next acceptance route.** Collect the locked Linux source-built R and native-parity artifacts from one actual GitHub run/attempt/source commit, verify provider and source identity, then execute the maintained admission gate before any separately authorized publication.

**Negative or refused result.** The historical 25-core certificate remains historical and insufficient for the 43-core gate;56 focused and 90 full synthetic gate tests are not a replacement hosted certificate.

**Matched denominator.** Required artifact scope:43 core R cases,23 domain cases and matching native-parity identities. Own population: zero new R cases, hosted runs or measured observations.

Qualified authored reader SHA-256: `1b6fdc2adacc2b43d38add111ba2588b5264e5cb1843de3776099be83e8c8e6b`.

- [Retained qualification evidence: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Retained qualification evidence: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
