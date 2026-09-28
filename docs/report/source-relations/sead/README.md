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
