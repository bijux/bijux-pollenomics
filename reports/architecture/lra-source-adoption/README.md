# How we selected the LRA source to adopt

## Our source decision

We retained three distinct authorities. The supplied `disqover` 0.9.14 R
archive is the numerical and authorship reference. The supplied
`disqover-native` 0.1.0 ZIP is a Python translation candidate and a useful
function inventory; its parity reports are evidence from that candidate, not
results produced by our engine. Our adopted engine is
[`bijux-pollenomics-lra`](../../../packages/bijux-pollenomics-lra/pyproject.toml),
with its own [source notice](../../../packages/bijux-pollenomics-lra/NOTICE),
tests, API and result provenance. We selected the original R archive for
reference comparisons and reviewed translation ideas from the prototype. We
did not install or copy the prototype tree into the host.

| Source | Exact identity | Authority and disposition |
| --- | --- | --- |
| Original R archive | `disqover_0.9.14.tar.gz`; SHA-256 `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`; 80 regular archive members, including 12 R files | Scientific numerical reference, GPL (>= 2); retained unchanged in the engine's `vendor/` directory. |
| Python prototype | `disqover_native_python_port_v0.1.0.zip`; SHA-256 `2d34088f55327fc39ec09e48364e0d1d0b511bdd70a476852edeef42e51568d0`; 73 regular ZIP members | Candidate translation and source inventory, GPL-2.0-or-later; private original in the external data store. |
| Adopted engine | [Engine API](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py) and [extension descriptor](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py) | Current supported facade and numerical implementation, GPL-2.0-or-later; installed only through the optional host extra. |

The prototype ZIP includes a 72-entry `FILE_MANIFEST.json`; the extra member
is that manifest itself. We checked every listed member's SHA-256 against its
ZIP bytes and checked that no regular member was omitted. Its embedded R
archive has the same SHA-256 as the separately supplied original. The
[file disposition table](prototype-files.csv) records every archived member,
its manifest hash, role and adopted or rejected destination. The
[function disposition table](source-functions.csv) records all 41 active
top-level R functions or Rcpp wrappers reported by the candidate inventory:
14 public and 27 internal. A `method_route` in that table means our API
implements a corresponding scientific operation; it does **not** claim that
the candidate function was copied or that every function-level behavior is
equivalent. Exact equivalence belongs to the separate
[method correspondence](../../science/method-correspondence.md).

## What we adopted and excluded

| Prototype source | Our disposition | Current owner or reason |
| --- | --- | --- |
| `_rounding.py`, `_validation.py` | Refactored after source review | [R-compatible rounding](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/rounding.py), typed errors and model validation. The rounding algorithm retains R Mathlib attribution in our engine notice. |
| `dispersal.py`, `reveals.py`, `love.py`, `optimizers.py` | Scientific methods adapted behind a narrower facade | [Dispersal](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/kernels.py), [REVEALS](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/workflows/regional.py), [LOVE](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/workflows/local.py) and [optimizer](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/optimization/solver.py). Source-R and publication comparisons govern the supported profiles. |
| `datasets.py` and converted examples | Selected inputs reviewed, not wholesale runtime data | The engine owns explicit [example resources](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/examples.py) and [data](../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data); original source assets retain their R/archive identity. |
| `eda.py`, `erv.py`, `marcopolo.py`, `plotting.py`, `ropes.py` | Reference only | No claim that the adopted public API implements these complete workflows or prototype plotting/Excel interfaces. The original R functions remain available to independent source studies. |
| Prototype parity/tests/fixtures | Reference evidence | We use governed original-R and engine-specific cases; candidate logs and its `python_expected_not_R_goldens.npz` cannot certify current parity. |
| Prototype build, CI and documentation | Excluded as installation instructions | The prototype uses fixed `0.1.0` and setuptools. Our engine uses Hatchling, hatch-vcs and the workspace's package/test/release conventions. Generated logs, wheel receipts and candidate `Makefile` are not production files. |

Our current [distribution decision](../lra-distribution.md) records the actual
built-wheel and R-free host-consumer check. The host declares the optional
`lra` extra and discovers the engine through one registered extension point;
publication uses governed outputs rather than importing numerical kernels.
The root [workspace metadata](../../../pyproject.toml), [test selection](../../../configs/pytest.ini),
[tox configuration](../../../tox.ini) and engine metadata own installation and
verification. The prototype's `pyproject.toml`, test markers and project name
do not override them. A native C++ backend remains a measured, separately
reported implementation question; its prototype compatibility shim is test
material, not the engine or a public C++ API.

## Source and geographic boundary

This adoption selects an LRA **method implementation**, not a pollen cohort.
The source registry covers Neotoma, SEAD, LandClim, RAÄ, SVAR, AADR, animal
aDNA, boundaries, Rootsi, OpenLand and HYDE 3.5 as distinct families. The
[four-country cohort account](../../science/source-cohorts.md) gives the
SE/DK/NO/FI sample and count denominators and the remaining core-specific
LRA gates. The [HYDE source account](../../science/hyde-cropland-source-account.md)
keeps modeled land use separate from observed vegetation. Neither the R
archive nor the Python prototype supplies selected chronologies, historical
basin series, count denominators and permitted PPE use for a named Nordic
core. Their examples and parity cases have their own declared spatial and
temporal support; we have admitted zero Nordic LRA samples. We do not infer
four-country or historical-window completeness from package adoption.

| Current study | Geography and temporal support | What the engine adoption changes |
| --- | --- | --- |
| [Observed-pollen transfer](../../science/source-cohorts.md) | Selected sites in Sweden, Denmark, Finland and Norway; 500 cal BP bins with each attempted bin retained in the country coverage ledgers. | Nothing: these are direct pollen predictions, not LRA inputs. |
| [Author-example LRA](../../science/english-lra-pollen-prediction.md) | 15 English sites in the declared 1250–1750 BP source window. | The selected engine ran a bounded reconstruction and forward-pollen study; the source and profile assumptions remain explicit. |
| Nordic LRA and published historical windows | No named four-country core or exact historical paper input window has passed its source gates. | An available method cannot fill those source gaps or define their temporal support. |

The two CSVs are an inventory of the exact retained ZIP and its embedded
`reports/source_inventory.json`. Recheck them when the source ZIP changes;
the SHA above and each row hash prevent a similarly named delivery from
silently replacing this candidate. The CSV dispositions are architectural
decisions, while the source-side path, symbol and hash columns are transcribed
from the verified source.
