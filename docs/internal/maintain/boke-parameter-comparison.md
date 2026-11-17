---
title: BOKE Parameter Comparison
audience: maintainer
type: how-to
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-11-17
---

# BOKE Parameter Comparison

Use the maintained nominal comparison to connect the retained BOKE/KRAG request
and parameter-source evidence to the fixed-support source-case workflow. It
compares the existing LandClim nominal Betula PPE of 5.106 with European Betula
4.94 from the 2025 compilation, while keeping Ulmus at 1.27, fall speeds,
original source SD metadata, counts, chronology and physical assumptions fixed.
The European Ulmus value is missing; it is not filled from another region.
The author alpha 5.10571 remains distinct from the displayed baseline 5.106.

Run from a clean source checkout with the host, LRA and developer packages
imported from that same checkout. The input repository may be a separate
retained-data location. The exact source revision identifies imported code,
not the input repository's incidental branch. The maintained input owners
require the original pinned baseline product, its nine evidence members, basin
source card, three public correspondence reports and the selected reference
metadata. They refuse changed or unavailable bytes. No source is acquired.

```sh
python -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.parameter_sensitivity \
  --repository /path/to/retained-input-repository \
  --output /path/to/retained-input-repository/artifacts/science/boke-nominal-parameter-comparison \
  --source-revision <full-imported-code-commit-sha>
```

The output parent must exist and the destination must be absent. This command
is a source-checkout maintainer workflow; it does not claim installed-package
qualification for this particular input-dependent command.

The host runs exactly two declared analytical cases with internal random draws
disabled. Both stages receive each case's same nominal parameter vector. This
is unweighted sensitivity: no probability mass, aggregate mean, covariance or
confidence interval is inferred. Count, chronology, basin, source-SD and model
uncertainty are not propagated. Known case refusals and unrun cases remain
explicit, and prevent a complete two-case difference.

The baseline's regional and local raw/adjusted numerical vectors must reproduce
the retained baseline exactly before a successful comparison is published.
The comparison retains the historical 100 km regional extent; it is a mixed
source nominal parameter contrast, not reproduction of the complete 2025 study.
The original native fall-speed field from that compilation is not used.

The final tree contains three files: `report.json`, `README.md` and
`source-cases/manifest.json`. Original source members and complete child bundles
stay in separate private analytical storage. The report preserves source and
plan digests, pooled support, physical assumptions, panel totals and separate
raw/adjusted changes in percentage points. It does not export individual count
vectors or silently supply a full native pollen denominator.

Local clipping follows the project assumption from discussion with supervisor
Anneli Poska, reported by the project author as personal communication. Each
case clips negatives to zero and renormalizes surviving positive mass; zero
surviving mass fails explicitly. Raw signed values remain available. Agreement
at a clipped endpoint does not establish parameter irrelevance or taxon absence.

The reader can reopen `source-cases/manifest.json` with
`read_source_lra_cases`, using the independently retained manifest digest from
`report.json`, without reopening original external source members. Full
forest/open/cereal cover, terrestrial-denominator admission, scientific input
acceptance and independent measured vegetation accuracy remain outside this
conditional two-tree comparison. The project's ten-percentage-point accuracy
criterion cannot be evaluated without a compatible independent reference.

## Qualified saved comparison

The [conditional nominal comparison account](https://github.com/bijux/bijux-pollenomics/blob/d461e34b80bfca71f1f4b7d16e4db228aeed0bd9/reports/science/pollen-reconstruction/bokesjon-pilot/parameter-sensitivity/README.md)
records two completed model cases and a separately qualified saved output.
The original operator refused a late software-identity bootstrap read after
publication and has no successful terminal receipt. Its failure remains immutable;
output qualification does not relabel that operator as clean or rerun its models.
Independent readback checks prior numerical parity, clipping and displayed deltas;
a separate review binds the two prepared requests and parameter declarations.
The public account retains the 100 km versus 2025-paper 1000 km distinction and
unknown full native pollen denominator. Original source members and full child
bundles remain private; no source-SD law or empirical accuracy is inferred.
