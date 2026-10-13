# Neotoma native variable and taxon surface

The [retained reconciliation](report.json) compares all native `datum` taxon
IDs, reported names, source taxon groups, ecological groups, elements, element
types and units in the validated nine-part download archive with the governed
relational variable surface. It validates the relational materialization before
reading its variable and conflict rows. The source snapshot is
`sha256:b2bcb99157e10b0c9f13c228acc12eabcb39d96a1f39c86ec25e34aacd78c791`;
the materialization is
`7d9bf04538f6fc9db0582a85656defc3b262b86b782d99bf310d2fec4ae96406`.

All 370,936 native datum rows produce 1,262 distinct native variable keys,
matching all 1,262 relational variable rows. Their 1,325 distinct source
semantic variants and source units match exactly. There are zero unidentified
taxon IDs, name or identity variants, variable identity conflict rows, missing
or unexpected variable IDs, duplicate variable IDs or attribute mismatches in
this snapshot. The report retains counts for all 14 source taxon-group labels:
316,806 datum rows say `Vascular plants`, while other source labels include
`Laboratory analyses`, `Unidentified palynomorphs`, `Algae` and `Charcoal`.
These labels remain source attributes; a variable row is not an approved pollen
taxon or an LRA input.

The [native hierarchy audit](../native-roundtrip/README.md) separately proves
parent-scoped raw observation payload preservation. This reconciliation checks
the derived variable surface and its source attributes. The
[acquisition scope receipt](../acquisition-scope/README.md) records the missing
original HTTP capture authority and six current-selection differences. None of
these reports supplies taxonomic approval, a pollen count denominator or LRA
admission.

Replay from the repository root into a new artifact path:

```sh
PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.neotoma_variable_surface \
  --repository "$PWD" \
  --output artifacts/jobs/neotoma-variable-surface/replay/report.json
```

Compare the replayed JSON with `report.json`; the source and materialization
identities must match before reusing the result. The focused regression covers
exact source attributes, a changed taxon-group field, a name conflict with and
without its ledger row, and an unidentified native taxon ID.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
