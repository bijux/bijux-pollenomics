# Native backend adoption decision

The current LRA runtime keeps its Python and NumPy implementation. The
[measured C++17 forward batch](../native-forward/README.md) did not meet the
prospectively declared **2× validated-call latency** gate at any of its three
shared-input shapes. Its NumPy-to-native latency ratios were 0.928, 0.897 and
0.722; values below one mean the native call was slower. Numerical agreement
with the public Python forward calculation was within the declared tolerance.
The independent R matrix equation checks this bounded calculation, but is not
the original DISQOVER execution path.

The [isolated worker comparison](../native-memory/README.md) confirms matching
forward outputs across five workers per method and shape. At the additional
8192 × 256 × 512 stress shape, native peak RSS was about 31 MB lower while
its median call remained slower (12.507 versus 9.388 ms). The large shape was
exploratory and does not change the latency gate. Python startup, imports,
input construction and export dominate the full worker times, so these
measurements do not establish a complete REVEALS or LOVE pipeline speed ratio.

The [seven-workload Python baseline](../python-baseline/README.md) and
[isolated Python resource measurement](../python-isolated/README.md) cover
REVEALS, analytical and optimized LOVE, series and forward execution. Each
isolated worker constructs only its named fixture; all 35 workers matched the
retained scientific and nonfinite output digests. These measurements supply
Python resource context. They do not show that the C++ forward result
generalizes to the other six workloads.

**Decision:** defer production C++ adoption. This closes the conditional
adoption decision for the measured forward boundary; it does not certify a
C++ LRA engine or waive investigation of another kernel with a demonstrated
benefit. The private binary stays in regenerable artifacts. No production
binding, platform wheel, SBOM or host dispatch path is claimed. If a later
representative workload identifies a candidate that meets a declared benefit
gate, revisit source-R/Python/C++ parity, buffer lifetime and ownership,
failure behavior, platform builds, packaging and release checks before
adoption. Empirical Nordic LRA remains separately gated on admitted pollen
samples, full taxon/PPE denominators and age-qualified basin geometry.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/runtime comparison reader; method correspondence and empirical/historical accuracy acceptance remain separate even when performance measurements pass.

**Supported claim.** This decision reader retains the measured refusal to adopt the artifact-only compiled forward candidate: all three conversion-inclusive validated speed ratios are below the prospective twofold gate.

**Unsupported claim.** It supplies no production C++ backend, portable wheel, full LOVE/REVEALS speed claim, field result or independent new benchmark execution.

**Actual verification performed.** Read this decision and the separately retained forward and isolated-memory accounts; verified their physical identities. No compiler, timing worker or numerical model ran for this reader qualification.

**Remaining input or review.** Adoption requires a real representative bottleneck, passing full-call speed and memory gates, source parity, supported-platform packaging and an explicit maintained boundary.

**Cause category.** Negative measured adoption decision rather than an implementation deliverable.

**Consequence.** The compiled artifact remains experimental; a lower RSS observation on one large stress shape does not overturn slower full-call latency.

**Precise next acceptance route.** Only reopen adoption on a newly declared representative workload and source-bound implementation that passes the existing twofold conversion-inclusive gate and required distribution qualification.

**Negative or refused result.** Ratios 0.928, 0.897 and 0.722 fail the speed gate. On the large stress case native 12.507 ms is slower than NumPy 9.388 ms despite lower observed RSS.

**Matched denominator.** This reader adds zero new benchmarks or compiled products. Linked forward comparison has three shapes; linked memory study has four shapes, two methods and five workers per method/shape (40 workers).

Qualified authored reader SHA-256: `4793dc7e0f557b695475cc55d9f7b28759a8ea8572469f61a64b76c48f845db9`.

- [Retained qualification evidence: docs/report/numerical-performance/native-forward/report.json](../native-forward/report.json) (SHA-256 `4d16a1400d6878f2abf21f796fb190dd72a365f0dd40295639b8635bd807d1d5`).

- [Retained qualification evidence: docs/report/numerical-performance/native-memory/report.json](../native-memory/report.json) (SHA-256 `6fcac93d4ccb79e80f8bedecb131e209e026800d7b979129025e47a628976f06`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
