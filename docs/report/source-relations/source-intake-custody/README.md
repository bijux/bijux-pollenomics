# Historical source intake custody

The [intake custody review](report.json) verifies three original intake
receipts and two materialized archives in the private source store. Its
`source-intakes/custody.json` has SHA-256
`5224fafb5854450d1f02163d8ad0b9c32479ad80576d3565a230873c24643220`.
The OpenLand ZIP and Rootsi archive together contain 204,568,300 original
bytes. The first OpenLand receipt records an unavailable attachment; the
second records the received ZIP. They are two receipt states for one named
delivery, not two independent datasets.
The replay validates all three receipts against the repository-owned
[`external-data-intake.v1` contract](../../../../data/source_intake_contract.schema.json)
after verifying their custody hashes. The report pins the contract SHA-256.
Schema validity records the historical intake format; it does not grant source
rights or scientific admission.

| Intake | Historical state | Four-country claim | Current scientific boundary |
| --- | --- | --- | --- |
| OpenLand unavailable receipt | Pending delivery; no archive hash | SE/DK/NO/FI not captured | Superseded for byte custody by the received receipt; no admission from this record |
| OpenLand received receipt | Quarantined; `adapt` decision; mixed rights | SE/DK/NO/FI blocked | [Member review](../openland-intake/README.md) identifies modeled cover and zero independent vegetation benchmarks; public use remains unapproved |
| Rootsi receipt | Quarantined; `review` decision; rights unknown | Swedish candidate workbooks; DK/NO/FI reference rows only | [Candidate overlap](../rootsi-landclim-overlap/README.md) does not authenticate historical inputs, chronology, taxonomy, or scientific use |

The historical Rootsi receipt claims 81 Swedish metadata rows, 79 observation
workbooks, 5,153 samples, 4,866 dated samples and 163,673 observations. Those
are receipt claims, not admitted pollen records. The separately retained
structural replay finds 5,170 mechanical data-row candidates; the different
denominators have different rules and are not reconciled as sample identity.
The Danish, Norwegian and Finnish reference rows in that receipt provide no
country pollen observation file. The machine-readable review retains all 12
historical country rows, their reason codes, receipt hashes and current report
hashes without turning missing or blocked evidence into zero observations.

Reproduce the review from the repository root with the private source store:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.intake_custody \
  --repository . \
  --private-source-root ../bijux-pollenomics-data \
  --output artifacts/jobs/source-intake-custody/replay.json
```

The producer refuses a changed receipt, archive, four-country roster, current
OpenLand archive identity, or Rootsi workbook archive identity. Exact original
receipts remain private; this report publishes only their historical decision
and country accounting. New rights and scientific decisions require their own
qualified review.
