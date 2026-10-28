# Abborrtjärnen chronology sensitivity for direct pollen prediction

We replayed the [three-site Swedish direct-pollen development study](../swedish-direct-pollen/REPORT.md)
with a conservative age rule for Abborrtjärnen (ABBO). The age evidence is the
[published LegacyAge 1.0 S5 depth join](../../source-relations/neotoma/legacyage-chronology/README.md)
to the same 107 Neotoma samples. A sample enters a 500-calibrated-year BP bin
only when its **entire reported S5 95% interval** lies inside the bin. A sample
whose interval merely overlaps a bin remains unresolved; we never assign it by
its mean or duplicate its counts across bins. Bussjösjön and Bökesjön retain
their native Neotoma point chronologies because no equivalent interval source
was admitted for them.

The original study has 13 shared bins. ABBO has eight interval-contained
samples in four of those bins: one in 1500–2000 BP, three in 2000–2500 BP,
three in 2500–3000 BP, and one in 4500–5000 BP. The eight samples contribute
3,543 NISP in the same closed 16-taxon subcomposition. The [sample ledger](age-bin-support.csv)
accounts for all 107 ABBO samples: eight contained, 37 overlapping a selected
bin without full containment, and 62 outside the four selected bins. The
[prepared ABBO profile](prepared/dataset-19913.json) contains the counts that
train or score the interval sensitivity.

We held out each entire physical site in turn, preserving the four fixed
predictors and their zero handling. The target pollen profile was not opened
by its prediction process; the [ABBO](predictions/site-13338.json),
[Bussjösjön](predictions/site-28869.json) and
[Bökesjön](predictions/site-28872.json) prediction files were saved and
hashed before the separate scoring process opened target
counts. All four methods predicted and scored the same 12 site-bin targets.
The comparison below uses exactly those four bins for **both** the original
point-age result and this interval-contained result. Values are site-macro
scores: four bins average within a site, then three sites have equal weight.

| Fixed method | Original MAE | Interval MAE | Original Hellinger | Interval Hellinger |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.060594 | 0.060258 | 0.427503 | 0.426070 |
| Nearest site | 0.056852 | 0.056477 | 0.425366 | 0.424255 |
| Inverse distance squared | 0.060058 | 0.059762 | 0.439302 | 0.438298 |
| CLR RBF ridge | 0.059051 | 0.058751 | 0.431725 | 0.430511 |

The small paired differences are a development sensitivity on a **very sparse
and selected** subset. They do not establish a better chronology or model.
The reported S5 intervals are marginal age summaries, not a joint posterior;
full containment in a 95% interval is not a guarantee of true bin membership.
Selection of the four bins followed inspection of ABBO source support. The
original site outcomes were already exposed, and the three lakes are
geographically unbalanced. The two southern chronologies remain point ages,
so this is not a common uncertainty treatment across sites. No basin geometry,
PPE, dispersal profile, vegetation truth, or LRA reconstruction enters this
study. The [score rows](scores.csv), [per-taxon scored predictions](predictions-scored.csv),
[summary](summary.json),
[same-support comparison](comparison.json), [config](config.json), and
[input receipt](input-manifest.json) retain the exact denominators and source
identities.

## Reproduce

From the repository root, use an absent output directory under `artifacts/`.
The producer checks the byte identities of the Neotoma input, original
profiles and LegacyAge sample join. Run `prepare`, three site-specific
`predict` processes, then `score` after all prediction files exist:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py \
  prepare --repository . --output artifacts/abbo-age-interval-sensitivity
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py \
  predict --repository . --output artifacts/abbo-age-interval-sensitivity \
  --target-dataset-id 19913
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py \
  predict --repository . --output artifacts/abbo-age-interval-sensitivity \
  --target-dataset-id 53995
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py \
  predict --repository . --output artifacts/abbo-age-interval-sensitivity \
  --target-dataset-id 54001
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py \
  score --repository . --output artifacts/abbo-age-interval-sensitivity
```

Compare the generated `age-bin-support.csv`, ABBO prepared profile, three
prediction JSON files, `predictions-scored.csv`, `scores.csv`, `summary.json`,
`comparison.json` and `input-manifest.json` with the governed files here.
Source credit and original
investigator attribution are retained in the parent [cohort](../swedish-direct-pollen/cohort.csv);
the LegacyAge S5 source is [Li et al. (2021), PANGAEA
933132](https://doi.org/10.1594/PANGAEA.933132), CC BY 4.0.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** A previously exposed three-lake direct-pollen study is rescored on four selected bins after replacing ABBO point assignment with full containment of each published LegacyAge S5 marginal 95% interval. The reported paired score changes are conditional development sensitivity.

**Unsupported claim.** A more accurate age model, joint 95% membership confidence, independent confirmation, a common uncertainty treatment across all lakes, LRA reconstruction or measured vegetation accuracy.

**Actual verification performed.** The reader, unchanged source/support ledger, configuration, input manifest and retained same-support comparison/summary were inspected. They describe separate prediction files saved before target-count scoring. This qualification runs no prepare, prediction, scoring or independent numerical replay.

**Remaining input or review.** The four bins were selected after inspecting ABBO support, and outcomes were already exposed. S5 supplies marginal intervals rather than a joint age posterior; Bussjösjön and Bökesjön still use point ages. Basin/PPE/dispersal and independent vegetation truth are outside this experiment.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Interpret the small same-support score reductions as a sparse conditional sensitivity. Interval containment cannot certify true membership, chronology accuracy or transfer skill; keep all unassigned source samples visible.

**Precise next acceptance route.** For joint age or chronology-quality claims, obtain and qualify a joint depth-consistent age model and comparable uncertainty sources for all sites. Freeze bin selection and a new evaluation before unexposed outcomes; assess vegetation/LRA claims separately with their required physical/reference inputs.

**Negative or refused result.** Only 8 of 107 ABBO samples are interval-contained in the four selected bins; 37 overlap without full containment and 62 are outside those four bins. Unresolved intervals are not assigned by their mean or duplicated as independent observations.

**Matched denominator.** 3 physical lakes; 4 selected 500-calibrated-year BP bins; 12 identical scored site-bin targets for each of 4 fixed methods. ABBO contributes 8/107 source samples and 3,543 NISP on the selected closed 16-taxon axis. Scores average bins within each site and weight the 3 sites equally.

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/age-bin-support.csv](age-bin-support.csv) (SHA-256 `26ca6dc862790c71a3a7821b027413307dd2334856080a1b07e186177cfb8e01`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/comparison.json](comparison.json) (SHA-256 `29ebcf5719161541c4241436e56feb02e282559780d5225c1e2a2b450f7eeab1`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/summary.json](summary.json) (SHA-256 `2a1e979eeb338e789fbb57e7e75353ff9a2737d782a82173a6aa2be9038ff0e8`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/age-interval-sensitivity/input-manifest.json](input-manifest.json) (SHA-256 `29c59ac308596444ee7abae1a1e4fe81e530157ee073dce5adc593a3fc99f4f4`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
