# Supplied DISQOVER source identity

The supplied `disqover_0.9.14.tar.gz`, the prototype's vendored copy and the
[retained product vendor archive](../../../../packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz)
are byte identical: each has SHA-256
`ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`.
Every one of the archive's 80 regular-file members matches the supplied
extracted source tree byte for byte; that tree has no extra files. All 13 R
source members are included in that equality. This comparison establishes
local copy identity without requiring the old workspace copies for future
execution. The product's archive remains the durable source copy.

The archive's `DESCRIPTION` identifies package version **0.9.14**, license
**GPL (>= 2)**, and package date **2026-01-22 10:02:31 UTC**. Its description
says LOVEr and LOVEoptim were added in version 0.9.12. The
[source lock](../original-r-reference/reference-bundle/source-lock.json),
[isolated R installation](../original-r-reference/reference-bundle/provision.json)
and [current R oracle](../original-r-reference/README.md) bind subsequent
numerical work to this exact archive. The isolated installation is an actual
run receipt, not evidence that the 2024 paper used this later package build.

The [2024 LOVE paper](https://doi.org/10.3390/quat7020018) cites the DISQOVER
package as accessed on 23 February 2024 but does not identify this 2026 archive
as the paper's executable source. Paper-method correspondence and archive
numerical parity therefore have distinct provenance claims.
