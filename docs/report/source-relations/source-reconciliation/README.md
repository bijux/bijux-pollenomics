# Source registry and intake reconciliation

The [combined audit summary](report.json) rechecks the 11 registered source families,
198 country-dimension cells, 187 capability cells, and three historical
external intake receipts against one pinned repository and private-source
read set. Its full reproducible audit records 321 repository input paths, 284
of them present, and checks 204 manifest-declared file identities; it also
verifies both original private intake archives. The mechanical accounting has
**zero findings**;
its content-bound full-audit digest is
`26116f18017f5695c8782849e9ab827251d033cc56a8e1e76eabf38063c9ba90`.
The current audit includes 13 existing authority paths added to the source
validation closure; this changes its input and audit digests without changing
the source-family accounting or scientific admission decisions.
The governed summary retains the input-closure digest, per-family blockers,
country publication states, intake decisions and the full-audit digest without
duplicating the existing source and country ledgers.

The registered family ledger and the [Nordic capability report](../../regions/nordic/source-capability/README.md)
keep source-reported, governed-assignment and publication counts separate.
The aggregate audit verifies three historical intake receipts and retains
their 12 four-country claims in its `external_intake_custody` field.
Rootsi and OpenLand are not silently added as independent family rows or
vegetation observations. The audit retains native source-stage records,
rights and source roles, plus Neotoma, SEAD and LandClim source-specific
reconciliation details.

`accounting_checks_pass: true` applies only to the explicitly consumed
registries and manifests. `full_source_confirmation: false` remains in the
result. Fifty-three supported capability dimensions across the 11 families
still have missing or partial materialization; qualified taxonomy, chronology,
rights, basin and independent vegetation decisions are separate gates. A
missing file, blocked country cell or historic intake refusal is never an
observed zero or an approved scientific input.

Reproduce the complete audit from the repository root with the private source
store, writing a new artifact file:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion \
  --root . \
  --private-source-root ../bijux-pollenomics-data \
  --output artifacts/jobs/source-reconciliation/full-replay.json \
  --summary-output artifacts/jobs/source-reconciliation/summary-replay.json
```

The producer records each consumed file digest and refuses changed manifest
bytes, country cell identity, intake archive identity or source relationship.
Compare `summary-replay.json` with `report.json` byte for byte. Provider
completeness and scientific admission require evidence beyond this mechanical
audit.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
