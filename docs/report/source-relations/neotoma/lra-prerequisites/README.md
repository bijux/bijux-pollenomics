# Neotoma LRA prerequisite review

The [source-bound projection](projection.json) has SHA-256
`26135d91bbe5d729dcca3a1f6f0ea69f5cec4dc00a54a6dd740d5004d4e4b809`.
It retains 10,637 sample-owned chronology review rows and 163 source-site basin
review rows from the corrected Neotoma relational snapshot. Country partitions
are Sweden 5,011 samples/77 sites, Denmark 91/1, Norway 3,544/52, Finland
1,797/28, and unassigned 194/5. The unassigned partition is not a fifth Nordic
country. Every row carries source identity, review status and source locators.

The lakeparameter source capture contains 24,554 rows in verified public API
pages. It was originally bound to a 54-site review with SHA-256
`aaded8ed751a8f245a357c50bb2c2a96a8710168deab7223f0c48284180e96ce`.
The producer verifies that original review and the original capture summary
against the exact page bytes. It then verifies that all 54 original site IDs
remain in the corrected 163-site cohort under the same raw Neotoma snapshot,
and projects the same source pages against the larger cohort. Fourteen native
lakeparameter rows match 13 current sites; 43 sites separately retain a native
site `area` value without an established unit or historical basin meaning.
The source pages came from live offset pagination, not a transactional snapshot;
absence of a row is not certified.

These are review leads. Chronology choice, taxon classification, a compatible
pollen denominator, PPE/fall-speed binding, historical basin geometry and
qualified returned decisions remain unresolved. The projection has **zero
accepted samples**, `scientific_acceptance=not_evaluated`, and no executable LRA
request. It does not supersede the separate four-country observed-pollen
prediction study.

To reproduce, run
`python -m bijux_pollenomics_dev.taxa_review.lra_prerequisites` with the
repository raw root `data/neotoma/raw/neotoma_pollen_dataset_downloads`,
normalized root `data/neotoma/relational`, external capture root
`<external-Neotoma-lakeparameter-capture-root>`, capture
SHA-256 `0c800ed252d6bd2bbed72f5ac7798e27d7a72f89330170b8ce33989384c758fd`,
and a new output path under `artifacts/`. Compare the resulting exact SHA-256
with the governed projection above before reuse. The external capture path is a
local custody location, not a source publication URL.
