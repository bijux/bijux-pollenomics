# Bijux Pollenomics LRA

An optional GPL-2.0-or-later scientific engine in the Bijux Pollenomics workspace.
The supported Python facade is `bijux_pollenomics_lra.api`. It provides typed
regional REVEALS, analytical and optimized LOVE, paired and exact-coordinate
series workflows, and homogeneous-local forward pollen prediction.

The current backend is **Python/NumPy/SciPy**. C++ adoption remains a measured
engineering decision; this package does not claim C++ execution. The exact-source
DISQOVER 0.9.14 oracle runs separately from the shipped numerical engine.

Pollen frames have a finite numeric coordinate in the first column and unique
named taxon count columns thereafter. The host retains canonical sample IDs,
units, chronology, parameter and geometry lineage. LOVE requires local pollen;
a model for predicting an unobserved site is a separate host experiment.
`run_lra` and `run_lra_series` take local pollen before regional pollen.

Use the host CLI to prepare inputs, execute analysis and register products.
This engine has no separate collection CLI or host product adapter. Numerical
results offer `.write(directory)` for their scientific tables and manifests.
`ConvergenceError` preserves optimizer diagnostics while refusing a successful
result when any optimization run fails to converge. Candidate replay checks
objectives and wrappers; it does not establish optimizer convergence.

The package follows host Hatchling/hatch-vcs release tags. Installed metadata
identifies the engine build; an unbuilt checkout reports `0+unknown`. See
[architecture](docs/architecture.md), [scientific validation](docs/validation.md),
and the source [compatibility notes](docs/reference/source-compatibility.md).

The original GPL source is retained under `vendor/`. `NOTICE` records authorship
and distribution obligations. Optional loading alone does not establish legal
compatibility of a combined redistribution.
