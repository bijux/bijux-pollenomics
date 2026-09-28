# LRA source and wheel distribution check

The [LRA package build configuration](../../../packages/bijux-pollenomics-lra/pyproject.toml)
selects only source, tests, documentation, the source archive and package
notices for its sdist. The wheel selects the import package. A fresh build on
CPython 3.11 with `uv 0.11.17` checked the configuration at product commit
`02e69831` plus the package configuration SHA-256
`af2de6d9b491077b77f7a0ec8e7839dfeceb25351dd536a4e429b604c8e8932e`.
The version generated from that dirty worktree was
`0.1.9.dev418+dirty`; these hashes identify this local check, not a release
candidate.

| Built artifact | SHA-256 | Content check |
| --- | --- | --- |
| sdist, 1,132,428 bytes | `773e54f534e21b391ef53832f19b242e8dca264be64732261b4ade2cc70b70fb` | 128 regular files, including source, tests, docs, vendor archive, license and NOTICE; zero `artifacts/` entries. |
| wheel, 260,548 bytes | `260702b46ad92f79bfacae0b5fa1badb51ec50ab300160440ed85845045ec84d` | 63 files, including both JSON schemas, bundled example JSON, LSM model data, license, NOTICE and the host extension entry point. |

Building a wheel **from the generated sdist** yielded a byte-identical wheel.
Both the wheel and the sdist installed independently into fresh isolated
environments with their declared NumPy, SciPy and pandas dependencies. With a
PATH containing no `R` or `Rscript`, the wheel installation ran a deterministic
paired REVEALS/analytical LOVE example, discovered the `lra` extension entry
point and opened its bundled schema and model/example resources. The direct
sdist installation loaded the same descriptor and resources and evaluated a
deterministic LOVE numerical function. The wheel import resolved inside the
isolated environment's `site-packages`, rather than the repository source tree.

The package declares `GPL-2.0-or-later` and preserves the supplied DISQOVER
source attribution in [NOTICE](../../../packages/bijux-pollenomics-lra/NOTICE).
The fresh install resolved NumPy 2.4.6, SciPy 1.17.1 and pandas 2.3.3.
Installed metadata reports NumPy's compound `BSD-3-Clause AND 0BSD AND MIT
AND Zlib AND CC0-1.0` expression; SciPy and pandas distribute license text
headed by BSD terms rather than a single SPDX expression in their installed
metadata. This records the direct numerical dependency and source-license
review; the dependencies' full bundled third-party notices still govern any
redistribution.
The [source identity receipt](../method-certification/disqover-source-identity/README.md)
checks the retained vendor archive. This local packaging result establishes
file selection, fresh installation and R-free deterministic operation on this
platform. It does not certify other platforms, hosted release CI, redistribution
decisions or Nordic ecological validity. A final frozen release candidate must
be built and checked under its own version and dependency identity.
