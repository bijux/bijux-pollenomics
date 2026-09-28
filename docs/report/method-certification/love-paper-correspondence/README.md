# LOVE paper method correspondence

[Theuerkauf and Couwenberg (2024)](https://doi.org/10.3390/quat7020018)
describe analytical LOVEr and optimized LOVEoptim using a simulated landscape.
The full article text was inspected through a public PDF copy with SHA-256
`3336b5b6450b89d97b6e52f18b42090333091bf355a3f4715676215e2b18cc3e`;
the publisher endpoint returned HTTP 429/403 during this review. The paper's
data availability statement points to DISQOVER functions, without identifying
a deposited simulation input bundle. No supplementary simulation bundle was
identified in the accessible article. The [local source identity
receipt](../disqover-source-identity/README.md) establishes the exact later
DISQOVER 0.9.14 archive used by our R oracle; the article accessed DISQOVER in
February 2024, whereas that archive was packaged in January 2026. Archive
parity therefore does not establish the exact software version behind Figure 2.

| Paper method or assumption | Current executable evidence | Scope of correspondence |
| --- | --- | --- |
| Small-site pollen deposition combines local and regional contributions. | [Optimized forward objective](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/optimized.py) and [analytical subtraction](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py). | Source equations have bounded R/Python parity; no ecological truth is inferred. |
| Analytical LOVE assumes comparable total distance-weighted abundance among small sites and local vegetation homogeneous with the regional composition. | [Analytical ring sensitivity](../analytical-love-ring-sensitivity/README.md) retains negative and above-one estimates rather than imposing cover constraints. | These are paper-stated limitations, not assumptions validated for Nordic basins. |
| LOVEoptim fits ring-specific local cover by log-Euclidean pollen mismatch using `RcppDE::DEoptim`. | [Common objective and solution-quality study](../optimizer-solution-quality/README.md) uses installed RcppDE and the Python optimizer on identical declared objectives. | Candidate evaluations agree; achieved objective quality is bounded, while search paths and stopping events differ. |
| Regional and local count/PPE perturbations are repeated for uncertainty. | [Paired LOVE draw study](../paired-love-draws/README.md) holds explicit local count/PPE draws equal across R and Python; [source compatibility](../../../../packages/bijux-pollenomics-lra/docs/reference/source-compatibility.md) records the optimized wrapper's sampled-but-unused local PPE. | The analytical supplied-draw calculation is checked. The article's general uncertainty description does not certify coverage, and the optimized source's local PPE behavior is narrower than that description implies. |
| Ring land-cover fractions can represent lakes, wetlands and terrestrial area separately. | [Forward input profiles](../../../../packages/bijux-pollenomics-lra/docs/reference/forward-preparation.md) name source and revised fraction rules; source dimensional refusals and revised ring/taxon tests are explicit. | No paper landscape ring raster or site-specific geometry has been admitted. |
| Paper simulation uses BÜK200 map units, one regional lake, eight artificial ponds (diameters about 10, 50, 100 and 200 m), a 100 km source extent, LSM unstable dispersal and 100 model runs. | [Dispersal and parity map](../../../../packages/bijux-pollenomics-lra/docs/reference/parity.md) covers the LSM kernel and core LOVE equations. | The published Tables 1 and 2 give map-unit compositions and ten taxon parameters, but the precise vector map extraction, pond placements, ring-area arrays, realized pollen inputs and random draws needed for Figure 2 are not supplied by the article. |
| Paper evaluates true-versus-reconstructed ring cover with RMSE and discusses a 100–500 m range for its simulated landscape. | [Ring sensitivity](../analytical-love-ring-sensitivity/README.md) reports source-compatible numerical behavior only. | The paper's Figure 2 RMSE and preferred radius cannot be reproduced or transferred to Nordic sites without its spatial truth and ring inputs. |

The accessible article supports an assumption and equation mapping. The
[original R reference](../original-r-reference/README.md),
[paired local draws](../paired-love-draws/README.md) and
[optimizer comparison](../optimizer-solution-quality/README.md) provide actual
bounded numerical tests on declared inputs. Reproducing the paper's eight-site
Figure 2 requires the author's exact landscape extraction, site and ring
geometry, pollen simulation inputs or code, and stochastic settings. The
article tables alone cannot determine those numerical outputs; digitizing the
figure would not establish a simulation replay. This paper-example obligation
remains open with that exact source input requirement.
