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

**Supported claim.** The pinned source audit reconciles registered families, country/capability cells and historical intake custody without claiming full source confirmation.

**Unsupported claim.** Zero mechanical findings cannot certify provider completeness, historical input semantics, rights or scientific review.

**Actual verification performed.** Read retained summary, external intake dispositions and source-specific blockers; no private archives or whole-registry audit rerun.

**Remaining input or review.** 53 supported dimensions need missing/partial materialization; qualified taxonomy, chronology, basin, rights and independent truth evidence remain.

**Cause category.** Mechanical accounting and scientific acceptance are separate states.

**Consequence.** Rootsi/OpenLand are intake relationships, not new independent vegetation families.

**Precise next acceptance route.** Resolve exact per-source blockers and changed evidence closure before rerunning source/country consumers and scientific review.

**Negative or refused result.** accounting_checks_pass=true but full_source_confirmation=false; SEAD 177,763 event dispositions remain refused.

**Matched denominator.** 11 families/198 country cells/187 capability cells; 321 input paths/284 present/204 manifested identities; 3 receipts/12 country claims/2 original archives; 0 mechanical findings.

- [Retained qualification evidence: docs/report/source-relations/source-reconciliation/report.json](report.json) (SHA-256 `16ff5155e6d653691587353ee2f1c741655f86f6cce12e669ff40c839a8b2eb2`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
