# Reference implementation scope

## Primary parity target

The exact source reference for `bijux-pollenomics-lra` 0.1.0 is the supplied
`disqover` 0.9.14 archive. It is the reference package that contains the paired
implementation surface required here:

- regional REVEALS (`REVEALS`, `REVEALSinR`),
- analytical local LOVE (`lov`, `LOVEr`),
- forward-optimisation LOVE (`LOVEoptim`, `calK`, `tf`, `logeuclidean`), and
- the dispersal/deposition kernels used by both stages.

The archive is retained unchanged in `vendor/`, is identified by SHA-256 in all
run manifests, and is the only package accepted by the exact live-R oracle.

## Secondary R implementation checked

Petr Kuneš's `LRA` 0.1.2 package is a distinct REVEALS implementation for one
or multiple sites. Its public namespace exports `KPf` and `REVEALS` and imports
`disqover`; it does not export a LOVE implementation. Its analytical
variance/covariance and multi-site bootstrap workflow is therefore a useful
secondary REVEALS reference, but it cannot serve as the complete REVEALS + LOVE
oracle requested for this package.

The separate `run_reveals_multisite` workflow now implements the historical
Petr Kuneš aggregation profile. The [tagged R comparison](../../../../docs/report/method-certification/petrkunes-r-comparison/README.md)
checks single and heterogeneous multi-site inputs with shared bootstrap draws.
It remains a distinct profile from DISQOVER's `REVEALSinR` and from
`run_lra_series`, which pairs exact age/depth/time coordinates. Each regional
LOVE input still requires an explicitly selected regional pollen sample or
qualified regional cover draws.

## Why the distinction matters

The name “REVEALS” covers related implementations with different input shapes,
uncertainty calculations, and aggregation behavior. Parity is meaningful only
when the package, version, function, inputs, stochastic draws, and numerical
backend are identified. The validation reports therefore avoid a generic claim
of parity with every R implementation named LRA or REVEALS.
