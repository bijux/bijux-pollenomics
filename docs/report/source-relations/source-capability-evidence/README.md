# Source capability evidence review

The [reproducible review](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/capability_evidence.py) checks every cell of the pinned [source capability contract](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/source_family_contracts.json) against the [materialization audit](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/source_family_evidence_stage_matrix.json) and current evidence bytes. The [report](report.json) retains 11 source families × 17 dimensions = 187 rows with each row's support state, materialization state, evidence paths, coverage metrics, reason codes, and human review flag.

The matrix contains 68 supported, 58 partial, and 61 unsupported capability cells. Separately, 73 cells have complete materialization, four partial, 49 missing, and 61 not applicable. The report hashes all 74 distinct present evidence files and explicitly lists 30 distinct missing paths. Human review remains required for 126 rows. A present file proves only that the declared artifact exists at its recorded digest; it does not promote a source dimension or establish scientific admission.

The producer refuses incomplete or duplicated source–dimension rows, a difference between declared support and audit support, changed evidence presence, invalid count metrics, and paths escaping the repository. Source support and evidence presence remain independent. Country coverage, transformation lineage, publication language, and source-specific scientific review are governed by their separate source and country ledgers; this review does not replace them.

The producer marks a `taxon_identity` cell declared unsupported by its source contract with `not_provided_by_source`. This reason describes source-native taxon availability; broad land-use categories do not become taxa. A supported or partially supported source with missing repository evidence retains its missing materialization state instead. Null source taxa, unmapped concepts, support states, coverage counts, and human-review requirements retain their separate meanings.

## Reproduce

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.capability_evidence \
  --repository . \
  --output artifacts/source-capability-evidence/replay.json
```

Compare `artifacts/source-capability-evidence/replay.json` byte-for-byte with `report.json`. The focused [tests](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/tests/source_completion/test_capability_evidence.py) exercise the support/materialization split and refusal cases.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
