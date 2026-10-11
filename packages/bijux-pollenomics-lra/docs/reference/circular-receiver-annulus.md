# Circular receiver response to a land annulus

`bijux_pollenomics_lra.dispersal.receiver_annulus.circular_receiver_annulus`
computes a separately declared conditional geometry model. The receiver is a
uniformly weighted circular disk of radius `R`. A homogeneous land annulus has
inner radius `a` and outer radius `b`, with `0 <= R <= a < b`. All radii are in
metres. The supplied fall speed, diffusion coefficient, turbulence parameter
and wind speed determine the existing GPM radial survival function `S(d)`.

The model interprets that survival function as a stationary isotropic radial
displacement law. Its planar density is `-S'(d)/(2*pi*d)`. The response is the
average, over receiving disk area, of that density integrated over the complete
emitting land annulus. It is a dimensionless factor multiplying homogeneous
cover and PPE in a caller's deposition model. It does not model partial land
coverage, directional wind, uneven receiver weighting or changing PPE.

The implementation integrates radial survival hazard and angular annulus
fractions, then averages over disk area. A point receiver (`R = 0`) reduces
exactly to `S(a) - S(b)`. Disjoint adjacent annuli add to the response of their
union. Tests independently integrate emitting and receiving area using
Gauss-Legendre quadrature and check this additivity.

The returned `AnnulusResponse` contains `factor` and
`estimated_absolute_error`. The latter combines adaptive quadrature estimates;
it is not a rigorous error bound. Integration warnings, unresolved survival,
invalid geometry and unsupported iteration limits refuse execution. Absolute
and relative tolerances and the bounded quadrature limit are explicit inputs.

For the declared example `R = 80`, `a = 81`, `b = 500`, fall speed `0.03`,
diffusion coefficient `0.12`, turbulence parameter `0.25` and wind speed `3`,
the response is approximately `0.0973099332655`. The adjacent `500–1000` metre
annulus contributes approximately `0.0270109855238`. These are mathematical
examples under the stated assumptions, without a fitted physical basin or
vegetation accuracy claim.

This function does not change the existing lake or peatland algorithms, their
facade parameter domains, or optimized LOVE defaults. It does not establish
correspondence to a historical lake algorithm, original paper results, physical
core admission or ecological validity. Hosts must separately establish source
identity, scientific suitability and permission for their application.
