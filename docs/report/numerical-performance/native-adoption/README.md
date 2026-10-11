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
its median call remained slower (14.488 versus 12.397 ms). The large shape was
exploratory and does not change the latency gate. Python startup, imports,
input construction and export dominate the full worker times, so these
measurements do not establish a complete REVEALS or LOVE pipeline speed ratio.

The [seven-workload Python baseline](../python-baseline/README.md) and
[isolated Python resource measurement](../python-isolated/README.md) cover
REVEALS, analytical and optimized LOVE, series and forward execution. The
isolated workers construct all seven fixtures and one provenance source path
changed after the earlier baseline. Their timing sets are therefore not an
identical-source comparison, even though their scientific outputs match.
They supply resource context, not evidence that the C++ forward result
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
