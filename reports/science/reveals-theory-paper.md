# Why large-site pollen can estimate regional vegetation

**Paper and question.** Sugita, S. (2007), “[Theory of quantitative reconstruction of vegetation I: pollen from large sites REVEALS regional vegetation composition](https://doi.org/10.1177/0959683607075837),” *The Holocene* **17**(2), 229–241. This is the first Landscape Reconstruction Algorithm (LRA) theory paper, commonly cited as **Sugita (2007a)**. It asks when pollen from large depositional sites can estimate a region's plant-cover composition despite heterogeneous vegetation. The distinction matters here because numerical agreement with a REVEALS program says nothing by itself about whether its inferred cover represents the vegetation around a particular core. [Indexed publisher citation and abstract](https://journals.sagepub.com/doi/10.1177/0959683607075837); [our source-specific method account](publication-correspondence/author-method-profile.md).

**Scoped conclusion.** In Sugita's **POLLSCAPE simulations**, the publisher abstract reports accurate regional estimates with relatively small standard errors from multiple lakes at least approximately **100–500 ha** in size; much smaller lakes can vary strongly between sites. Its target region is **10⁴–10⁵ km²**. These simulated findings do not measure accuracy at a Nordic core. Our separate author-R/native check covers **two later LandClim II example grids**. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075837); [two-grid execution](publication-correspondence/author-example-reexecution.md).

## The modeled quantity and source roles

A pollen percentage divides the counted grains assigned to a taxon by a defined grain sum. It is not that taxon's share of land cover: taxa produce unequal pollen quantities, grains disperse differently, and a basin receives pollen from more than its immediate shore. **REVEALS** (“Regional Estimates of VEgetation Abundance from Large Sites”) uses large-site pollen and taxon-specific relative pollen productivity estimates (**PPEs**, called RPP in some sources), with dispersal and deposition assumptions, to estimate **regional cover fractions**. Pollen fall speed, lake or bog type and basin size influence the distance weighting. These input roles are explicit in the [later LandClim author-method profile](publication-correspondence/author-method-profile.md); the accessible 2007 abstract establishes the model's regional question and large-lake/multiple-site conditions but does not expose its equations or parameter tables. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075837).

```text
regional vegetation in a simulated or observed landscape
  → taxon-specific production and transport → large-site pollen counts
  → REVEALS with declared productivity, fall speed and basin assumptions
  → estimated regional taxon-cover composition
```

The original test used **POLLSCAPE simulations** across landscapes and atmospheric conditions. Its abstract gives no site or taxon count, scenario ledger, or numeric error distribution. Large lakes are the regional evidence unit; the companion [LOVE theory](love-theory-paper.md) uses that regional estimate to address background pollen at small sites. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075837).

## An exact later source-to-result trace

The trace below tests an **installed calculation**, not a 2007 observation. The released **LandClim II author example** identifies `WHH05` as a grid-512 lake with a **150 m radius**. Its raw source sample at **depth 16**, **1320 cal BP**, contains **301 counted grains** across 30 named fields; the author-prepared **1500 BP** interval vector has **297 grains** across ten positive taxa, with the four-grain difference accounted for by four named, one-grain excluded fields. The age falls inside `[1250,1750)` cal BP; 1500 BP is the interval label, not the sample's measured age. The prepared model uses 31 taxa, and the source parameter table has 31 PPE means and a 31 × 31 covariance axis. [Authenticated source-to-input trace](publication-correspondence/author-example-site-replay.md).

The author R release and installed native engine then produce a **WHH05 site-level REVEALS** estimate for that 1500 BP window. In the retained paired row, *Calluna vulgaris* has author-R mean **0.9248830793** and standard error (**SE**) **0.0468069771**, both fractional-cover units. The row is one modeled taxon fraction and its model SE, not a measured cover fraction. Across the 31 means the composition sums to one to numerical precision. The maximum R/native residual among the window's means is **4.77 × 10⁻¹⁵**, and among SEs **8.90 × 10⁻¹⁶**. WHH05 contributes **eight of 25** supported windows in this example. These exact source identities and denominators make a calculation check possible while leaving ecological accuracy untested. [WHH05 account](publication-correspondence/author-example-site-replay.md); [paired rows](../../docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv).

The wider comparison covers **17 prepared lake sites** in two grids, **25 bins**, **31 taxa**, and **184 of 425** possible site-bins with available support. It matches **14,074 declared regional and site-level mean/SE values** within the recorded numerical tolerances. The released source is a later LandClim II author example using a 2016 REVEALS implementation; it neither reproduces Sugita's POLLSCAPE scenarios nor proves the 2007 paper's simulated error claim for historical vegetation. [Execution report](publication-correspondence/author-example-reexecution.md); [method profile](publication-correspondence/author-method-profile.md).

## What remains unresolved and how to use this account

The indexed publisher abstract is the direct 2007 evidence available here. Direct full-article access did not yield a lawful text for this account, and the retained source packet examined contains no Sugita 2007 paper PDF or original POLLSCAPE scenario tables. Therefore original numeric scenario errors, standard-error formula, exact atmospheric regimes, taxon list and parameter values are **not evaluated**. For our later example, the 17 sites are all lakes, so its agreement does not check bog transport; its historical PPE covariance propagation and 1,128-sequence archive provenance have separate limitations. Even a small R/native residual cannot resolve those source and physical-interpretation questions. [Source-specific profile](publication-correspondence/author-method-profile.md); [publication boundary](publication-correspondence.md).

Readers can inspect the [retained WHH05 trace](publication-correspondence/author-example-site-replay.md) and [two-grid result](publication-correspondence/author-example-reexecution.md) without private input bytes. To verify the two-grid governed execution report from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --verify-report docs/report/publication-replay/landclim-example-reexecution/report.json
```

A fresh R/native reexecution requires the separately identified lawful author snapshot and pinned R dependency, as specified in the [reexecution instructions](publication-correspondence/author-example-reexecution.md). It cannot rerun the 2007 simulation.

The **unsent source request** is for a lawful full Sugita (2007a) paper, its original POLLSCAPE landscape and atmospheric scenario definitions, basin sizes and positions, taxon/PPE/fall-speed inputs, regional truth vectors, REVEALS outputs and error/SE calculations, plus usable source permissions. The **unsent qualified-review request** is to assess whether a proposed pollen cohort has sufficiently large and appropriately distributed sites, matched taxa and support, and a defensible parameter/uncertainty profile for its target region. No independent scientific endorsement, original figure reproduction or colleague reading outcome is recorded here.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Sugita 2007a abstract-level REVEALS theory is distinguished from a later exact WHH05 author-code trace.

**Unsupported claim.** Original 2007 POLLSCAPE simulation reproduction or historical Nordic vegetation accuracy.

**Actual verification performed.** Retained primary indexed abstract and author-example receipts are described; index did not access full original paper.

**Remaining input or review.** Only indexed publisher abstract is directly available for Sugita 2007a; original POLLSCAPE scenario inputs/output and full lawful article are absent, and later LandClim replay is a different population. Resolver: Original theory-paper/scenario custodian and qualified REVEALS reviewer Reopen when: Lawful original scenarios, parameter/truth vectors and rights permit a separate 2007 experiment account.

**Cause category.** data|access/rights|comparability

**Consequence.** Do not attribute later author-code parity to the 2007 simulation.

**Precise next acceptance route.** Lawful original scenarios, parameter/truth vectors and rights permit a separate 2007 experiment account. Then update reports/science/paper-accounts.md.

**Negative or refused result.** Original scenario counts/errors not locally evaluated; later example is not original experiment.

**Matched denominator.** Original abstract names large lakes approximately 100–500 ha; later example has 17 sites, 184/425 supported site-bins, 31 taxa.

Retained evidence: [reports/science/reveals-theory-paper.md](reveals-theory-paper.md), [reports/science/publication-correspondence/author-example-site-replay.md](publication-correspondence/author-example-site-replay.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 1b1abd0b0b2fecdec6ca16aabafd8c5326d1181e7fcbb63b6faaf018d5cd13a0 -->
<!-- scientific-authored-source-sha256: 02426d55c1252148f9ec7e518a6f92593988d78cb1c33ecff7e280a8d09fede4 -->
<!-- scientific-verification-and-limits:end -->
