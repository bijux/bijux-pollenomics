# Our artifact custody decisions

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

## Known-landscape source checkout

We retired only the 13 MiB `artifacts/v3/known-landscape/agent001/snapshot/`
copy. Its plan named commit `cefea94daaad459494ab97742fcbf4cd2b042fe8`
and a focused source/test closure. We compared its files to that Git tree:
1,521 files had the exact commit blob, four were later synthetic generator or
test files whose exact blobs are reachable from repository history, and four
were Ruff cache files. No independent numerical result lived in this
snapshot. The current [governed synthetic reconstruction](../../docs/report/synthetic-validation/reconstruction/README.md)
retains the scientific result and its synthetic-only limits.

The four later blobs were `4417a74d5d3a66e39839f7e39a9182387f045b40`
(`lra_validation/known_landscape.py`),
`821d24907f9ffbfd3db1b69296b0eb25868d4b93` and
`1d3a665089d71d18bc915ddc4e62f5cf90921965` (the source and test package
initializers), and `23a60a3a775a00b7b689d65702a45ec1395a046e`
(`test_known_landscape.py`). All four paths are under
`packages/bijux-pollenomics-dev/`.

The host challenge and development sweep contain distinct report values and
run scripts. We copied the two unique result JSON files, development policy,
both historical run scripts, shared snapshot preparer and sweep trial ledger
source into the [host challenge](../science/synthetic-host-challenge/README.md)
and [model selection](../science/synthetic-model-selection/README.md) reports.
The copies are exact and source-locked. A one-pass comparison of the two frozen
snapshots to their declared Git commits found no missing base paths:

| Snapshot | Declared Git commit | Exact base paths | Extra paths | Changed base paths |
| --- | --- | ---: | ---: | ---: |
| Host challenge | `70ddf5085ea8fef060f359ef0a4ddc719fb5cb68` | 1,519 / 1,520 | 2 | 1 |
| Development sweep | `d915d1709d3c8fca4680f70958452860d578d5d1` | 1,521 / 1,521 | 1 | 0 |

The extra or changed blobs do not occur in reachable Git history. One host
extra is an earlier experiment ledger; the model-selection source custody
instead contains the later ledger from the development snapshot and its
declared Git commit. Both snapshots include the same generated engine `_build_version.py`
(`0.1.9.dev121`), and the host snapshot has a changed fieldwork
`lake_archaeology_sensitivity.py` source. The latter is outside the synthetic
producer's declared read set. The exact frozen packages, original requests
and trial outputs are retained in the private archive described below. The
one-pass audit was retained locally at
`artifacts/jobs/report-owner-proof/known-landscape-snapshot-audit.json`,
SHA-256 `3c8bc0a885c746bfdfc5b65a8ff39a5af0d9a6c358bc348746abbe4db106962d`.

We placed both exact historical subtrees in one private source-custody archive
and checked every member against its original file before deletion. The
[durable receipt](artifact-custody/known-landscape-runs.json) records 3,325
regular files, 31,943,300 uncompressed file bytes, a complete sorted
path/content index digest and archive SHA-256
`6476ff26bbe038f57beccbba7b0c703a25941ea111c0a7f24b18e132b97256a6`.
The selected directories had no symlinks, hardlinks, open handles or producer
processes. We retired `host-challenge/` and `development001/` under
`artifacts/v3/known-landscape/`. The archive is a private historical replay
closure; the owned reports above carry the numeric results and their
scientific limits without depending on artifact paths.

The two remaining known-landscape prefixes contained eight regular files and
16,265 bytes. `agent001/` held a snapshot preparer and four plans, with no
local numerical output after its source checkout was retired. The
`development-challenge001/` result independently audited all 12 synthetic
trial envelopes and the candidate ranking; we retained its exact
[result](../science/synthetic-model-selection/independent-ledger-audit.json)
and [source text](../science/synthetic-model-selection/producer-source/verify_challenge.py.txt)
with the model-selection report. We also recalculated all 12 MAEs and six
candidate ranks from the retained trial report, matching the audit result.
The eight original files were checked byte for byte inside a second private
archive. Its [receipt](artifact-custody/known-landscape-remaining-records.json)
binds archive SHA-256
`13145fcef165e4d759adc0cafce080c53a709058768998c0c48b0ccc158de09d`.
No live process or open handle used either prefix. We retired those exact
directories and removed the now-empty `known-landscape/` parent; this does
not apply to any other `artifacts/v3/` material.

## EMPD2–NFI check plans

We separately retired `artifacts/v3/science-empd2-nfi-5a0ec4ea/` and
`artifacts/v3/science-empd2-nfi-frozen-5a0ec4ea/`. After the earlier removal
of their cache directories, these prefixes contained only ten check plans,
16,966 bytes in total, and no terminal results. They named focused pytest,
Ruff, formatting, typing, real-source and schema checks. We did not convert
plans into passing checks or alter the governed
[zero-pair scientific decision](../../docs/report/validation/empd2-nfi-pairing/README.md).
The exact plan bytes are in private custody, bound by
[this receipt](artifact-custody/empd2-nfi-plans.json) and archive SHA-256
`84c8c80e45d7e53962a355ea9847d15f1659cc7411f4783a894f558c98c8fe34`.
All ten members matched their original bytes. No symlink, hardlink, live
consumer or open handle was found for either selected prefix. Other v2 job
receipts and v3 source artifacts were outside this retirement.

## Historical SBOM checks

We retired four inactive `artifacts/v3/tox-sbom-*` prefixes after checking
their exact members and open handles. The diagnosis file explains an old
all-extras environment audit failure. Two subsequent order probes exited 2
without completing phases; the third exited 0 with the declared
`clean/prod/dev/summary` order. These are historical process results, not
current package security or SBOM validation. Later clean candidate SBOM
factors have their own terminal receipts; we do not substitute these old
checks for them.

We placed all 14 regular files, 18,846 bytes, in private custody and compared
every archive member byte for byte before removing the four exact artifact
directories. The [custody receipt](artifact-custody/sbom-history.json) records
every original path and SHA-256, the per-probe outcome, and archive SHA-256
`1a6f7cb42872d68bcf6c897bfbf72f26e3b847e14969b916b5384482b49de63a`.
No symlink, hardlink or open handle was found. The wider v3 tox, source and
release trees were outside this decision.

## Released LandClim author acquisition

We [retired the duplicate author checkout](artifact-custody/landclim-author-acquisition.md)
after matching all 51 author files to the private source capsule and retaining
the original archive, commit response and acquisition receipt there. The
source-specific account records its exact hashes, test consumer and limits.
