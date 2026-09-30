# Why we retired the chronology and basin checkout

## Our decision

We removed the inactive chronology and basin candidate checkout from
`artifacts/v3/` after checking that its source changes are recoverable from
repository history. The checkout was a run input, not a scientific result
owner. Its plan declared no output files, and the three companion launcher
logs contain zero bytes. We do not treat those empty logs as passing tests.

The candidate plan named product commit `af60ed9912251f28303054424686145e12e29494`
and a focused runtime-isolation and LRA-prerequisite test command. Its SHA-256
was `d123f4c414e4878c78f62b186be55ead02ce93dec90b4e567e1bff1b37ce6e75`.
No live process or product reader referenced either selected artifact prefix
at removal time.

## What we checked

The checkout contained 5,790 file or symlink paths. `git ls-tree -r` at the
declared commit contained 5,782 of those paths; the eight additional paths
were LRA-prerequisite source and test files. Of the checkout entries, 5,781
had the declared commit's exact timestamp, and nine had a later timestamp:
those eight additions plus the edited runtime-isolation test. We checked that
the exact Git blob for each of the nine later entries is reachable from a
repository ref:

| Later entry | Reachable Git blob |
| --- | --- |
| `src/.../lra_prerequisites/__init__.py` | `099d0a32dfe1ebcb98e66b3c670486712d32ce88` |
| `src/.../lra_prerequisites/__main__.py` | `21097299d8da75598f79dd4912491a81dfefbbca` |
| `src/.../lra_prerequisites/decisions.py` | `b9eed7d05cf48a974e4086f226a4f6cf2db5c17f` |
| `src/.../lra_prerequisites/projection.py` | `fa4a5d32ccfcc1978233010160414a37f08c79e6` |
| `tests/.../lra_prerequisites/__init__.py` | `d5c3b5f38341573f2f4aca7a6294eae77a670ca3` |
| `tests/.../lra_prerequisites/test_decisions.py` | `acd8dcf67125ddc58badd2627fbd5f1fa19bb691` |
| `tests/.../lra_prerequisites/test_main.py` | `803568048e61361bd9a85036ddeb6d91fdd3eedf` |
| `tests/.../lra_prerequisites/test_projection.py` | `66275ff2f8529578d1600ffaaa13a56c41a21355` |
| `tests/test_runtime_isolation.py` | `831fb585d9284b34b46653ea8aa32981ad007446` |

In the table, `src/.../lra_prerequisites` expands to
`packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/taxa_review/lra_prerequisites`;
`tests/.../lra_prerequisites` expands to
`packages/bijux-pollenomics-dev/tests/taxa_review/lra_prerequisites`. The
runtime-isolation test is under `packages/bijux-pollenomics-dev/tests/`.
The one checkout symlink, `data/adna/species/homo_sapiens/raw/aadr`, pointed
within that checkout to `../../../../aadr`; it did not point at an external
source store. We did not rehash every base-commit data file. The path set,
commit-matched timestamps, plan, exact later blobs and absence of result
outputs were the basis for retiring this bounded copy.

We removed only `artifacts/v3/science-chronology-candidate-af60ed99/` and
`artifacts/v3/science-chronology-runtime-af60ed99/`, about 2.2 GiB and 12 KiB
respectively. Other `artifacts/v2/` and `artifacts/v3/` prefixes still need
their own source, consumer and liveness decisions before removal.

## Map legend check receipts

We also retired the inactive 16 KiB `artifacts/v3/core-legend-successor/`
prefix. It contained only two terminal check receipts: a focused run exited
zero with **8 passed in 0.89 seconds**, and a style run exited zero with
“All checks passed” and one formatted file checked. No source, prediction,
fixture or code file lived in that prefix, and no product reader or live
process referenced it. The receipts did not retain an exact command or input
closure, so they are historical outcomes only and cannot certify the current
map legend or replace a selected check on current code.
