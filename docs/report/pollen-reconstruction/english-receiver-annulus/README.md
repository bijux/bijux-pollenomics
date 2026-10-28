# Conditional English receiving-disk sensitivity

This account changes only the local transport model for the previously exposed BECKHAM regional and LARKBARR local training pair. The author TW5 aggregate covers 1250–1750 BP and is labeled 1500. We retain the original exploratory 30-taxon mask excluding Filipendula (source fall speed 0.006 m/s). BECKHAM retains 699 of 741 counts after 42 exclusions; LARKBARR retains 553 of 563 after 10 exclusions. The separate 15-site cohort retains 20,573 of 20,732 after 159 exclusions; two empty windows remain outside that cohort. These denominators describe different populations.

The local receiver is a uniformly area-weighted disk of radius 80 m. Homogeneous terrestrial sources occupy annuli 81–500,500–1000 and 1000–10000 m. The 80–81 m guard strip and sources beyond 10000 m are outside this local calculation. The regional factor retains the historical lake profile with radius 150 m and cutoff 100000 m. This is an explicitly declared hybrid comparison; the unchanged historical account retains its zero middle-ring factor. It is neither original historical reproduction nor an authenticated physical landscape.

The [admitted mathematical capture](https://github.com/bijux/bijux-pollenomics/blob/main/data/method-certification/english-receiver-annulus/kernel-capture.json) retains 60 actual independent comparisons for 20 source fall speeds and three rings. Angular integration versus independent emitting/receiving-area quadrature agrees within 6.58e-14; the 64/128-order independent difference is at most 1.49e-12. These floating diagnostics are not rigorous interval bounds. The kernel interprets GPM survival as an isotropic stationary planar displacement law; it does not establish physical basin suitability.

All 64 conditional likelihood fits passed the 1e-7 simplex gap criterion, with maximum 9.9856027447e-8. Direct and maintained forward probabilities differ by at most 6.67e-16; independent objective and gap recomputation differs by at most 8.89e-16. Vertex condition numbers reach 50.489. An independently initialized optimizer's first nominal run reported success but failed its separate 1e-6 gradient-gap requirement. We retained that failure and changed its objective stopping tolerance from 1e-12 to 1e-14, keeping the acceptance unchanged; its next uniform-start gap was 1.4598545251e-7. Objective agreement alone did not override failed acceptance.

The nominal mean negative log likelihood is 1.012108241962, compared with 1.014024172453 under the historical local kernel. This difference describes fit to the same exposed training pollen. It supplies no independent vegetation accuracy or held-out model selection.

| Taxon | Nominal cover, % | PPE-only mean, % | PPE-only fifth/ninety-fifth percentiles, % |
| --- | ---: | ---: | ---: |
| Betula | 0.068608| 0.070288| 0.061300–0.082873|
| Calluna vulgaris | 2.108658| 2.104353| 2.027111–2.183154|
| Fagus sylvatica | 0.066599| 0.066567| 0.063374–0.069922|
| Fraxinus | 0.103246| 0.105943| 0.093447–0.119391|
| Plantago lanceolata type | 0.304384| 0.310503| 0.274796–0.353578|
| Poaceae | 97.294444| 97.286634| 97.187365–97.380744|
| Rumex acetosa type | 0.054061| 0.055703| 0.046941–0.063238|

The table shows the seven positive nominal components; the generated report retains all 30 taxa, including zero components and occasional small stochastic Alnus cover. One nominal PPE vector anchors the calculation. The 63 stochastic vectors use seed 20261002, source-declared diagonal covariance and whole-vector normal rejection. Each vector drives regional and local/background calculations together. Summary moments and percentiles exclude the nominal anchor. Historical regional percentage rounding is retained, with actual row sums 0.99998–1.00002.

These are PPE-only conditional sensitivities. They do not include pollen sampling, chronology, basin geometry, field cross-taxon covariance, source selection, parameter estimation or model discrepancy. The percentiles are not calibrated confidence coverage. Original source-use/redistribution authority, physical core/basin admission, measured vegetation, untouched confirmation and qualified external review remain separate requirements.

The maintained producer uses the existing source qualifier, exact source preparation and public shared-PPE likelihood interface. It reads the external 193-file author capsule and the separately admitted mathematical capture; it publishes only derived summaries. It does not rerun receiving-disk quadrature or overwrite the historical account. Failed publication attempts preserve their private artifact stage.

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_reconstruction.english_receiver_annulus \
  --repository . --source-root /path/to/private-source-store \
  --output artifacts/jobs/english-receiver-reproduction/source-products
```

The source-store parent must contain `landclim/author-reference`. Two clean maintained writer runs completed all 64 fits and produced byte-identical [compact reports](report.json) and [per-draw diagnostics](diagnostics.json). The independent numerical consumer and scalar review check the scientific calculations separately from this publication replay. Future reproductions must compare both derived files with these governed counterparts while preserving exact source and mathematical-capture identities. This technical owner admission leaves the external and ecological requirements above open.

## Probability law and metre convention

The conditional receiving-disk calculation has a normalized probability interpretation under its declared stationary, isotropic displacement assumption. This is a mathematical property of the chosen law; empirical pollen transport and paleobasin suitability still require separate evidence. Let `r` denote the numerical distance in metres, `beta = turbulence_parameter / 2 > 0`, and `a > 0` the coefficient of the existing GPM survival curve:

```text
S(r) = exp(-a * r^beta)
a = 4 * fall_speed / (turbulence_parameter * wind_speed * sqrt(pi) * diffusion_coefficient)
f_R(r) = a * beta * r^(beta - 1) * exp(-a * r^beta), r > 0
```

Since `S(0)=1` and `S(r)` tends to zero as `r` increases without bound, `f_R=-S'` integrates to one. With an independent uniform direction, its planar density is `h(r)=f_R(r)/(2*pi*r)`. This density may diverge at the origin when `beta < 2`, but the area element supplies the missing radial factor: the probability within radius `epsilon` is `1-exp(-a*epsilon^beta)`, which is finite and tends to zero. There is no point mass at zero. The change of variable `q=a*r^beta` gives `f_R(r) dr = exp(-q) dq`, so the hazard-coordinate density used by the quadrature is exactly normalized.

For a receiver at offset `x` from the basin center and a displacement of length `r`, landing within a centered circle of radius `t` means `x^2+r^2+2*x*r*cos(theta) <= t^2`. For positive `x*r`, define `c=(t^2-x^2-r^2)/(2*x*r)`. The fraction of uniform directions is one if `x+r <= t`, zero if `abs(x-r) >= t` after the full-circle case, and otherwise `1-acos(c)/pi`. These are the implemented circle branches; zero-offset/zero-distance cases have their direct geometric limits. Subtracting the inner-circle fraction from the outer-circle fraction gives a nonnegative annulus probability no greater than one.

A receiver uniformly distributed by area on a disk of radius `R` has radial density `2*x/R^2`. Therefore `z=x^2/R^2` is uniform on `[0,1]` and `x=R*sqrt(z)`. The maintained response is

```text
K = integral_z[0,1] integral_q[0,infinity]
      exp(-q) * (circle_fraction(outer, (q/a)^(1/beta), R*sqrt(z))
               - circle_fraction(inner, (q/a)^(1/beta), R*sqrt(z))) dq dz
```

Nonnegative integration proves `0 <= K <= 1`; disjoint concentric annuli conserve their combined probability. For `R=0`, the point response is exactly `S(inner)-S(outer)`. For a finite receiver the land-domain contract `0 <= R <= inner < outer` places the receiver disk inside the inner excluded circle. Consequently the angular integrand vanishes outside the distance range from `inner-x` to `outer+x`; the four geometric boundary hazards split the remaining integral. The implementation's exponential tail cutoff at `q=745` discards at most `exp(-745)` probability in exact arithmetic. This tail statement does not certify adaptive quadrature error: the returned quadrature estimate and the retained independent numerical comparisons remain nonrigorous diagnostics.

The source GPM coefficient is an empirical metre-based convention. In physical notation the exponent is `a * (distance / one_metre)^beta`; it must be dimensionless. An equivalent length unit with `u` metres per unit requires coefficient `a_new = a * u^beta` when using that unit's numerical distance. Rescaling distances alone changes the model. The source value `0.12` is not an SI diffusivity inferred by this calculation; the dimensional requirement on the exponent does not authenticate its physical derivation, wind regime or transfer between taxa/sites. In the finite-disk implementation `a=-log(S(1))` recovers the existing curve's coefficient and refuses an unresolved rounded survival, rather than fitting a separate law.

The law's normalization and these geometric identities establish the bounded conditional mathematical response. They do not establish the historical lake algorithm, a measured basin radius, independent vegetation accuracy or empirical uncertainty coverage. The original numerical capture and its failed predecessors remain unchanged.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
