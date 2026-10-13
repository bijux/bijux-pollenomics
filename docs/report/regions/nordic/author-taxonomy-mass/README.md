# Author taxonomy coverage in held-out Nordic pollen

The [report](report.json) and [site ledger](sites.csv) measure native pollen count
coverage for the exact Danish, Finnish and Norwegian samples in the
[country-held-out direct-pollen study](../direct-pollen/RESULTS.md). The producer
reopens the hash-bound Neotoma observation parts and reproduces the published
cohort selection before applying the authors' 10,788-row
[LandClim II taxonomy lookup](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv).
It retains the native NISP denominator, the mass assigned to 31 author targets,
the mass assigned to author exclusion codes, and names absent from the lookup.
Each site's three exclusive masses sum to its selected native pollen NISP, which
also agrees with the published direct-pollen input profile. Counts are not
reallocated between taxa.

| Country | Sites | Samples | Native NISP | Assigned to author targets | Author excluded | Unmapped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Denmark | 1 | 91 | 129,768 | 122,998 (94.78%) | 6,699 | 71 |
| Finland | 28 | 1,797 | 1,260,281 | 1,229,019 (97.52%) | 28,847 | 2,415 |
| Norway | 52 | 3,544 | 2,286,020 | 2,018,295 (88.29%) | 233,598 | 34,127 |

Norway's largest unmapped names are `Ranunculus sect. Batrachium` (15,061 NISP)
and `Artemisia sp.` (11,150); its largest author-excluded name is
`Myriophyllum alterniflorum` (76,935). Those rows remain distinct so a future
taxonomic decision can be reviewed against the actual source mass. The zero
size-variant candidate count refers only to the two Swedish size labels previously
identified in the source review; it does not mean that all Nordic variants have
been resolved.

This is a source-taxonomy feasibility result, not an LRA-ready sample count or a
REVEALS/LOVE reconstruction. It establishes neither qualified lake-basin geometry
nor country-specific PPE, fall speed, dispersal support, source rights for the
private Swedish workbooks, or independent vegetation observations. The 16-label
direct-pollen study has a different response and denominator. All 5,432 selected
samples therefore retain `lra_admitted_samples = 0` in this report.

Run from the repository root:

```sh
source_store="/path/to/qualified/bijux-pollenomics-data"
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.nordic_author_taxonomy_mass \
  --repository . \
  --author-source-root "$source_store/landclim/author-reference" \
  --output artifacts/jobs/nordic-author-taxonomy-mass
```

The external lookup is identified by SHA-256 in the report. The input source
rights and investigator attribution are recorded in the
[Neotoma](../../../../public/pollenomics-data/sources/neotoma.md) and
[LandClim II](../../../../public/pollenomics-data/sources/landclim.md) source
reviews. The checked-in files contain aggregate counts and source names, not the
private lookup or source workbook bytes.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
