# Artifact retention and cap inventory

This report records a bounded V3-26 inventory of this repository's root
`artifacts/` tree. It authorizes no deletion. The machine-readable result is
[`report.json`](report.json); the raw measurements and refused scans are under
`artifacts/jobs/artifact-retention/`.

## Cap result

The exact cap is **800,000,000,000 bytes**. A native macOS `du` apparent-size
traversal finished with exit code 0 and empty stderr after 240.25 seconds. It
reported 1,370,245,364 units of 512 bytes. The conservative upper bound is
**701,565,626,368 bytes**, leaving at least **98,434,373,632 bytes** below the
cap at the time of that traversal. The command was
`du -A -B 1 -l -s <repository>/artifacts`: `-A` measures apparent size,
`-B 1` calculates in one-byte blocks, and `-l` counts each hardlink path.
The displayed total is rounded to 512-byte units. The tool did not follow
symbolic links. Its exact command, raw stdout, stderr, exit code, time bound,
and conversion are in `artifacts/jobs/artifact-retention/native-du-receipt.json`.

This was **not an atomic snapshot**. Atlas and source-validation jobs produced
small artifacts during the traversal. The margin is much larger than those
observed jobs' outputs, but this result does not certify an immutable byte
total or future compliance. A substantial new job should check the cap again.

The Python metadata inventory deliberately stopped at 12,000,000 entries in
401.51 seconds, after counting 570,897,310,425 path-apparent bytes. Its
`indeterminate_incomplete_scan` decision remains in `report.json`; the native
check supplies the separate whole-tree cap observation. An earlier 2,000,000
entry refusal is retained as `initial-scan.json`, and the 12,000,000 entry
measurement is retained as `metadata-scan.json` in the artifact-retention job
directory. Neither partial measurement was extrapolated into a total.

## Evidence and liveness

The metadata walk used `lstat`, did not follow symlinks, counted each path's
apparent and allocated bytes, and tracked unique inodes separately. Its partial
walk observed 24,070 symbolic links and one repeated hardlink path. Its
top-level and selected-prefix byte totals are **partial** because the entry
bound stopped the walk. Ordinary file contents were not hashed.

Six selected files were content-hashed. Four matched independently declared
digests: the R 4.6.0 source archive in the source lock, the source-built R
runtime and private-library receipts in the Linux R report, and the retained
raw numerical receipt matching the governed Linux R report. The source-drift
refusal receipt and container-build log have recorded new digests and remain
protected as potentially unique process evidence. Five of the six have an
independent directory-level report reference; the build log has no such
independent reference, so its absence of references is **not** evidence that
it is disposable. Exact file mentions originating in the inventory producer
are excluded from the `independent_reference_origins` classification.

The durable-reference search read 2,531 eligible files from report,
configuration, workflow, and source locations and found 215 artifact-path
mentions. It skipped one file above the eight-megabyte per-file limit, and
other repository locations were outside this bounded search. Consequently,
reference absence is not a proof of unreferenced status. The walk found no
parseable `process.json` PID receipts; this limited process snapshot cannot
establish that any candidate is inactive. Private external source storage is
outside the repository artifact tree and was not inventoried or purged.

## Retention decision

Three exact cache/test-output paths have recorded regeneration commands:
`artifacts/jobs/linux-r-oracle/mypy-cache` (13,640,160 partial-scan apparent
bytes), `artifacts/jobs/linux-r-oracle/test-run` (6,635 bytes), and
`artifacts/jobs/neotoma-first-observed/mypy-cache` (22,077,920 bytes). They are
review candidates only. Their combined 35,724,715 bytes cannot materially
change the cap result. Inactivity and unique-proof absence have not been
independently established, so this inventory authorizes **no removal**.
