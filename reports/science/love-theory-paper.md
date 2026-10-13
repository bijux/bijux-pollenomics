# Separating nearby vegetation from regional background pollen

**Paper and question.** Sugita, S. (2007), “[Theory of quantitative reconstruction of vegetation II: all you need is LOVE](https://doi.org/10.1177/0959683607075838),” *The Holocene* **17**(2), 243–257. This second Landscape Reconstruction Algorithm (LRA) theory paper, commonly cited as **Sugita (2007b)**, asks how pollen from a smaller target basin can estimate **local vegetation** when part of its pollen arrived from farther away. We examine it because a local result requires a separate regional background estimate and a defensible spatial extent; a REVEALS regional fraction cannot simply be renamed local cover. [Indexed publisher citation and abstract](https://journals.sagepub.com/doi/10.1177/0959683607075838); [our LOVE interface account](reveals-love-interface/README.md).

**Scoped conclusion.** In the publisher abstract, Sugita's **POLLSCAPE simulations** support background-pollen prediction and report better local-cover estimates from LOVE than from pollen percentages. They also support a backward-modeling approach to the **relevant source area of pollen**, which remains hard to estimate for past landscapes. These are simulation claims. Our later numerical interface check used a constructed ring and **no independently observed local vegetation**; it does not reproduce the 2007 experiments. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075838); [interface result](reveals-love-interface/report.json).

## What LOVE estimates and needs

A small lake or peatland receives pollen from plants near the basin plus a **regional background**. Pollen counts are grain shares, while vegetation cover is area share; taxon pollen productivity and dispersal separate the two. **REVEALS** (“Regional Estimates of VEgetation Abundance from Large Sites”) estimates regional cover from large-site pollen. **LOVE** (“LOcal Vegetation Estimates”) subtracts the background contribution and estimates cover within a relevant local source area. **PPEs** are relative pollen productivity estimates; fall speed, basin type and radius, and chosen extent control the modeled deposition. [Later method profile](publication-correspondence/author-method-profile.md).

```text
large-site pollen → REVEALS regional cover → expected background pollen
                                             ↓
small-site pollen ───────────────────────→ LOVE subtraction
                                             ↓
                       estimated local cover within chosen source area
```

The abstract specifies regional input cover over **10⁴–10⁵ km²** from large sites of at least **10² ha**, plus target-site counts, PPEs and a relevant local area. It provides no simulated-basin count, exact radii, numeric errors or full backward-modeling algorithm. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075838); [companion REVEALS account](reveals-theory-paper.md).

## A constructed interface trace, separate from the 2007 experiment

Our [later LandClim author-source interface](reveals-love-interface/README.md) supplies **1,000 regional REVEALS draws** from **five pollen-supported sites**, on **31 taxa**, for the first time bin of grid 512. It feeds those draws, the source-aligned local `BROADOWN` pollen and declared transport inputs to **one constructed 200–300 m analytical LOVE ring**. `BROADOWN` also belongs to the regional cohort, so this is neither a held-out site nor an independent local-vegetation comparison. A placeholder regional-pollen argument is taxon-aligned for the interface but does not reconstruct the supplied regional-cover draws. [Exact machine receipt](reveals-love-interface/report.json); [source and replay route](reveals-love-interface/README.md).

The resulting tensor has **1,000 × 1 × 31 = 31,000** finite local fraction cells. **8,312** are negative; its minimum is **−0.4695300882**. For a concrete taxon row, *Calluna vulgaris* has mean local output **0.6135168974**, standard deviation across these draws **0.0385115602**, and **zero negative draws**. The standard deviation is variation over this constructed input draw set, not an ecological confidence interval. Because other taxa yield negative cover, the complete output is not a physically admissible vegetation composition. The calculation demonstrates that the regional tensor enters the local interface and its declared shape is enforced; it does not show that any inferred ring resembles real vegetation. [Tensor result](reveals-love-interface/report.json); [Calluna row](reveals-love-interface/taxon-summary.csv).

The [separate packaged LOVE example](analytical-love-ring-sensitivity/README.md) reinforces the spatial limit: among its first ten candidate rings, only **three** satisfy the source's local-basin boundary, and **16 of 30** valid taxon/ring cells are negative while **six** exceed one. Those are fixture outcomes for a later implementation, not a test or reproduction of Sugita's 2007 POLLSCAPE finding. Nor does a finite result determine the relevant source area for an actual past basin. [Exact ring rows](analytical-love-ring-sensitivity/ring-cover.csv).

## Evidence boundary and reproduction

The indexed publisher abstract supplies the original theory and qualitative simulation findings. A lawful full 2007 article or original simulation scenario table was not located in the retained packet examined here, and direct publisher page retrieval did not yield full text. Thus the paper's exact simulation denominators, equations and result rows are **not evaluated**. The constructed interface uses a later author REVEALS release and current analytical LOVE implementation; the [2024 LOVE/LOVEoptim paper account](loveoptim-paper.md) concerns a further, separate simulated population and R tools. None supplies measured Nordic local vegetation. [Publisher abstract](https://journals.sagepub.com/doi/10.1177/0959683607075838); [interface account](reveals-love-interface/README.md).

The retained [interface report](reveals-love-interface/report.json) and [taxon rows](reveals-love-interface/taxon-summary.csv) are readable without private author inputs. With the intact lawful author snapshot, a fresh run writes only to an absent repository `artifacts/` directory:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python reports/science/reveals-love-interface/replay.py \
  --repository . --source-root "$BIJUX_LANDCLIM_AUTHOR_REFERENCE" \
  --output artifacts/jobs/reveals-love-interface/reproduction
```

The producer authenticates the consumed source files and rejects a **999-draw** input before accepting the 1,000-draw tensor. This route replays our interface only, not the Sugita simulations. [Replay method](reveals-love-interface/README.md).

The **unsent source request** is for a lawful full Sugita (2007b) paper and original POLLSCAPE scenario definitions, target and regional basin identities/geometries, pollen counts, regional truth/REVEALS vectors, PPE and fall-speed tables, background-pollen terms, relevant-source-area search rule, local vegetation truth and uncertainty/error rows, plus usable source permissions. The **unsent qualified-review request** is to decide for each proposed historical target whether its regional cohort is independent and temporally comparable, its basin and local-area geometry are defensible, its taxon/parameter support is adequate, and a measured local vegetation reference exists before any accuracy claim. No independent review, original figure reproduction or colleague reading outcome is claimed.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Sugita 2007b abstract-level local-background theory and separate 1,000-draw constructed interface are accounted for.

**Unsupported claim.** Original POLLSCAPE numerical replication or independent local-cover accuracy.

**Actual verification performed.** Retained publisher abstract and later interface/ring receipts are described; index did not rerun 2007 simulation.

**Remaining input or review.** Original Sugita 2007b full paper/scenario rows are not retained; constructed later interface and packaged rings cannot reproduce the original POLLSCAPE experiment or validate local vegetation. Resolver: Original paper/scenario custodian and qualified LOVE method reviewer Reopen when: Lawful original scenario/count/geometry/parameter/truth packet allows exact experiment account and separate ecological comparison.

**Cause category.** data|access/rights|comparability

**Consequence.** Do not present constructed fixture as Sugita 2007b result or normalize invalid cover into ecological truth.

**Precise next acceptance route.** Lawful original scenario/count/geometry/parameter/truth packet allows exact experiment account and separate ecological comparison. Then update reports/science/paper-accounts.md.

**Negative or refused result.** Constructed interface has 8,312 negative of 31,000 finite cells; original experiment error values not available.

**Matched denominator.** Later interface: 1,000 regional draws × one ring ×31 taxa; original abstract has no exact scenario rows.

Retained evidence: [reports/science/reveals-love-interface/report.json](reveals-love-interface/report.json), [reports/science/analytical-love-ring-sensitivity/report.json](analytical-love-ring-sensitivity/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 77dafd427441a48732795e1a0e3c7d9105781ee8fda4958b8703f98a8f964503 -->
<!-- scientific-authored-source-sha256: c6c43f07ac3d550a72360a5cf1aee434eb45c72cf70ebe36aaccbe14d4e8864f -->
<!-- scientific-verification-and-limits:end -->
