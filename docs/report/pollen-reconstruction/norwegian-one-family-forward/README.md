# Norwegian one-family pollen forward development

Two actual calibrated training cores, Mukkavaara (dataset 4286, chronology 30602) and Rattuvarri (4372, 25351), predict the literal Betula/Poaceae pollen panel at the already exposed Dalmutladdo target (20034, 11601). Both training cores share primary publication 1096; retained secondary reference 1149 does not create another independent family. This is a conditional cross-core development result.

The declared support extends workbook grids 1486 and 1436 within 100 km of the native target point. The assumed static receiver radii are 252, 98 and 160 m, with land annuli from the receiver edge to 100 km, wind 3 m/s and the source's empirical metre-based coefficient 0.12. Every admitted sample has actual integer NISP pollen counts for both literal labels; missing rows remain refusals. Native calibrated BP points relative to AD 1950 determine half-open windows. Native age bounds are preserved privately; most admitted training bounds cross windows and all 72 target bounds are missing. No interpolation or calibration is performed.

The source census admits 55/56 Mukk, 30/32 Rattu and 72/72 Dalmut samples. Both training cores support 20 windows; 18 have target outcomes, with 17,935 unique paired target panel counts. All 20 windows generate all three predictions. The complete 60-vector ledger is written and hashed before a separate scoring loop reads its frozen predictions. Two older windows retain absent target outcomes, yielding 54 scored and six unscored method records. The target data were previously inspected; this is not untouched confirmation.

The physical inverse uses

\[
U_i=\sum_s \frac{n_{si}}{K_{si}p_i},\qquad c_i=\frac{U_i}{\sum_jU_j}.
\]

Forward closure at the target gives

\[
\operatorname{close}(K_{\mathrm{target},i}p_i c_i)
=\operatorname{close}\left(K_{\mathrm{target},i}\sum_s\frac{n_{si}}{K_{si}}\right).
\]

Positive shared PPE cancels from this pollen prediction. Lower pollen scores therefore cannot identify PPE or validate reconstructed vegetation cover. Conditional training-cover covariance still includes fixed-total multinomial counts and shared diagonal PPE variance, with count-site independence and zero count–PPE cross-covariance as working assumptions. Unknown shared investigator and chronology correlations are omitted; no forward predictive uncertainty or empirical coverage is claimed.

All three methods share the same observed source/window/spatial support. Equal-window squared panel-fraction error is 0.0046395958 for the physical method, 0.0047549467 for count-pooled pollen and 0.0049424239 for the equal-source mean. The physical method has lower error in 18/18 windows against count pooling and 15/18 against equal-source averaging; windows 17, 19 and 21 retain poorer physical results. Both equal-window and target-count-weighted summaries and every paired contrast remain in comparisons.json. The improvement is modest development evidence, not ecological truth.

The actual native collector exited 0 with 15 source controls. An independent Decimal50 consumer checked 632 saved cover, covariance, prediction, score and contrast cells, with maximum absolute difference 1.6914e-16. Its own scalar circle-lens integration checked the two new 252 m response tuples across 40 window/taxon uses, with maximum factor difference 2.8872e-13. Existing 98/160 m qualifications cover only their exact reused tuples. Error and convergence estimates are numerical diagnostics, not rigorous bounds or empirical transport validation.

The original numerical report's pending flag is retained unchanged because it preceded the oracle. Separate later review and native-terminal hashes establish the scoped numerical qualification. The maintained writer replays this retained account and does not rerun the model. Native per-sample counts, age bounds and identifiers stay in the private qualified source store. Rights, qualified external review, two independent training families, full taxon panels, historical reproduction, vegetation accuracy and untouched validation remain open.

Producer module: `bijux_pollenomics_dev.source_completion.pollen_reconstruction.norwegian_one_family_forward.producer`. Its pinned source descriptor is `configs/ci/qualified-report-sources/norwegian-one-family-forward.json`; the ordinary artifact output contains only report.json, comparisons.json, assumptions.json and source-account.json.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
