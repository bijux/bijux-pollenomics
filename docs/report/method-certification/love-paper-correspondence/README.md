# LOVE paper method correspondence

[Theuerkauf and Couwenberg (2024)](https://doi.org/10.3390/quat7020018)
describe analytical LOVEr and optimized LOVEoptim using a simulated landscape.
The exact 1,097,851-byte article PDF (SHA-256
`3336b5b6450b89d97b6e52f18b42090333091bf355a3f4715676215e2b18cc3e`)
was acquired from the [publisher PDF](https://mdpi-res.com/d_attachment/quaternary/quaternary-07-00018/article_deploy/quaternary-07-00018.pdf).
It is byte-identical to the formerly retained mirror copy. The article prints
copyright 2024 by Martin Theuerkauf and John Couwenberg and the
[CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/) on page 1.
The public source packet under `data/love/paper/` binds the PDF and its
separately native-qualified text derivative. The table producer derives 151
numeric cells from printed page 6, including the wrapped Tilia header;
the retained table is the genuine source-backed producer output, checked against all
151 formerly transcribed constants. Ordinary configured-owner reference/replay
proof remains a separate output-custody requirement.
This establishes public article identity and printed constants only. The paper's
data availability statement points to DISQOVER functions, without identifying
a deposited simulation input bundle. No supplementary simulation bundle was
identified in the accessible article. The [local source identity
receipt](../disqover-source-identity/README.md) establishes the exact later
DISQOVER 0.9.14 archive used by our R oracle; the article accessed DISQOVER in
February 2024, whereas that archive was packaged in January 2026. Archive
parity therefore does not establish the exact software version behind Figure 2.

The retained [published parameter tables](paper-parameter-tables.json) are generated
by `bijux_pollenomics_dev.source_completion.love.paper_tables` from the exact
publisher PDF, its qualified text derivative and their source manifest. Its
121 map-unit fractions from Table 1 and 30 fall-speed, PPE and PPE SD constants
from Table 2 reproduce all 151 previously transcribed numeric cells on page 6.
The retained source metadata now identifies the public article and the
byte-authenticated extraction, rather than a private mirror transcription. Each map-unit row sums to
one, and every printed PPE SD is 10% of its PPE. Table 2 does not state a
fall-speed unit, so the transcription does not assign one. These constants
resolve a bounded paper input; they do not identify the spatial extent of
each map unit, the pond placements or the random realizations behind Figure 2.

The [source-parameter comparison](source-parameter-correspondence.json) is a
fresh execution of the maintained verifier against that genuine public-source
table and the pinned packaged DISQOVER
`LOVEexampleParams.json`. All 30 fall-speed, PPE and PPE SD values agree
exactly by row position, with zero residuals. The refreshed report changes
only its table input receipt; its comparison rows and scope are unchanged.
Nine labels agree exactly; the paper prints
`Grasses` where the package prints `Gras`. This is a numeric source
correspondence with an explicit label difference, not evidence that the 2024
simulation ran the later pinned package version. The pinned package example
has only `local` and `regional` pollen rows and one 36-ring layout reaching
100,000 distance units. Those inputs do not encode the article's eight
artificial ponds or their realized pollen/draws. Check the producer output
byte for byte against the governed JSON from the repository root with
`python3 docs/report/method-certification/love-paper-correspondence/verify.py --repository . --check`.
Use `--output artifacts/method-certification/love-paper-source-parameter-replay.json`
instead when an isolated replay file is needed; the output must be absent.
The configured comparison adapter
`bijux_pollenomics_dev.source_completion.love.parameter_correspondence` invokes
this same fixed verifier. Separate genuine reference/replay calls for both
configured owners are required before output-ownership acceptance. Neither
these constants nor their agreement supplies a Figure 2 simulation replay.

The same pinned DISQOVER 0.9.14 archive's
`disqover/man/LOVEexampleRings.Rd` (member SHA-256
`43c8f7166a88d35b609d8772bab2c5830dc1e76f97ff5d4e9d6fa2a5fd0fc5ad`)
describes its example as simulated from **BÜK300**. The retained 2024 paper
describes its eight-site Figure 2 simulation as using **BÜK200**. We retain
those source descriptions as a difference in stated map basis; the example
parameter match does not establish that either archive example contains the
paper's Figure 2 landscape or random runs.

| Paper method or assumption | Current executable evidence | Scope of correspondence |
| --- | --- | --- |
| Small-site pollen deposition combines local and regional contributions. | [Optimized forward objective](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/optimized.py) and [analytical subtraction](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py). | Source equations have bounded R/Python parity; no ecological truth is inferred. |
| Analytical LOVE assumes comparable total distance-weighted abundance among small sites and local vegetation homogeneous with the regional composition. | [Analytical ring sensitivity](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/analytical-love-ring-sensitivity/README.md) retains negative and above-one estimates rather than imposing cover constraints. | These are paper-stated limitations, not assumptions validated for Nordic basins. |
| LOVEoptim fits ring-specific local cover by log-Euclidean pollen mismatch using `RcppDE::DEoptim`. | [Common objective and solution-quality study](../optimizer-solution-quality/README.md) uses installed RcppDE and the Python optimizer on identical declared objectives. | Candidate evaluations agree; achieved objective quality is bounded, while search paths and stopping events differ. |
| Regional and local count/PPE perturbations are repeated for uncertainty. | [Paired LOVE draw study](../paired-love-draws/README.md) holds explicit local count/PPE draws equal across R and Python; [source compatibility](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/docs/reference/source-compatibility.md) records the optimized wrapper's sampled-but-unused local PPE. | The analytical supplied-draw calculation is checked. The article's general uncertainty description does not certify coverage, and the optimized source's local PPE behavior is narrower than that description implies. |
| Ring land-cover fractions can represent lakes, wetlands and terrestrial area separately. | [Forward input profiles](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/docs/reference/forward-preparation.md) name source and revised fraction rules; source dimensional refusals and revised ring/taxon tests are explicit. | No paper landscape ring raster or site-specific geometry has been admitted. |
| Paper simulation uses BÜK200 map units, one regional lake, eight artificial ponds (diameters about 10, 50, 100 and 200 m), a 100 km source extent, LSM unstable dispersal and 100 model runs. | [Dispersal and parity map](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-lra/docs/reference/parity.md) covers the LSM kernel and core LOVE equations. | The published Tables 1 and 2 give map-unit compositions and ten taxon parameters, but the precise vector map extraction, pond placements, ring-area arrays, realized pollen inputs and random draws needed for Figure 2 are not supplied by the article. |
| Paper evaluates true-versus-reconstructed ring cover with RMSE and discusses a 100–500 m range for its simulated landscape. | [Ring sensitivity](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/analytical-love-ring-sensitivity/README.md) reports source-compatible numerical behavior only. | The paper's Figure 2 RMSE and preferred radius cannot be reproduced or transferred to Nordic sites without its spatial truth and ring inputs. |

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
