# Conditional English receiving-disk sensitivity

This account changes only the local transport model for the previously exposed BECKHAM regional and LARKBARR local training pair. The author TW5 aggregate covers 1250–1750 BP and is labeled 1500. We retain the original exploratory 30-taxon mask excluding Filipendula (source fall speed 0.006 m/s). BECKHAM retains 699 of 741 counts after 42 exclusions; LARKBARR retains 553 of 563 after 10 exclusions. The separate 15-site cohort retains 20,573 of 20,732 after 159 exclusions; two empty windows remain outside that cohort. These denominators describe different populations.

The local receiver is a uniformly area-weighted disk of radius 80 m. Homogeneous terrestrial sources occupy annuli 81–500,500–1000 and 1000–10000 m. The 80–81 m guard strip and sources beyond 10000 m are outside this local calculation. The regional factor retains the historical lake profile with radius 150 m and cutoff 100000 m. This is an explicitly declared hybrid comparison; the unchanged historical account retains its zero middle-ring factor. It is neither original historical reproduction nor an authenticated physical landscape.

The [admitted mathematical capture](../../../../data/method-certification/english-receiver-annulus/kernel-capture.json) retains 60 actual independent comparisons for 20 source fall speeds and three rings. Angular integration versus independent emitting/receiving-area quadrature agrees within 6.58e-14; the 64/128-order independent difference is at most 1.49e-12. These floating diagnostics are not rigorous interval bounds. The kernel interprets GPM survival as an isotropic stationary planar displacement law; it does not establish physical basin suitability.

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
