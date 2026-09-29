# Rootsi workbook age-column audit

The [replay](replay.py) verifies the four private workbook hashes against the
[79-sequence overlap ledger](../../rootsi-landclim-overlap/overlap.csv), then
reads only the source-native age-column structure. Its [report](report.json)
retains exact sheet-row locations and values for chronology reversals. The
workbooks remain in the private source store.

| Sequence | Sample rows | Explicit source age column | Finding |
| --- | ---: | --- | --- |
| FLINK | 109 | `Sample age (cal AD/BC)` | The value jumps from −3850.6025 at sheet row 55 to +3910.8433 at row 56, then returns to negative ages. |
| HOLK | 40 | `Sample age (cal AD/BC)` | The bottom two ages rise from −1491.0767 to −1490.1805; the 40 exact numeric ages contain no duplicates. |
| RANV | 141 | None | Column two is `SALIX`; no workbook sample-age field is present. |
| STAV | 77 | None | Column two is `Picea`; no workbook sample-age field is present. |

The FLINK jump is a candidate sign error, but the local bytes do not authorize
a corrected value. HOLK has a small source-order reversal; the claim of
duplicated ages in the inherited review is not supported by exact equality of
these 40 workbook cells. RANV and STAV have site coverage metadata elsewhere,
which are not sample dates. No source age uncertainty, model identity, historical
publication-input identity, or per-sequence analytical rights is established.
All four remain refused for dated-event and LRA use on this evidence.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/landclim/workbook-chronology/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/rootsi-workbooks \
  --output artifacts/jobs/rootsi-workbook-chronology/report.json
cmp artifacts/jobs/rootsi-workbook-chronology/report.json \
  docs/report/source-relations/landclim/workbook-chronology/report.json
```
