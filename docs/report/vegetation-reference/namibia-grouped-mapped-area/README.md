# Grouped prediction of five-taxon mapped area in Namibia

Training a positive compositional correction improves mean agreement with deposited mapped-area compositions over uncorrected pollen at all 15 source ring labels. A stronger baseline, the training-only mapped composition, has lower error at 8 of 15 radii under equal-site weighting and 9 of 15 under equal-group weighting. The correction therefore supplies a qualified algorithm development result, with substantial negative outcomes retained.

The sources are Tabares, Ratzmann, Kruse, Theuerkauf, Mapani and Herzschuh (2021): [modern pollen counts](https://doi.org/10.1594/PANGAEA.931033) and [calculated vegetation areas](https://doi.org/10.1594/PANGAEA.931035), in [the Namibia source series](https://doi.org/10.1594/PANGAEA.931037). Both native headers declare CC BY 4.0. The associated [paper](https://doi.org/10.1177/09596836211003193) describes pollen productivity and historical reconstruction; this experiment addresses a separate empirical predictor of deposited modern map quantities.

The native panel is Acacia, Dichrostachys, Grewia, Poaceae and Combretaceae. Ten sites contribute 50 positive integer count cells, totaling 6,894 grains across those five labels. The area table contributes 150 site/ring rows and 750 positive calculated areas in square metres. Fractions close over these five listed quantities. Neither denominator establishes all pollen or whole-landscape vegetation cover. The area source names its method “Calculated, vegetation cover”; it supplies a map-derived target, rather than independent field vegetation measurements. Exact soil/image dates, actual image masks, taxonomic classification uncertainty and campaign dependence remain unresolved. No age or BP conversion enters the calculation.

The 15 native ring-sector labels run from 100 to 1,500 metres. Ring quantities remain separate; they are not converted to cumulative disks. Modern pooled Acacia is retained as supplied and is not split into the historical output's Senegalia and Vachellia axes.

To reduce obvious spatial overlap between training and target, a declared 1.5 km circular envelope is placed around each native event coordinate. Under a spherical distance with radius 6,371,000 m, T4 and T5 are 2,111.062 m apart and share one held-out group. The closest non-intersecting pair is T8/T10 at 5,317.683 m. This yields nine nominal groups. The approximation does not recover the actual image-sector masks or establish statistical independence. All rows of the whole held-out group are excluded at every radius; the other eight groups receive equal training weights, with equal site weights within each group.

For each radius, the fitted correction is the group-weighted mean of `log(mapped_share / pollen_share)` for each of the five taxa. Predictions close the held-out pollen multiplied by the exponential correction. Two baselines use the same paired source support: unchanged pollen, and the closed geometric mean of training mapped compositions. All source cells are positive, so no pseudocount or assumed zero is needed. The [estimator proof](estimator-proof.md) establishes the unique centered least-squares log-compositional solution under these conditions. It establishes no physical transport, PPE or ERV interpretation.

The saved prediction ledger contains all 450 vectors before the first scorer call. Outcomes were already exposed, so that ordering does not create an untouched confirmation population. Scores use squared Hellinger loss, `sum((sqrt(predicted) - sqrt(mapped))²) / 2`; smaller is better. Equal-site means average ten sites; equal-group means average nine groups. All 15 radii are retained without selecting a best radius.

The [complete table](all-radius-means.md) includes both weighting schemes and every radius. In the 150 paired site/radius contrasts against unchanged pollen, the correction is better in 130 and poorer in 20, with no ties. Against the training mapped baseline, it is better in 60 and poorer in 90, with no ties. All 110 poorer contrasts remain in the original report. The largest deterioration against the mapped baseline occurs at T3's 1,400 m ring: correction loss 0.147341104797, unchanged pollen 0.115110836618, mapped baseline 0.042007846620. This is a retained failure of the correction on that source target.

The actual native job passed 17 source/training/scope guards and emitted all 450 vectors, 450 scores, 90 mean values and 300 contrasts. A separate implementation reparsed original count/area tokens and used 50-digit Decimal arithmetic for all 7,290 compared fields, including 2,250 prediction cells. Maximum absolute difference was at most 5.356174e-16 under the unchanged 1e-12 tolerance. A separate unit-vector spherical calculation checked all 45 position pairs; maximum distance difference was 6.912160e-10 m. These implementations share an interpreter. Numerical agreement checks the calculation; it adds no independent environmental observations.

The result concerns one exposed study family with repeated ring targets. Ten sites, nine nominal groups and 150 site/ring rows do not constitute 150 independent cohorts. There are no calibrated uncertainty intervals, field vegetation accuracy, PPE identification, ERV calibration, historical reproduction or Nordic transfer claims. In particular, successful empirical correction does not resolve the paper's reported unreliable grass PPE/ERV estimation. The preserved mapped baseline comparison limits claims of predictive usefulness even within the declared development scope.

The [source/result qualification](source-account.json) binds the exact source, protocol, native terminal, ledger and independent numerical review. The original native report retains its pending-review status; the subsequent numerical and source reviews remain separate evidence. No model, oracle or scoring calculation was rerun to assemble this account.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named measured/mapped/published reference scope and unmatched temporal/taxon/observation/independence limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/namibia-pollen-vegetation-paper.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/namibia-pollen-vegetation-paper.md) (source SHA-256 `a8c92d02c7e7a9d2155f193b5e59451d741184afbfdd626eb5d8c4c3ae8e4bcc`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
