# Buffered adjacent-grid pollen prediction

Two one-degree author grids are withheld in turn. Prediction reads only the opposite grid's count tables and predicts each author bin with clr_wgs84_rbf_ridge_half_count_31_taxon_observed_pollen_fraction_by_bin. A training basin must be at least 20 km from every target basin after subtracting both reported basin radii. The independently reopened target counts are scored afterward.

Across 17 author site IDs and 2 adjacent blocks, 184 site-bin targets have observed counts, 140 are scored and 44 lack the declared fit support ({'no_training_site_same_bin': 36, 'fitted_model_requires_two_training_sites': 8, 'no_positive_training_distance': 0}). Site-macro MAE is 0.040564 fractions; site-macro total variation is 0.628745. On 140 site bins scored by both methods, the site-macro MAE is 0.040564 for the buffered block holdout and 0.019955 for the retained within-grid site holdout. This paired difference is descriptive development evidence; coverage differs between methods.

The fitted model adds 0.5 to every named training taxon count before CLR closure, uses a per-bin median positive training-centre distance scale and ridge penalty 0.01. No target count enters fitting; the zero policy and scale rule were declared before scoring.

This is a development comparison on author-prepared pollen, not a Swedish cohort, LRA vegetation reconstruction, or measured vegetation accuracy. The 20 km basin-edge buffer is a declared diagnostic rule; the broader pollen source footprints and cross-database site aliases are not independently closed. Two adjacent blocks cannot establish general spatial-transfer uncertainty. Author-prepared 31-taxon counts do not certify a full raw-core pollen denominator or publication rights.
