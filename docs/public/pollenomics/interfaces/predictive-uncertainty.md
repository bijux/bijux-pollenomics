---
title: Supplied predictive uncertainty
audience: developer
type: how-to
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-16
---

# Supply a paired law without opening target pollen

Use `bijux_pollenomics.analysis.lra_validation.spatial` when you already have
an explicitly supplied finite law over training reconstructions and their paired
forward inputs. Its exported `JointSpatialDraw`, `UnavailableSpatialDraw` and
`propagate_withheld_spatial_draws` preserve the complete atom population. They
do not estimate or authenticate a field uncertainty distribution.

A `JointSpatialDraw` binds its rational probability mass, training compositions,
coordinates, forward regional deposition/PPE/kernels, and dependency identities.
Every successful atom refits the spatial model on the training groups and forwards
that atom's prediction using its own paired context. Do not independently shuffle
training and forward axes. All atoms must address one fixed target temporal
support; chronology-dependent training membership may vary within that support.

The fold excludes the complete target group, including aliases and derived input
ancestry. Outcome-free target geography and support are legitimate forward
inputs. Target pollen, observed count totals and target vegetation labels are
not arguments to this operation.

## Run the repository example

Install the repository's developer/numerical dependencies first. From its root,
run this Python snippet with that configured environment:

```python
from pathlib import Path

from bijux_pollenomics_dev.lra_validation.predictive_uncertainty.example import (
    run_example,
)

repository = Path.cwd()
result = run_example(
    repository=repository,
    law_path=repository / (
        "packages/bijux-pollenomics-dev/tests/fixtures/"
        "predictive_uncertainty/paired-law.json"
    ),
    expected_sha256="218d55540c868e14eecad8a6d1dbc1ccf1b0d29432a2da5d4f410c4802df4c27",
    output=repository / "artifacts/predictive-uncertainty/example",
)
print(result["cases"])
```

The destination must be absent and inside this repository's `artifacts/`.
The private fixture reader accepts only this example's fields; it is not a
supported file format for arbitrary field laws. The SHA authenticates the supplied
fixture bytes before construction. It does not approve their scientific law.
The example imports canonical package implementations, not a source overlay or
an artifact-only review adapter.

The constructed law has two training sites, one withheld `p10` group including
`p10-alias`, two taxa, and two paired atoms with masses 1/3 and 2/3. The fixed
Gaussian length scale is 100 km. The declared ridge penalty is
`(1 - exp(-0.5 * (training_distance_km / 100)**2))**2`; it is an illustrative
algebraic choice, not a tuned field parameter. Coordinates, forward kernels and
parameter values are constructed inputs. No field data or kernel integration
is performed.

Three files retain the complete API result:

| File | Population | Interpretation |
| --- | --- | --- |
| `complete.json` | Both supplied atoms succeed | Mean and population covariance of this finite supplied law |
| `mixed-refusal.json` | First atom succeeds, second has an upstream refusal | Successful mass 1/3, failed mass 2/3; unconditional moments unavailable |
| `all-unavailable.json` | Both upstream atoms refuse | Failed mass 1; no spatial fitting, forward prediction or moments |

The complete example's vegetation means are `(20/27, 7/27)` and its pollen
means are `(52/81, 29/81)`. These values reuse the existing exact paired-law
calculation check. This example is a way to use the API, not new field evidence.

## Carry upstream refusals intact

A reconstruction can refuse before a numerical composition exists. Preserve its
original serialized row in `UnavailableSpatialDraw`, together with the original
row's byte identity, exact mass, fixed target support and training ancestry.
The example calls the maintained upstream `project()` missing-role branch on a
deliberately incomplete constructed sample selection. That branch returns its
real `missing_role_in_bin` envelope before constructing a child request or
accessing an admitted plan. It does not simulate successful upstream admission.

Use an actual scientifically admitted source projection and its authorized
bin-to-target-support mapping for a physical application. Never invent a
composition for a refused row, discard its probability mass, renormalize only
successful atoms, or replace an interrupted atom with a zero result.

Any failed mass suppresses the unconditional mean and covariance. A source
hash alone leaves `law_authenticity_verified` false. Fixed-law intervals and
empirical coverage are not supplied; `intervals` remains `None`. Known numerical
refusals retain their causes, while unknown implementation or infrastructure
errors propagate rather than becoming failed probability mass.

## Interpret identifiability separately

`spatial_identifiability` reports unpenalized centred-feature rank, the target
row-span diagnostic and ridge-augmented rank. This example has raw rank 1 and
ridge-augmented rank 2. A unique regularized solve does not identify physical
inverse parameters or establish independent predictor information.

The workflow explicitly conditions out target-coordinate, spatial residual,
observation, hyperparameter-selection and taxon-model processes. A physical law
needs appropriate upstream evidence and justified treatment of those omissions.
This example establishes no calibrated field interval, independent vegetation
accuracy, chronology calibration, ecological inverse identifiability or complete
withheld-site uncertainty acceptance.

## Fixed-support conditional source cases

`SourceCasePlan` and `run_source_lra_cases` provide a separate exploratory
route for retained paired analytical requests. The caller supplies exact byte
references for the base request, its source evidence, a parameter reference
scale and domain, and each explicitly conditioned parameter vector. Admission
preserves pooled-bin identities, count and taxon axes, chronology support,
stationarity decisions, geometry, exclusions and configuration. A pooled bin
remains a pooled bin; this route neither invents native observation identifiers
nor authenticates a caller's empirical origin claim.

Import `SourceCasePlan`, `run_source_lra_cases` and `read_source_lra_cases`
from `bijux_pollenomics.analysis.lra.api`. A plan uses schema
`lra-source-cases.v1`, profile `source-fixed-support-analytical-v1` and purpose
`exploratory`. File references carry a canonical relative path, SHA256 and exact
byte length. Inputs are captured through selected descriptor-bound reads into
private analytical storage before the deterministic host is called.

Choose `unweighted_sensitivity` for cases without an explicit probability law;
its aggregate mean, covariance and probability masses are unavailable. A
`caller_weighted_finite_design` instead requires a separately pinned law with
positive rational masses covering exactly the declared cases and summing to
one. This is a caller-declared conditional design, not an inferred empirical
uncertainty distribution. Refused cases retain their mass; no successful subset
is renormalized, and incomplete designs have no full-law mean or covariance.
Raw and per-case clipped/adjusted cover are different estimands and are
aggregated separately with the existing population-moment routine. These
moments describe supplied-design dispersion of conditional point estimates,
not source standard errors, confidence intervals or full reconstruction
uncertainty. Existing source SD/SE metadata remains in the retained source
snapshot; this workflow does not propagate that uncertainty.

The final directory contains only a derived manifest: conditional results,
source references, code identities, coverage distinctions and design summaries.
Original source members, private basin cards and complete child request bundles
remain in separate private analytical recovery storage. Publication grants no
redistribution permission for those source members. `read_source_lra_cases`
checks derived internal consistency and an optional independently retained
manifest digest without opening original external inputs. Source authenticity,
scientific acceptance and terrestrial-denominator admission remain unevaluated.
When native full pollen totals lack independent bound evidence, both full and
excluded totals stay unknown; a design mass of one does not fill that gap.
