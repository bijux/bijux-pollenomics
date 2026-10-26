# Separating nearby vegetation from regional background pollen

**Paper and question.** Sugita, S. (2007), “[Theory of quantitative reconstruction of vegetation II: all you need is LOVE](https://doi.org/10.1177/0959683607075838),” *The Holocene* **17**(2), 243–257. This second Landscape Reconstruction Algorithm (LRA) theory paper, commonly cited as **Sugita (2007b)**, asks how pollen from a smaller target basin can estimate **local vegetation** when part of its pollen arrived from farther away. We examine it because a local result requires a separate regional background estimate and a defensible spatial extent; a REVEALS regional fraction cannot simply be renamed local cover. [Indexed publisher citation and abstract](https://journals.sagepub.com/doi/10.1177/0959683607075838); [our LOVE interface account](reveals-love-interface/README.md).

**Scoped conclusion.** The supplied full paper describes LOVE's background correction, its **POLLSCAPE** tests, and an explicit backward method for selecting a feasible relevant source area. It does not provide the realized simulation inputs and complete numerical outputs required for exact historical reproduction. Our later interface check used a constructed ring and **no independently observed local vegetation**. It remains a separate calculation, including its negative fractions. [Sugita 2007b, pp. 245–256](https://doi.org/10.1177/0959683607075838); [interface result](reveals-love-interface/report.json).

## What LOVE estimates and needs

A small lake or peatland receives pollen from plants near the basin plus a **regional background**. Pollen counts are grain shares, while vegetation cover is area share; taxon pollen productivity and dispersal separate the two. **REVEALS** (“Regional Estimates of VEgetation Abundance from Large Sites”) estimates regional cover from large-site pollen. **LOVE** (“LOcal Vegetation Estimates”) subtracts the background contribution and estimates cover within a relevant local source area. **PPEs** are relative pollen productivity estimates; fall speed, basin type and radius, and chosen extent control the modeled deposition. [Later method profile](publication-correspondence/author-method-profile.md).

```text
large-site pollen → REVEALS regional cover → expected background pollen
                                             ↓
small-site pollen ───────────────────────→ LOVE subtraction
                                             ↓
                       estimated local cover within chosen source area
```

## Full source and the local/background equation

The supplied original-website package is complete as received: **15 PDF pages**, printed **243–257**, including Appendices A–C. Its filename is `sugita-2007-theory-of-quantitative-reconstruction-of-vegetation-ii-all-you-need-is-love.pdf`, **607,543 bytes**, SHA-256 `786ce8ffcefa9a952aacb702bd2e7b9dacf032cd67af14bc42cc4dae75df804b`. The visible bibliography ends within a reference; that observation does not turn the supplied complete package into an outstanding download request. No different publisher copy was checked. The original stays unchanged outside the repository; private derivative text and selected page images support this reading, without redistribution of the PDF. This replaces the earlier abstract-only access limitation.

In Equations (1)–(2), pollen loading is split at `Z_RSAP` into local and regional integrals. `R`, `Z_RSAP` and `Zmax` are distances from the basin **centre**; the local integral begins at the shore `R`. The modeled local quantity is a taxon's share of **distance-weighted plant abundance**, not automatically the unweighted area fraction in an arbitrarily drawn disk. Writing `c_i` for closed productivity-corrected local counts, Equations (6)–(7) give:

```text
c_i = (n_i / alpha_i) / sum_j(n_j / alpha_j)
Klocal_i = integral(R, Z_RSAP, g_i(z) dz)
Kregional_i = integral(Z_RSAP, Zmax, g_i(z) dz)
S_i = V_i Kregional_i / sum_j(V_j Klocal_j)
local_i = c_i (1 + sum_j(S_j)) - S_i
```

This is the algebra implemented by the maintained [analytical LOVE consumer](../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py). The source approximates the local total distance-weighted abundance using a homogeneous composition equal to regional cover when constructing `S_i`. This is a closure assumption for background scaling, not an independent observation that the reconstructed local vegetation equals regional vegetation. The paper requires a region-specific factor shared among study sites, neutral transport, constant productivity through time, circular basins, uniform wind directions and negligible within-basin assemblage variation; stream/runoff pollen, source-height differences and differential preservation are excluded. [Equations (1)–(7) and assumptions, pp. 244–246](https://doi.org/10.1177/0959683607075838).

Appendix A, p. 255, supplies the **Ring-Source** lake integral and Prentice bog/mire kernel, using wind **3 m/s**, `Cz=.12`, `Cy=.21`, `n=.25`. The later analytical interface's peatland deposition calls and source-compatible diameter/radius convention are therefore a separately named implementation profile, not a demonstrated original Ring-Source replication. Matching Equation (6) alone does not establish transport equivalence. All existing positive-PPE, support-axis and finite-range refusals remain applicable; a mathematically finite signed output is retained rather than clipped into a physical composition. [Later interface limits](reveals-love-interface/README.md); [signed equation and finite-domain checks](method-correspondence.md).

## Published experiments and uncertainty assumptions

| Source setting or result | Published scope |
| --- | --- |
| Default landscape | Matrix/three patches occupy `.40/.30/.20/.10`; mean patch areas `30±10`, `15±5`, `2±1 ha`. Five taxa have regional proportions `.423/.232/.144/.079/.122`. |
| Taxon/productivity/transport axis | Poaceae `1/.035`, Picea `1.77/.056`, Betula `8.94/.024`, Quercus `7.60/.035`, Fagus `6.73/.057`, with fall speeds in m/s. These are the 2007 table values, not the later 31-taxon inputs. |
| Spatial and count support | Nonoverlapping random patches in `60×60 km`; homogeneous mean vegetation beyond the plot to `400 km`; lakes in the central `10×10 km`; default **30 lakes** and **1,000 grains** per lake. |
| Landscape 2 openness | Three scenarios have regional Poaceae fractions `.333/.597/.882`; **90 simulated lakes per scenario**. The comparison uses vegetation within **1,000 m of shore**, with estimated relevant distances about `750/800/1,000 m`. |
| Landscape 3 | Patch type 1 mean area **10,000±2,000 ha**; default regional composition unchanged. The backward example uses 30 lakes of **50 m radius**. |
| PPE uncertainty construction | Separate **30 lakes of 20 m radius (0.13 ha)** feed `erv-v6.exe` to estimate the inverse-information covariance matrix. This differs from the REVEALS paper's 50 m covariance-estimation set. |
| Regional uncertainty construction | **30 simulated lakes of 800 m radius**, 1,000 grains each, plus PPE covariance enter REVEALS to derive regional-cover covariance. |

Tables 1–3 and methods on pp. 246–248 disclose these assumptions. Realized patch locations, pollen vectors, numerical covariance matrices and result arrays are not included. On p. 246, LOVE's standard errors combine counts, PPE variance/covariance and regional-cover variance/covariance through a **delta-method/Monte Carlo hybrid**, referring to the companion REVEALS appendix. The article supplies no complete joint draw law, Monte Carlo size or seed. Appendix B of this LOVE paper instead specifies **multinomial ERV likelihood and distance-based goodness-of-fit**, not a full covariance sampling recipe. Accordingly, marginal parameter SDs or supplied regional draws do not identify the original full uncertainty law or an ecological confidence interval. [Sugita 2007b, pp. 246–248, 255–256](https://doi.org/10.1177/0959683607075838); [companion error-law comparison](reveals-theory-paper.md#error-propagation-and-the-maintained-conditional-law).

## Backward inference preserves invalid fractions

Appendix C, p. 256, seeks the **minimum common** `Z_RSAP` satisfying the nonnegative local-composition condition for **all taxa at all sites simultaneously**. In the notation above, that condition is `S_i <= c_i (1 + sum_j S_j)`; with nonnegative corrected counts and regional factors and exact closure, it also makes each local fraction at most one. The appendix provides a bog analytical form and lake root-finding routes, including a Sugita (1993) approximation. These are model feasibility conditions, not proof of the true landscape extent. The main text explicitly says one site is insufficient for reliable backward modelling; several similarly sized sites and assessment of parameter errors are needed. [Appendix C and discussion, pp. 253–256](https://doi.org/10.1177/0959683607075838).

The two published backward examples each have **30 sites × five taxa = 150 predictions**. At an assumed **150 m from shore**, Landscape 1 has **32/150** out-of-range fractions and Landscape 3 **79/150**. The iterative examples reach zero invalid predictions around **700 m** and **3,700 m from shore**, respectively, using **5 m increments**. The appendix route gives **715 m** and **3,656 m from shore** as reported in the discussion. These source-reported results have not been independently reconstructed from original arrays. Figures use shore-based distances whereas the equations use centre-based radii; any implementation must preserve the basin-radius offset. [Figure 6 and pp. 252–254](https://doi.org/10.1177/0959683607075838).

Separately, Appendix B defines an ERV log-likelihood asymptote rule: a smooth curve's largest absolute difference within **±50 m** reaches **0.1**; for irregular curves a **300 m** moving-window slope is tested against zero. That rule requires observed/simulated surrounding vegetation and ERV fitting, and is not interchangeable with the backward feasibility rule. Neither rule is implemented merely by rejecting rings inside a basin or counting negative values for one later example. Existing ring diagnostics preserve evidence relevant to backward modelling, but they do not infer or validate a common relevant source area for a historical landscape. [Appendix B, pp. 255–256](https://doi.org/10.1177/0959683607075838).

## A constructed interface trace, separate from the 2007 experiment

Our [later LandClim author-source interface](reveals-love-interface/README.md) supplies **1,000 regional REVEALS draws** from **five pollen-supported sites**, on **31 taxa**, for the first time bin of grid 512. It feeds those draws, the source-aligned local `BROADOWN` pollen and declared transport inputs to **one constructed 200–300 m analytical LOVE ring**. `BROADOWN` also belongs to the regional cohort, so this is neither a held-out site nor an independent local-vegetation comparison. A placeholder regional-pollen argument is taxon-aligned for the interface but does not reconstruct the supplied regional-cover draws. [Exact machine receipt](reveals-love-interface/report.json); [source and replay route](reveals-love-interface/README.md).

The resulting tensor has **1,000 × 1 × 31 = 31,000** finite local fraction cells. **8,312** are negative; its minimum is **−0.4695300882**. For a concrete taxon row, *Calluna vulgaris* has mean local output **0.6135168974**, standard deviation across these draws **0.0385115602**, and **zero negative draws**. The standard deviation is variation over this constructed input draw set, not an ecological confidence interval. Because other taxa yield negative cover, the complete output is not a physically admissible vegetation composition. The calculation demonstrates that the regional tensor enters the local interface and its declared shape is enforced; it does not show that any inferred ring resembles real vegetation. [Tensor result](reveals-love-interface/report.json); [Calluna row](reveals-love-interface/taxon-summary.csv).

The [separate packaged LOVE example](analytical-love-ring-sensitivity/README.md) reinforces the spatial limit: among its first ten candidate rings, only **three** satisfy the source's local-basin boundary, and **16 of 30** valid taxon/ring cells are negative while **six** exceed one. Those are fixture outcomes for a later implementation, not a test or reproduction of Sugita's 2007 POLLSCAPE finding. Nor does a finite result determine the relevant source area for an actual past basin. [Exact ring rows](analytical-love-ring-sensitivity/ring-cover.csv).

## Evidence boundary and reproduction

The full article now establishes the source equations, published scenario denominators, uncertainty assumptions and backward-search definitions. The original numerical landscape/count/truth/output arrays and described source programs remain unavailable, so exact POLLSCAPE replay is still unsupported. The constructed interface uses a later author REVEALS release and current analytical LOVE implementation; the [2024 LOVE/LOVEoptim paper account](loveoptim-paper.md) concerns a further, separate simulated population and R tools. None supplies measured Nordic local vegetation. No new simulation or uncertainty experiment was run for this source comparison.

The retained [interface report](reveals-love-interface/report.json) and [taxon rows](reveals-love-interface/taxon-summary.csv) are readable without private author inputs. With the intact lawful author snapshot, a fresh run writes only to an absent repository `artifacts/` directory:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python reports/science/reveals-love-interface/replay.py \
  --repository . --source-root "$BIJUX_LANDCLIM_AUTHOR_REFERENCE" \
  --output artifacts/jobs/reveals-love-interface/reproduction
```

The producer authenticates the consumed source files and rejects a **999-draw** input before accepting the 1,000-draw tensor. This route replays our interface only, not the Sugita simulations. [Replay method](reveals-love-interface/README.md).

The remaining source need is the original realized landscape/basin/count inputs, numeric PPE and regional covariance arrays, local truth and output/error arrays, and usable programs with appropriate terms. The full paper, printed parameter tables and backward rule are available and no longer missing inputs. A historical application still needs matched chronology, basin geometry, taxon/parameter support and a declared uncertainty/dependence law; a local-accuracy claim additionally requires a suitable independent vegetation reference. No independent review or original figure reproduction is claimed.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Full Sugita 2007b local/background equations, published scenario settings and backward conditions are compared with the separate 1,000-draw constructed interface.

**Unsupported claim.** Original POLLSCAPE numerical replication, independently inferred historical source radius or local-cover accuracy.

**Actual verification performed.** Source byte/hash and 15-page identity checks, full-text reading, selected equation/appendix page-image comparison and maintained-consumer inspection. No new model run.

**Remaining input or review.** Original realized numerical inputs/covariance/truth/output arrays and usable programs remain absent; a historical application needs its own supported physical and temporal inputs.

**Cause category.** data|assumption|comparability

**Consequence.** Preserve signed diagnostics; do not normalize invalid cover into ecological truth or equate single-ring validity with the common source-area solution.

**Precise next acceptance route.** Authenticate original numerical scenarios for reproduction, or use a separately declared supported historical/conditional profile. Independent vegetation is needed for an accuracy comparison.

**Negative or refused result.** Constructed interface retains 8,312 negative of 31,000 finite cells; original numerical arrays remain unevaluated.

**Matched denominator.** Original backward examples: 30 sites × five taxa = 150 predictions each; later interface: 1,000 regional draws × one ring × 31 taxa.

Retained evidence: [reports/science/reveals-love-interface/report.json](reveals-love-interface/report.json), [reports/science/analytical-love-ring-sensitivity/report.json](analytical-love-ring-sensitivity/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
