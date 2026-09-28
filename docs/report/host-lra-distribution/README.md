# Installed host LRA integration

The [host build configuration](../../../packages/bijux-pollenomics/pyproject.toml)
selects its source tree and notices explicitly for the source distribution. An
initial local build attempted to include thousands of files under `artifacts/`;
the corrected `only-include` configuration (SHA-256
`5210c72e9ee4827f64c81f7ca1906e2fe4465cb6cf227311378fc77038ed8aaf`)
produced the following CPython 3.11 candidates at product commit `8aec9872`
plus that configuration change. The dirty VCS version
`0.1.9.dev419+dirty` is a local build identity, not a release version.

| Candidate | SHA-256 | Selection |
| --- | --- | --- |
| Source distribution, 1,677,846 bytes | `fa6a511ee087bb93069bd8316df1332068086d8be63de7349c4939712ebfb1f6` | 1,401 files; zero `artifacts/` entries. |
| Wheel, 2,474,752 bytes | `5beb2e7059bc9be24b0607ae8bd1e5046bf8fd5619ede4599362034d0d01b374` | 1,400 files; zero `artifacts/` entries. |

A wheel rebuilt from this source distribution was byte-identical to the direct
wheel. In a fresh isolated environment, the host wheel installed with its
declared base dependencies and without NumPy, SciPy, pandas or the LRA
distribution. The installed host resolved from that environment's
`site-packages`; `load_engine()` refused with `lra_extension_missing`.
Installing the separately built LRA wheel and its dependencies in that same
environment exposed the single `bijux_pollenomics.extensions:lra` entry point
and its declared version/backend. The PATH excluded R and Rscript.

The installed `bijux-pollenomics` CLI validated a two-taxon synthetic request
and ran all supported method routes through the host adapter. Results under
`artifacts/jobs/host-distribution/products/` have the following content
identities; each manifest reports `generated_exploratory` and
`scientific_acceptance: not_evaluated`.

| Route | Method profile | Scientific content SHA-256 |
| --- | --- | --- |
| REVEALS | `disqover-0.9.14-source-compatible` | `7629d2570d4d4eef011cc4d4403bbcfdc4569cafe992913fea31994ce1f46ef2` |
| Analytical LOVE | `disqover-0.9.14-source-compatible` | `540d9f4414120771a47f1575c79a8860ccd76299b4b1c36138063329f657e0f1` |
| Paired LRA | `disqover-0.9.14-source-compatible` | `cae8a1eb519cc9dd778f9cd6185fa163ddf23773d8a2fb11202352846ec32752` |
| Series | `disqover-0.9.14-source-compatible` | `f8ca0d6839a888f36828dbf369909012b0a656d873d31bb297bd5d4a52b640b4` |
| Optimized LOVE | `ring-taxon-preserving` | `704e8d18b1a2383c9922821b976c306581d5c7686eb72fe5cc7135869966b1d3` |

Input validation returned `validated_exploratory_input` for the valid request.
An absent request file returned exit code 2 with structured
`lra_request_io_or_encoding` refusal. The installed extension's incompatible
metadata, facade and capability paths remain covered by the focused discovery
tests in the host package. The run fixtures are synthetic, with two taxa and
at most two samples; they establish installation and dispatch behavior only. A
source-qualified Nordic cohort, empirical uncertainty interpretation and
independent vegetation validation require separate evidence.
