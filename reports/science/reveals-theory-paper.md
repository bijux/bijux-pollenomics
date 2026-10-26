# Why large-site pollen can estimate regional vegetation

**Paper and question.** Sugita, S. (2007), “[Theory of quantitative reconstruction of vegetation I: pollen from large sites REVEALS regional vegetation composition](https://doi.org/10.1177/0959683607075837),” *The Holocene* **17**(2), 229–241. This is the first Landscape Reconstruction Algorithm (LRA) theory paper, commonly cited as **Sugita (2007a)**. It asks when pollen from large depositional sites can estimate a region's plant-cover composition despite heterogeneous vegetation. The distinction matters here because numerical agreement with a REVEALS program says nothing by itself about whether its inferred cover represents the vegetation around a particular core. [Indexed publisher citation and abstract](https://journals.sagepub.com/doi/10.1177/0959683607075837); [our source-specific method account](publication-correspondence/author-method-profile.md).

**Scoped conclusion.** The supplied full article supports a conditional regional method and describes its **POLLSCAPE simulations**, including landscape, transport and error assumptions. Multiple lakes approximately **100–500 ha** can reduce variation in the simulated landscapes; this is not a universal minimum basin size or measured accuracy at a Nordic core. Its target region is **10⁴–10⁵ km²**. Our separate author-R/native comparison covers **two later LandClim II example grids**. [Sugita 2007a, pp. 234–238](https://doi.org/10.1177/0959683607075837); [two-grid execution](publication-correspondence/author-example-reexecution.md).

## The modeled quantity and source roles

A pollen percentage divides the counted grains assigned to a taxon by a defined grain sum. It is not that taxon's share of land cover: taxa produce unequal pollen quantities, grains disperse differently, and a basin receives pollen from more than its immediate shore. **REVEALS** (“Regional Estimates of VEgetation Abundance from Large Sites”) uses large-site pollen and taxon-specific relative pollen productivity estimates (**PPEs**, called RPP in some sources), with dispersal and deposition assumptions, to estimate **regional cover fractions**. Pollen fall speed, lake or bog type and basin size influence the distance weighting. These input roles are explicit in Equation (5), Tables 1–2 and Appendices A–B of the full article, and in the separate [later LandClim author-method profile](publication-correspondence/author-method-profile.md). [Sugita 2007a, pp. 231–233, 238–239](https://doi.org/10.1177/0959683607075837).

```text
regional vegetation in a simulated or observed landscape
  → taxon-specific production and transport → large-site pollen counts
  → REVEALS with declared productivity, fall speed and basin assumptions
  → estimated regional taxon-cover composition
```

## Full source, equations and published scenarios

The supplied original journal PDF contains **13 pages**, printed **229–241**, including both appendices. Its filename is `sugita-2007-theory-of-quantitative-reconstruction-of-vegetation-i-pollen-from-large-sites-reveals-regional-vegetation.pdf`, **867,410 bytes**, SHA-256 `7a1cae00b2ffad9a11f814a8a8d0bb34f51145304e657bde0dc040f64e51e4ce`. The original remains unchanged outside the repository. Text, PDF metadata and selected page images were inspected; no publisher PDF or full-text extract is redistributed here. This supersedes the earlier abstract-only access limitation.

For a site, Equation (5) and Appendix B1 close the corrected grain vector:

```text
u_i = n_i / (alpha_i K_i)
V_i = u_i / sum_j(u_j)
```

Here `alpha_i` is relative pollen productivity and `K_i` the taxon-specific dispersal/deposition coefficient. Appendix A uses Prentice transport for bogs and mires and Sugita (1993) transport for lakes. The neutral lake expression uses the **lower unregularized incomplete gamma**, of shape 8, with the three arguments `b_i (Zmax−R)^(1/8)`, `b_i (Zmax+R)^(1/8)` and `b_i (2R)^(1/8)`, multiplied by `4πR/b_i^8`. The maintained implementation uses the same gamma expression, with the rounded neutral coefficient `b_i = 75.2 × fall_speed_i / wind_speed`, as retained by the [historical publication deposition consumer](../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/publication.py). It establishes published formula provenance; it does not settle the later author's unresolved comment or qualify a physical basin. The paper distinguishes this lake approximation from the **Ring-Source** model used to generate simulated pollen. [Appendix A, p. 238](https://doi.org/10.1177/0959683607075837).

The source assumptions include circular basins without pollen-producing plants within them, nondirectional airborne transport, ground-level release and constant taxon productivity. Inlet and runoff pollen are excluded; the discussion explicitly warns about water-borne input. Distances and regional extent are measured from the basin **centre**, not its shore. The regional extent is **400,000 m** in these simulations. Neutral parameters are wind **3 m/s**, vertical coefficient **0.12**, horizontal coefficient **0.21**, and empirical turbulence parameter **0.25**; the unstable case uses **0.21**, **0.20** and **0.20**, respectively. The printed vertical coefficient has units **m^(1/8)**, rather than an ordinary SI diffusivity. [Table 1 and assumptions, pp. 231–232; Appendix A, p. 238](https://doi.org/10.1177/0959683607075837).

| Published input or denominator | Exact scope |
| --- | --- |
| Default taxa, PPE and fall speed (m/s) | Poaceae `1/.035`, Picea `1.77/.056`, Betula `8.94/.024`, Quercus `7.60/.035`, Fagus `6.73/.057`; the additional Pinus transport row is `5.71/.031`. |
| Default stand mixture | Matrix and three patch types occupy `.40/.30/.20/.10`; mean patch areas are `30±10`, `15±5`, `2±1 ha`. The five-taxon regional truth vector is `.423/.232/.144/.079/.122` in the order above. |
| Spatial construction | Random nonoverlapping circular patches in a `60×60 km` plot; vegetation beyond it to 400 km is homogeneous at the plot's mean composition. |
| Default sampling | Six randomly located lakes in the central `10×10 km` square per run, five runs, **30 lakes**; **1,000 grains** per lake. |
| Size and atmosphere comparisons | Radius sweep `20–2000 m`; this landscape's homogeneity threshold is `390 m` (about `48 ha`, significance `.05`). Atmospheric comparison uses `750 m` radius (about `177 ha`), 30 lakes and four simulated/fitted atmosphere combinations. |
| Larger-patch experiment | Patch type 1 varies `15–100,000 ha`, dominated by Picea or Pinus, in a `200×200 km` plot. This changes the appropriate basin-size threshold. |
| PPE covariance estimation | A separate **30-lake, 50 m radius** simulated set is input to the described `erv-v6.exe`; covariance is the inverse expected information matrix. Its numerical covariance array is not supplied. |

These are published settings and denominators, not recovered random landscapes or per-lake count/truth/output arrays. Table 1, Table 2 and the methods on pp. 232–235 supply the settings. A source inconsistency remains: the body on p. 234 calls the larger Figure 3 lakes **750 ha**, whereas that caption says **177 ha**, and p. 235 explicitly equates **750 m radius** with **177 ha**. The conflicting labels are not silently harmonized. The **100–500 ha** guidance therefore remains context-dependent; “large” is defined by statistical homogeneity, not a mandatory numerical cutoff. [Sugita 2007a, pp. 232–237](https://doi.org/10.1177/0959683607075837).

## Error propagation and the maintained conditional law

Appendix B, pp. 238–239, treats the dispersal factors as fixed and includes uncertainty in multinomial grain proportions and PPE estimates. Equation B2 retains covariance between a corrected taxon term and its closure denominator; B4 retains cross-taxon multinomial and PPE covariance. Some covariance terms and the multisite mean/variance are approximated by a **delta-method/Monte Carlo hybrid**. The article does not specify the executable, complete joint sampling law, draw count or seed needed to reproduce that hybrid exactly. The paper's description of independently obtained PPE estimates does not establish that PPE and pollen counts are statistically independent in every application. [Appendix B](https://doi.org/10.1177/0959683607075837).

There is a specific printed-formula discrepancy under the appendix's fixed-`K_i` definitions: B3 puts `var(alpha_i)/(K_i² alpha_i²)` inside the relative-variance bracket for `q_i/(alpha_i K_i)`. Direct differentiation with fixed `K_i` instead gives the PPE contribution `var(alpha_i)/alpha_i²` inside that bracket. The page image confirms the printed extra factor; this is an analytical discrepancy, not a claimed publisher erratum. The maintained [fixed-site covariance consumer](../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py) differentiates the closed inverse explicitly, combines fixed-total multinomial counting covariance with full PSD PPE covariance, and **declares zero count/PPE cross-covariance**. Its [joint consumer](../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_fixed_site_covariance.py) additionally declares support/dependence across observations. Those are conditional mathematical laws with [independent analytical checks and finite-domain refusals](method-correspondence.md#conditional-covariance-numerical-domain-refusals), not literal replication of every printed B3 term or of Sugita's unspecified hybrid. The later historical bootstrap's omission of PPE covariance remains visible in its [source profile](publication-correspondence/author-method-profile.md).

## An exact later source-to-result trace

The trace below tests an **installed calculation**, not a 2007 observation. The released **LandClim II author example** identifies `WHH05` as a grid-512 lake with a **150 m radius**. Its raw source sample at **depth 16**, **1320 cal BP**, contains **301 counted grains** across 30 named fields; the author-prepared **1500 BP** interval vector has **297 grains** across ten positive taxa, with the four-grain difference accounted for by four named, one-grain excluded fields. The age falls inside `[1250,1750)` cal BP; 1500 BP is the interval label, not the sample's measured age. The prepared model uses 31 taxa, and the source parameter table has 31 PPE means and a 31 × 31 covariance axis. [Authenticated source-to-input trace](publication-correspondence/author-example-site-replay.md).

The author R release and installed native engine then produce a **WHH05 site-level REVEALS** estimate for that 1500 BP window. In the retained paired row, *Calluna vulgaris* has author-R mean **0.9248830793** and standard error (**SE**) **0.0468069771**, both fractional-cover units. The row is one modeled taxon fraction and its model SE, not a measured cover fraction. Across the 31 means the composition sums to one to numerical precision. The maximum R/native residual among the window's means is **4.77 × 10⁻¹⁵**, and among SEs **8.90 × 10⁻¹⁶**. WHH05 contributes **eight of 25** supported windows in this example. These exact source identities and denominators make a calculation check possible while leaving ecological accuracy untested. [WHH05 account](publication-correspondence/author-example-site-replay.md); [paired rows](../../docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv).

The wider comparison covers **17 prepared lake sites** in two grids, **25 bins**, **31 taxa**, and **184 of 425** possible site-bins with available support. It matches **14,074 declared regional and site-level mean/SE values** within the recorded numerical tolerances. The released source is a later LandClim II author example using a 2016 REVEALS implementation; it neither reproduces Sugita's POLLSCAPE scenarios nor proves the 2007 paper's simulated error claim for historical vegetation. [Execution report](publication-correspondence/author-example-reexecution.md); [method profile](publication-correspondence/author-method-profile.md).

## What remains unresolved and how to use this account

The full article now resolves the equation, parameter-table, atmospheric-regime and error-method access gaps. It does **not** supply the original random POLLSCAPE realizations, numerical PPE covariance array, complete count/truth/result arrays, or the programs described as available on request. Figures are published evidence, not an authenticated numerical output ledger. No new simulation, refit or ecological validation was run for this source comparison. For our later example, all 17 sites are lakes, so its agreement does not check bog transport; its historical PPE covariance propagation and 1,128-sequence archive provenance retain their separate limitations. [Source-specific profile](publication-correspondence/author-method-profile.md); [publication boundary](publication-correspondence.md).

Readers can inspect the [retained WHH05 trace](publication-correspondence/author-example-site-replay.md) and [two-grid result](publication-correspondence/author-example-reexecution.md) without private input bytes. To verify the two-grid governed execution report from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.example_reexecution \
  --verify-report docs/report/publication-replay/landclim-example-reexecution/report.json
```

A fresh R/native reexecution requires the separately identified lawful author snapshot and pinned R dependency, as specified in the [reexecution instructions](publication-correspondence/author-example-reexecution.md). It cannot rerun the 2007 simulation.

The remaining source need is the original realized landscapes and basin positions, count/parameter/covariance/truth arrays, programs and output/error arrays, with terms permitting their intended use. The full paper and its published scenario settings are already available and are no longer missing inputs. A historical cohort still needs its own basin, chronology, taxon and transport support; the article alone supplies neither that support nor measured historical vegetation. No independent scientific endorsement, original figure reproduction or colleague reading outcome is recorded here.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Full Sugita 2007a theory, published scenario settings and error-method assumptions are compared with maintained consumers; the later exact WHH05 trace remains separate.

**Unsupported claim.** Original 2007 POLLSCAPE numerical reproduction or historical Nordic vegetation accuracy.

**Actual verification performed.** Source byte/hash and 13-page identity checks, full-text reading, selected appendix page-image comparison, and maintained-consumer inspection. No new model run.

**Remaining input or review.** Original realized landscapes, numerical covariance/count/truth/output arrays and usable source programs are absent. A proposed historical application needs separately supported physical and temporal inputs.

**Cause category.** data|assumption|comparability

**Consequence.** Published equations and later code parity do not establish original experiment reproduction or physical basin validity.

**Precise next acceptance route.** Authenticate original realized inputs, programs and numeric outputs for historical reproduction; use a separately declared supported profile for any new conditional reconstruction.

**Negative or refused result.** The printed B3 fixed-factor discrepancy is retained; unavailable original numerical arrays remain unevaluated.

**Matched denominator.** Original default simulations: 30 lakes, five default taxa and 1,000 grains per lake; later example: 17 sites, 184/425 supported site-bins and 31 taxa.

Retained evidence: [reports/science/reveals-theory-paper.md](reveals-theory-paper.md), [reports/science/publication-correspondence/author-example-site-replay.md](publication-correspondence/author-example-site-replay.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
