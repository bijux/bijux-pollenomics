# What a newly evaluated Swedish lake showed for observed-pollen prediction

We evaluated the fixed 16-label observed-pollen predictors at [Lake
Sämbosjön](../../docs/report/regions/nordic/sambosjon-direct-pollen/README.md),
a Swedish Neotoma/EPD physical site absent from the earlier Swedish and Nordic
target studies. The entire site and its core were excluded from 84 training
physical sites. We froze 66 predictions for 22 age bins before target scoring.
No bin was refused or failed.

The primary fixed inverse-distance-squared predictor had equal-bin pollen
fraction MAE **0.022991** and Hellinger distance **0.184176**. The fixed
nearest-site comparator had MAE 0.026202, and the training mean had 0.037466,
on the same 22 bins. These are descriptive results for one site, not evidence
of a general method ranking across Sweden. The 16 exact source labels account
for 224,291 of 393,822 native pollen NISP counts (56.95%); these scores
describe that closed subcomposition, not all pollen or vegetation.

Sämbosjön contributes 111 distinct core samples. Each has a source-default
comparable calibrated age from the Neotoma MADCAP chronology; temporal bins
did not propagate its age uncertainty. A nearby LandClim `SAM` point is
3.316459 km away and remains an explicitly refused identity join. The source
names Gunnar Digerfeldt and a 1982 primary report; the Neotoma dataset DOI is
[`10.21233/53ys-nt12`](https://doi.org/10.21233/53ys-nt12). Neotoma's
[data policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
governs reuse and attribution.

The site is newly scored, with prior aggregate count-mass and positive-bin
exposure disclosed in the [protocol and governed evidence](../../docs/report/regions/nordic/sambosjon-direct-pollen/README.md).
The shared source screen parsed target rows during preparation but discarded
them before predictor inputs. Aggregate scores were inspected after a
pre-score prediction freeze and before a later annotation correction; fixed
prediction bytes did not change. This is descriptive development evidence,
not independent confirmation. One site supplies no between-site uncertainty
estimate. The result does not admit LRA reconstruction or validate predictions
against measured vegetation.
