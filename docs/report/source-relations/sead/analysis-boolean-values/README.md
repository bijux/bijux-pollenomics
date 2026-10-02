# SEAD boolean component lineage

This account checks whether native boolean flags survived the governed SEAD
capture and staging unchanged. It compares each typed component with its raw
parent analysis value and the corresponding staged observation. The
[compact report](report.json) keeps parent display text, value-class IDs and
boolean types separate.

The source is acquisition `sead-full-evidence-39bfff6a-ce80714e`, with build
`sha256:ce80714e4c9e9974b24913e5da50f49854670ed642879c1ca5076499e1d56725`.
The report binds the raw admission, acquisition and evidence manifests, two
raw tables, the observation header and all 25 observation partitions through
31 exact source hashes.

## Source populations

| Population | Rows |
| --- | ---: |
| All staged source observations scanned | 177,763 |
| Parent analysis values reconciled | 68,705 |
| Boolean components and their distinct parents | 11,603 |
| Typed true components | 1,708 |
| Typed false components | 9,895 |
| Typed source-null components | 0 |
| Eligible events admitted | 0 |

These denominators describe different populations. The absence of nulls in
the boolean component table does not mean every parent analysis value is
reported. False and null remain distinct states. Integer `1` and `0` cannot
substitute for native boolean `true` and `false`, even though Python equality
can treat those pairs as equal.

## Interpretation and event admission

There are 17 exact combinations of value-class ID, boolean state and parent
display text. For example, 4,766 false components have display `Nej` in class
5, and another 4,391 have the same display in class 7. Class 18 includes
1,296 true components with display `Not dated`. The report preserves those
labels without translating them into presence, absence, human activity,
selected dates or transport routes. Interpretation requires the relevant
source semantics and scientific qualification.

All 68,705 parent observations retain refused event eligibility and the
`source_classification_not_accepted` reason. This check establishes typed
source continuity. It supplies no ecological classification, calibrated age,
chronology admission or first-observed event.

## Reproduce

From the repository root, with an absent artifact destination:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run --frozen python -m \
  bijux_pollenomics_dev.source_completion.sead.boolean_values \
  --repository "$PWD" \
  --output "$PWD/artifacts/sead-boolean-lineage/report.json"
```

Compare that JSON with the governed report. The writer refuses changed source
hashes, component or parent substitutions, repeated or missing parent keys,
altered event eligibility, unsafe destinations and existing output files.
Its source hashes are checked again before writing the account. The source
files remain subject to external concurrent writes; they are not locked by
this producer.
