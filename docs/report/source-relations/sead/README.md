# Governed SEAD relational capture replay

The retained source capture reconciles **61 tables and 522,270 source rows** to
522,270 distinct primary keys, with no duplicated primary keys. All 61 table
receipts are complete; eight tables are genuinely empty. The [table export](tables.csv)
retains each table's key field, row/key counts, minimum and maximum key, range
count, payload digest,
receipt digest and receipt status. Empty-table key endpoints remain empty.

The replay binds the normalized source-key ledger to independently admitted raw
acquisition bytes, receipt identities, relational admission and the country
boundary authority. It verifies every UUID/country binding through the existing
ledger derivation and checks the exact normalized file set and part identities.
It does not reacquire a changing provider snapshot or replace missing values.

The [summary](summary.json) retains the source run, build, scope, raw admission,
normalized manifest, source-key set and UUID-binding identities. The reviewed
bounding-box population is 2,195 sites: 2,069 assigned (SE 1,925; DK 59; NO 45;
FI 40), 103 requiring review and 23 unassigned. Review and unassigned sites remain
outside the assigned country population.

The [country discovery and retrieval ledger](../sead-country-retrieval/README.md)
checks each of those 2,195 identities against its boundary decision, the
retrieved source site row and the normalized site consumer. Its country counts
are governed boundary assignments because the source supplied no country field.

## Scientific boundary

The raw acquisition's release and downstream statuses are preserved exactly.
Those downstream statuses describe the acquisition-time admission, before later
normalized chronology and observation materialization. They are not assertions
that the current normalized products are missing. Complete capture does not
approve cross-source taxon/parameter mappings, lake events, propagation or
independent measured vegetation accuracy. The replay does not convert refused
scientific admission into a passing scientific result.

The [pollen-named dataset screen](pollen-named-dataset-screen/README.md) exports
sample-level source observations and records why the captured rows cannot form
an admitted pollen time series or LRA input.

The [numerical analysis value review](analysis-numerical-values/README.md)
traces 60 typed source values through their parent analysis rows and normalized
components. It preserves source precision differences and keeps all rows
outside scientific event admission.

The [integer analysis value review](analysis-integer-values/README.md)
reconciles all 24,701 typed integer components with their parent observations,
source classes and chronology links while preserving qualified display text
and event refusal.

The [country chronology account](chronology-country-accounting/README.md)
joins all 25,109 reviewed claims to the 2,069 assigned site decisions. It
separates source-row counts, distinct sites and chronology-display eligibility
for each country; every claim remains refused for ecological propagation.

The [country retrieval and evidence account](country-coverage/README.md)
reconciles those site decisions with source retrieval and 177,763 refused
observation dispositions. It keeps 103 review and 23 unassigned sites outside
the country totals, and records zero eligible ecological events.

The [country source-unit account](source-unit-accounting/README.md) follows
the same assigned sites through sample groups, physical samples, analysis
entities, distinct linked datasets and analysis values. Its source-unit counts
are separate from claim rows and ecological events.

## Report ownership

We replayed the six source-owned report families linked above: the pollen-named
dataset screen, numerical values, integer values, country chronology, country
coverage and country source units. Their producers reproduced all **11 governed
JSON/CSV files byte for byte** from the admitted source and normalized inputs.
All 15 local links in the six explanatory pages resolved. The
[owner verifier](verify_report_owners.py) binds each producer to its exact output
names and refuses an extra, missing or differing generated file. Run it from the
repository root with a new destination:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/sead/verify_report_owners.py \
  --repository . --output-root artifacts/jobs/sead-report-owner-replay
```

This covers these six source-owned families. The full mixed-owner `docs/report/`
tree has other producers and requires its own assembled no-difference check.

## Reproduce

From an installed development environment at the repository root, use a new,
unoccupied destination:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.source_completion.sead_relations \
  --data-root "$PWD/data" \
  --output "$PWD/artifacts/sead-relations-replay"
```

The producer uses the existing independent source-key/acquisition validators and
pinned identities, not the summary as an input. It refuses an existing destination,
a changed admission, inconsistent row/table denominators or a source-key ledger
that cannot be rederived from admitted acquisition bytes. A source refresh needs
its own governed admission and identities; it cannot silently reuse this replay.
