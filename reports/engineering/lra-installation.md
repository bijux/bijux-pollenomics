# LRA installation and distribution decision

**Decision:** keep `bijux-pollenomics-lra` as a separate optional distribution
and expose it through the host's `bijux-pollenomics[lra]` extra. A single
installation command already selects both built wheels; combining their
source packages would not simplify the user operation demonstrated below.

The [host metadata](../../packages/bijux-pollenomics/pyproject.toml) declares
an Apache-2.0 runtime with small base dependencies and an `lra` extra pointing
to `bijux-pollenomics-lra>=0.1.5,<0.3`. The [engine metadata](../../packages/bijux-pollenomics-lra/pyproject.toml)
declares GPL-2.0-or-later, NumPy, SciPy and pandas, and one extension entry
point. The host [discovery contract](../../packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra/engine/discovery.py)
checks that installed distribution, version, entry point and API descriptor.
The [earlier standalone engine build](../../docs/report/lra-distribution/README.md)
also checked wheel contents and R-free numerical execution.

## Built-wheel check

At clean product commit `46fcf43f5`, both wheel builds and two fresh CPython
3.11 environments used offline cached dependencies. Generated files were
kept under `artifacts/jobs/lra-single-install/`.

| Wheel | Bytes | SHA-256 |
| --- | ---: | --- |
| `bijux_pollenomics-0.1.9.dev655-py3-none-any.whl` | 2,487,011 | `eb428cc0d8edbbc2c7060f847dd70c89d758402d1bf30b1f831eb1d0174d8eed` |
| `bijux_pollenomics_lra-0.1.9.dev655-py3-none-any.whl` | 261,194 | `2ddcd766eef56090b7786957b4bf88c29da6e05b679a49cda3bec8aece3991f3` |

With both wheel directories supplied as local indexes, one command installed
`bijux-pollenomics[lra]` into a fresh environment. It resolved both
`0.1.9.dev655` distributions and their 16 other dependencies. From a working
directory outside the source tree, with `PYTHONPATH` and `R_HOME` removed
and a `PATH` without R, the installed host loaded the installed engine and
verified its `lra` entry point and selected analytical LOVE capability.
Both imports resolved inside the environment's `site-packages`.

A second fresh environment installed the base `bijux-pollenomics` wheel only.
It had neither NumPy nor the engine package, and `load_engine()` produced the
declared `LRARefusal` directing the user to install the extra. This checks
the intended light base boundary on this local platform. It does not check
other operating systems, final release versions, public-index availability
or a hosted release pipeline.

## Why the split remains useful

| Option | Benefit | Cost or condition |
| --- | --- | --- |
| Separate engine with the host extra | One install command for users; base install stays light; the engine has an explicit scientific/version/entry-point boundary. | Coordinate compatible releases and check extension discovery in built artifacts. |
| Merge engine source into host distribution | One distribution artifact and version. | Pulls numerical dependencies and GPL-derived code into the Apache-declared host; requires a qualified redistribution and licensing review, plus migration of entry points, API and release contracts. |

Package size alone does not justify merging. The [Apache Software Foundation's
GPL compatibility explanation](https://apache.org/licenses/GPL-compatibility.html)
distinguishes Apache-2.0 compatibility with GPLv3 from GPLv2; a merge must
therefore be reviewed against the exact upstream rights and the project's
release model. This is a packaging decision based on current behavior, not a
legal determination. Reconsider a merge only if a measured user or release
problem remains after the optional-extra route, with qualified rights review
and an explicit migration/verification plan.
