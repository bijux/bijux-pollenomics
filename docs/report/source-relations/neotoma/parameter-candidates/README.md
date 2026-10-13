# Neotoma pollen names against published LandClim parameters

The [candidate ledger](report.json) compares the exact 31 taxon or pollen-type
strings in the PANGAEA LandClim II PPE/FSP parameter table with the current
Neotoma pollen-concept priority. Both consumed file paths, byte counts and
SHA-256 hashes are in the ledger. Its SHA-256 is
`6f3290a73db9d5e02c4f66a9c38fe809cbf3d1795515186b7a9f0da9843e3065`.

Twenty parameter strings have at least one literal source-name match. Eleven
have none. The twenty strings lead to **23 distinct source-concept rows**:
`Betula`, `Tilia` and `Ulmus` each have separate `NISP` and `NISP digitized`
rows. Their observation counts and exact source-unit sums remain separate.
For example, `Betula` has 9,920 native `NISP` observations and 49 digitized
`NISP` observations. Neither unit is merged or converted. `Cerealia-t` has
no literal source-name match; a similar-looking source label cannot be used as
an unreviewed replacement.

These are spelling leads, not accepted biological mappings. All selected
Neotoma concepts remain `needs_discussion`; the source's PPE and FSP strings
are retained but not applied. This table does not establish a pollen counting
denominator, historical parameter version, taxon identity, basin support,
qualified review or LRA eligibility. The admitted LRA sample count remains
zero. A reviewer can use the exact concept IDs and separate source units to
resolve row-specific mappings without losing unmatched parameter rows.

Reproduce into a fresh directory under `artifacts/` and compare `report.json`
byte-for-byte with the governed report:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.neotoma_parameter_candidates \
  --repository . --output artifacts/neotoma-parameter-candidates/replay
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_parameter_candidates.py)
refuses changed parameter/concept row counts, duplicate source concept IDs,
duplicate parameter names or a changed review/admission state. The focused
regression checks the native/digitized split and refuses review-state promotion.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
