# EMBSeCBIO literal correspondence account

[report.json](report.json) preserves the source-bound population, conditional literal-label support and two complete reported-axis cases. [source-refusals.json](source-refusals.json) preserves the exact supplement access refusal and unsettled mapping, denominator, missing-data and source-identity decisions. The account distinguishes 112 shared-label correspondences from two complete reported axes; neither establishes the full 1,184-to-242 taxon transformation.

The producer consumes an independently pinned 18-file private source snapshot containing the original terminal, source/diagnostic populations, full-case association review and actual access refusal. Snapshot qualification establishes byte identity, not reuse rights or scientific endorsement. It copies no per-taxon count vectors or source-age fields into the public products. Existing [biome results](../embsecbio-biome-reconstruction/README.md) retain their own model/training evidence and limits.

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.pollen_reconstruction.embsecbio_literal_correspondence.producer \
  --repository . --source-root /path/to/private-scientific-source-store \
  --output artifacts/jobs/embsecbio-literal-correspondence/source-products
```

Create the output's parent directory first; the output directory must be absent. The private source-store parent contains `embsecbio/literal-count-percentage-correspondence` and its exact sorted-spec snapshot manifest. The atomic producer refuses changed source/control bytes, unsettled terminal custody, upgraded attribution/mapping claims, incomplete attempted populations and nonfinite diagnostic values. A publication replay is distinct from the original diagnostic, independent source review and future configured-owner qualification.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/vegetation-reference.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/vegetation-reference.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
