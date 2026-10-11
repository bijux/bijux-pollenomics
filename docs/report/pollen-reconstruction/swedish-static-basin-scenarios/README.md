# Swedish pollen scenarios with declared static basins

The original LandClim metadata contains 84 Swedish rows. A coordinate,
site-alias and native-core search of the retained Neotoma capture found
leads for 58 rows, covering 59 datasets and 4,548 distinct native samples.
The retained capture contains 200 sites and 209 datasets; the other 26 rows
require further source discovery. A candidate match remains separate from
an authenticated historical prepared input.

This account executes new conditional reconstructions for four source-linked
lake cores using [declared assumptions](assumptions/protocol.json). Each
included sample explicitly reports every taxon on its small per-core panel.
The [machine report](report.json) retains derived core-window counts, selected
calibrated chronologies, count denominators and exact source-support hashes.
Individual raw sample/depth/age records and their native identifiers stay in
the local source-bound captures until their publication scope is admitted.

| Core / native dataset | Literal panel | Included / native samples | Occupied windows | Panel NISP / all reported pollen NISP in included samples |
| --- | --- | ---: | ---: | ---: |
| Abborrtjärnen / 19913 | Betula; Pinus sylvestris | 106 / 107 | 22 | 105,525 / 128,593 (82.06%) |
| Bökesjön / 54001 | Betula; Fraxinus; Ulmus | 50 / 52 | 13 | 11,295 / 40,999 (27.55%) |
| Bussjösjön / 53995 | Betula; Ulmus | 60 / 69 | 19 | 6,848 / 63,678 (10.75%) |
| Lake Tibetanus / 53980 | Pinus sylvestris; Poaceae | 45 / 45 | 23 | 11,286 / 43,851 (25.74%) |

The four outcomes use 261 of 273 source samples in 77 occupied core-windows.
Six source ages fall outside the declared nonnegative windows and six
Bussjösjön samples lack an explicit Ulmus datum. All 261 included point ages
lack raw younger/older bounds. Missing bounds do not imply exact ages or
provide a chronology posterior. The source chronologies are calibrated
radiocarbon years BP, with the AD 1950 datum documented in
[Neotoma manual section 7.5](https://open.neotomadb.org/manual/database-design-concepts.html).
Collection and publication dates do not reset zero BP.

Each metadata radius is interpreted as a fixed circular receiving disk:
98 m for Abborrtjärnen, 80 m for Bökesjön, 69 m for Bussjösjön and 100 m for
Tibetanus. The homogeneous land annulus extends from that disk edge to
100 km. The maintained
[physical receiver response](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/receiver_annulus.py)
uses the source GPM convention with fall speed and wind in m/s, distance
in metres, turbulence parameter 0.25 and empirical transport coefficient
0.12. That coefficient is not an SI diffusivity in m²/s. Uniform disk
reception, stationary isotropic transport and a fixed basin are scenario
assumptions. Tibetanus retains the metadata-versus-native elevation
disagreement (161 versus 568 m) and approximately 398 m coordinate separation.

The [conditional inverse correction](../../../../packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py)
closes weights proportional to each count divided by its physical response
and PPE. Public LandClim PPE standard deviations supply a diagonal covariance
with all off-diagonal covariances assumed zero. Conditional standard errors
combine multinomial counting variance and this assumed PPE covariance.
Chronology, basin, transport and site-selection uncertainty remain outside
those standard errors. The native source names match the public parameter
strings literally; scientific parameter transfer is explicitly assumed and
does not close the existing source-concept reviews.

For radius $r$, regional extent $L$, fall speed $v_i$, wind $u$,
empirical transport coefficient $D$ and turbulence parameter $\gamma$,
the displacement survival is

$$
S_i(d)=\exp(-a_i d^{\gamma/2}),\qquad
a_i=\frac{4v_i}{\gamma u\sqrt{\pi}D}.
$$

The physical response is the uniform disk average of the probability that
an isotropic displacement lands in the declared land annulus. An equivalent
circle-overlap integral used in independent verification is

$$
K_i=\int_0^{\infty} e^{-q}
\frac{A(r,L,d_i(q))-A(r,r,d_i(q))}{\pi r^2}\,dq,
\qquad d_i(q)=(q/a_i)^{2/\gamma},
$$

where $A(r,b,d)$ is the overlap area of circles of radii $r$ and $b$
whose centers are separated by $d$. For a pooled core-window count vector,
the estimand is the corrected composition on its declared panel:

$$
b_i=(K_i\mathrm{PPE}_i)^{-1},\quad
W=\sum_j b_j n_j,\quad c_i=b_i n_i/W.
$$

The count Jacobian is $J_{ij}=\delta_{ij}b_i/W-c_i b_j/W$, and the PPE
Jacobian is $H_{ij}=c_i(c_j-\delta_{ij})/\mathrm{PPE}_j$. With panel
total $N$ and direct fraction $f=n/N$, the reported delta covariance is

$$
C_c=J\,N[\operatorname{diag}(f)-ff^T]\,J^T
   +H\,\operatorname{diag}(\mathrm{SD}_{\mathrm{PPE}}^2)\,H^T.
$$

Pooling within a window assumes a common conditional panel composition;
variation between source samples is not independently estimated. The closed
panel composition and this conditional covariance are the numerical targets.

For example, the Tibetanus 0–100 cal BP window contains one source point
and pooled counts of 111 Pinus sylvestris and 39 Poaceae grains. Its two-taxon pollen fractions are 74% and
26%; the baseline corrected fractions are 29.21299% and 70.78701%, each with
conditional standard error 3.93339 percentage points. This panel represents
150 of that window's 1,024 reported pollen grains. These fractions describe
the declared panel, not total vegetation cover. The four panels have
different axes and cannot be pooled or used to compare vegetation between
cores.

Halving and doubling radius change area by factors 0.25 and 4. Across the
retained windows, the largest corresponding cover changes are 0.27–0.56
percentage points. Wind scenarios at 2 and 4 m/s produce largest changes of
1.37–5.44 percentage points. The report retains every scenario and a
zero-PPE-variance comparison. These comparisons describe assumption
sensitivity; they are not probability intervals or independent validation.

The original Bussjösjön Betula/Poaceae attempt is preserved in
`negative_predecessors`: zero of 69 samples supported that literal panel.
The source actually uses `Poaceae undiff. (<40 µm)`, and its mapping was not
silently changed. A separate Betula/Ulmus successor admits 60 samples using
explicit source observations. The other three successful outcomes were
reused unchanged.

The [actual run receipts](execution/actual-runs.json) preserve the two native
exit-zero captures, source-custody checks, resource scope and original receipt
identities. Their scientific source candidate is
`5fe91a5c64cdae35eeddc77e529e6c0e44eb529c` with the explicitly admitted
covariance source overlay SHA-256
`4dde1a078ae7d57f3c93e93fa8cc4e73756f551e774d78aadb606fa47c483448`.
The machine report separately records its subsequent canonical admission;
later Git history does not replace the actual run identity. Counts, cover
closure, the PPE/count covariance decomposition and measured-taxon refusals
were checked during execution. Independent scalar inverse/count/PPE checks covered 385 cases and 77
zero-PPE controls. A separate analytic circle-overlap integral checked 55
physical response factors, with largest absolute difference 7.50 × 10⁻¹¹
from the maintained disk/angle quadrature. Exact source counts, window
assignment, exclusions and missing bounds were also independently checked;
the [scoped mathematical review](execution/independent-math-review.json)
retains these results. This account supplies neither historical LandClim replay,
a complete 31-taxon reconstruction, native R parity for these scenarios nor
independent vegetation accuracy.

The [source identities](inputs/source-identities.json) name the original
LandClim workbook/parameter bytes and native Neotoma parts. Data contributors
are Thomas Giesecke (Abborrtjärnen), Marie-José Gaillard-Lemdahl (Bökesjön), Joachim Regnéll
(Bussjösjön) and Lena Barnekow (Tibetanus), as retained in the actual source
dataset records. The European Pollen Database curates these records; exact
dataset DOI strings remain in the report, including the Neotoma and EPD
identities where the source supplies both. The
[official Neotoma policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
states CC BY 4.0 use for available data with attribution to Neotoma, the
constituent database and original contributors/publications. Historical
LandClim R/NR flags and the separate rights/source decisions are preserved in
[source reconciliation](assumptions/source-reconciliation.json). No private
Rootsi workbook or author LUT is used by these scenarios, and this account
does not grant publication rights for those separate sources. Complete
primary-publication attribution and any actual access restriction remain
publication follow-through.

![Direct panel pollen and conditional corrected composition](figures/panel-comparison.png)

The [167 plotted core-window-taxon points](figures/panel-comparison.csv) come from the baseline profiles of the retained numerical captures. Open markers show direct pollen panel fractions; filled markers and bars show corrected fractions and conditional one standard error. Each core has its own taxon panel. The actual R Quartz capture and layout inspection are recorded in [figure-capture.json](execution/figure-capture.json); this figure supplies no numerical R/Python parity or reader-feedback claim.

The [maintained producer capture](execution/maintained-producer-capture.json) records actual independent reference and replay directories with identical report bytes and exact agreement with the original scoped numerical captures. The [observed import closure](execution/observed-imports.json) and [capture receipt](execution/import-observation-capture.json) retain 59 actual project module origins from a separate cold import and callable observation. That observation establishes import source identities; it does not trace every dynamic scientific file read or establish platform completeness.
