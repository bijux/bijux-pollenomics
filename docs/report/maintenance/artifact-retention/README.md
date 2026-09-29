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

## Historical Nordic tox snapshots

The [Nordic tox snapshot custody record](nordic-tox-snapshots.json) preserves
the candidate commit and tree, candidate-manifest digest, and every available
lane-result digest and exit code for seven historical snapshots. All seven
candidate trees still resolve from Git. Each snapshot's nine scientific fixture
files matches the private author-reference source store byte for byte. The
record also keeps the selected failure lines from completed lanes. Two
snapshots have no lane result, and several completed lanes failed; none is a
current candidate certification.

The snapshot inputs are copies of Git-tracked files and those nine author
fixtures. Lane run directories contain installed environments, caches, build
products, test output and repeated input copies. This identity check makes
each snapshot a candidate for **selective** removal after its process liveness
and exact retained evidence are checked. It does not change the no-removal
decision for other artifact paths in the original inventory.

The `7bb6a614` snapshot was removed after its five recorded lane processes
were confirmed absent. Its five lane outcomes, including the failed map-legend
test, remain in the custody record. The other six exact snapshots were then
removed after verifying each candidate-manifest digest and every available
lane-result digest against committed custody. All seven paths are absent, while
all seven candidate Git trees still resolve. Their prior path-apparent total
was at most **182,010,481,152 bytes** at the earlier native `du` scan. This is
not a measurement of physical disk space freed because copies can share blocks.

The [complete lane receipts](nordic-tox-lane-receipts.json) retain all 19
available lane-result objects from the six later removed snapshots, including exact
environment and JUnit identities. Each original receipt byte hash was checked
against the custody record before inclusion. The earlier removed snapshot has
only its compact outcome record; its full lane objects were not retained.

## Linux R oracle input and build custody

The [R oracle retirement receipt](linux-r-oracle-retirement.json) records three
subsequent exact removals: the v2 locked source cache, the source-built R
runtime tree, and the provisioned private R library tree. Their source-lock
archives, **1,227 runtime files**, **2,784 library files**, and **130 acquisition,
build and provision process files** were first checked and retained in the
private `lra-reference/` store. Its custody manifest has SHA-256
`0398b643a2124ce44d9854a6979b1939c6c93337ddea30d1e030439de44d3575`.
The three recorded process IDs were absent before removal. The unpacked R source
and build intermediates were generated from the locked archive; the original
receipts and step logs remain in private custody. The governed
[Linux R oracle report](../../method-certification/linux-r-oracle/README.md)
now uses that custody for reproduction. Other v2–v5 artifact paths were not
covered by this retirement decision.

## Rootsi workbook structural review custody

The [Rootsi review retirement receipt](rootsi-workbook-review-retirement.json)
records two exact local replay directories whose five scientific outputs were
byte-identical. The private `landclim/rootsi-workbooks/structural-review/`
store retains one checked copy of each output and both original manifests;
the manifests differ in their producer file identity. Its custody manifest
has SHA-256
`f718e3d954e655968af804b94d5ab52bde9bddf922cda4ba9e506c7f4e97adb3`.
The 5,170 row candidates and 7,459 header positions remain private because
source rights and scientific semantics are unresolved. The two replay
directories were removed only after byte checks, liveness review, and private
copy verification. This decision covers no other Rootsi or v2–v5 artifacts.

## Publication correspondence custody

The [publication correspondence retirement receipt](publication-correspondence-retirement.json)
binds four derived files from one v5 artifact directory. The repository's
current correspondence CSV contains all nine retired result IDs plus a newer
classification row; its interpretation records the numerical limits and the
five exact unsent source-owner questions. The inspected LOVE paper PDF has
separate private source custody. No repository consumer or live open file
depended on the retired directory at removal. This decision does not certify
historical publication input equivalence or affect any other artifact path.

## Earlier scientific report provenance

The original six generated files in the LandClim author-example and published-window
correspondence runs are retained in the governed [author ledger](../../publication-replay/landclim-author-example-correspondence/README.md)
and [published-window ledger](../../publication-replay/landclim-published-window-correspondence/README.md).
Each ledger manifest records the original byte size and SHA-256; the two CSVs
match after CRLF-to-LF normalization, and the Markdown and JSON match exactly.
The two original output directories were retired after checking those six
files, single-link regular-file status, absence of symlinks and open handles,
and repository consumers. Historical report snapshots retain their original
path strings as provenance, not live read dependencies. Other correspondence
plans, caches and runs remain pending separate custody review.

The [remaining correspondence retirement receipt](landclim-correspondence-retirement.json)
records the 46 file and symlink entries left in the two bounded working
directories, including their process plans, earlier numerical reports and
pytest products. Both earlier row-level CSVs equal the governed ledgers after
newline normalization. Shared JSON values also agree: the final author report
adds explicit zero missing and extra key counts, while the final
published-window report names the author site count and signed extreme taxa.
The original final outputs remain bound by the
two ledger manifests. Four pytest symlinks point within the retired directories;
no regular file has another hardlink, no file was open, and no current repository
consumer reads either directory. The historical snapshot's old artifact paths
remain provenance strings. This retirement changes no scientific admission.

The [earlier Swedish direct-pollen run](historical-swedish-direct-pollen-run/README.md)
retains its unique producer, input manifest and report bytes. Its custody ledger
maps the other 12 files to byte-identical or newline-normalized current study
outputs, so the inactive 15-file working directory can be retired without
losing its scientific or process record.

The [author-example holdout retirement receipt](author-pollen-holdout-retirement.json)
binds the 33 remaining file and symlink entries in its working directory. The
governed holdout contains the verified numerical report and newline-normalized
prediction and score ledgers. The unique [unsent Swedish LRA source request](swedish-lra-source-request/README.md)
is retained byte for byte with its historical status explained; current Swedish
source questions supersede its admission claims. No file was open or had another
hardlink, and the sole repository path mention is historical replay provenance.

The [buffered author-pollen retirement receipt](author-buffered-pollen-retirement.json)
binds 577 regular files and 56 internal symlinks from the earlier two-grid
spatial-block working directory. The [governed English study](../../pollen-reconstruction/author-buffered-pollen/README.md)
retains the four final prediction and score chains, paired baseline/taxon and
Hellinger diagnostics, fixed fitted comparison, and strict CLR support result.
Current consumers reproduced all four governing comparison reports from the
retained inputs. Earlier baseline and site reports add no non-schema values
to the retained taxon report; the remaining plans and fixtures are process
products. No file was open or multiply linked, and no live report or package
consumer reads the retired directory. Scientific admission is unchanged.

The [Swedish site comparison retirement receipt](swedish-site-identity-retirement.json)
binds 25 process and result files from the earlier 37-site cross-source review.
The governed [current comparison](../../source-relations/neotoma/landclim-site-identity/README.md)
uses the 77-site prerequisite projection and includes all 37 earlier rows with
identical values. Its manifest retains the old selection IDs and summary, so
the earlier denominator remains interpretable after the working directory is
removed. No open file, multiple hardlink or live consumer depended on it.

The [Abborrtjärnen core retirement receipt](abborrtjarne-core-retirement.json)
binds 67 files and two local pytest symlinks from the old core comparison
working directory. The governed [core lead](../../source-relations/neotoma/abbo-core-identity/README.md)
replays the scientific fields using the current prerequisite projection and a
selected independent count-mass receipt. The governed
[workbook comparison](../../source-relations/neotoma/abbo-native-correspondence/README.md)
retains the native-count summary; its private per-sample CSV is reproducible
from retained source inputs. All four old native-count reports match that
summary exactly. No file was open or multiply linked, and the only repository
path mention is historical.

The [two-lake core retirement receipt](swedish-lake-core-retirement.json)
binds 61 files and two pytest symlinks from the earlier Bussjösjön and
Bökesjön working directory. The governed [core and age comparison](../../source-relations/neotoma/swedish-lake-core-identity/README.md)
reproduces its final scientific fields using current prerequisite inputs and
two selected independent count-mass rows. The governed BUS and BOKE native
reports retain their source summaries and add later diagnostics; private
cell-level CSVs remain reproducible from the retained source inputs. No file
was open or multiply linked, and the sole repository path mention is
historical.

The [published-window retirement receipt](landclim-published-window-retirement.json)
binds 98 files and 13 pytest symlinks from the earlier time-window and
numerical-provenance workspace. Governed reports now retain the
[three-way numerical ledger](../../publication-replay/landclim-published-window-provenance/README.md),
[reported uncertainty envelopes](../../publication-replay/landclim-published-window-uncertainty/README.md)
and [25-window axis comparison](../../publication-replay/landclim-window-alignment/README.md).
Their manifests bind original final outputs and current source inputs. The
early runs are superseded by those checked results; no live consumer or open
file depends on this working directory.

The [earlier scientific report provenance](scientific-report-provenance/README.md)
retains exact results, scope, and evidence-manifest bytes from the previous
11-result study. The current report has 17 result rows and a passing 170-file
verifier. The historical manifest records the earlier input closure and is not
a live source of report claims or a valid check against the current worktree.
Its ten-row Swedish question artifact is now retained byte for byte beside that
snapshot, with a [custody receipt](scientific-report-provenance/source-questions-custody.json)
and a mapping to the current source questions. The original one-file artifact
directory was retired after its exact hash, file type, links, consumers and open
handles were checked.

## Author pollen development custody

The [author development custody record](author-pollen-development-custody.json)
binds two byte-identical six-file artifact directories to the governed 17-site
exploratory study.
Design and interpretation bytes match exactly. Predictions match after
decompressing the retained CSV. Coverage, scores and leaderboard contain the
same ordered records; only CRLF versus LF line endings differ. The current
scientific report verifier authenticated those retained outputs. No product
consumer or live open file depended on either retired artifact directory. This
does not turn previously exposed development outcomes into confirmatory data.

## Scientific source refusal custody

The [source refusal custody record](scientific-source-refusal-custody.json) binds
four earlier derived notes to their exact hashes and current repository evidence.
Their HYDE, Swedish LRA, vegetation and Nordic scientific limits remain open
where source admission is unresolved. The older Nordic screen counts are
historical; current country pollen results and source screens supersede them.
Only the four recorded inactive note directories were retired. The retained
scientific-report provenance may still name their former paths as historical
evidence, not as live report inputs.

## Swedish direct-pollen run copies

The [Swedish run custody record](swedish-direct-pollen-run-custody.json) binds
two complete derived copies of the three-lake direct-pollen study. Their 13
relative files matched each other byte for byte. All 12 scientific data and
manifest files in each copy also match the governed
[Swedish report](../../pollen-reconstruction/swedish-direct-pollen/REPORT.md).
The older run README lacks the report's later parameter-coverage finding and
reproduction instructions. The two inactive copies were retired after exact
file, link, consumer and open-handle checks. The original v5 working directory,
which contains a distinct historical producer and earlier tables, remains
outside this decision. Its `run_study.py` is 27,190 bytes with SHA-256
`b219e8bbe362f89010ac10642c298eb4a45127b75d9148252b76a33046e66fa9`,
matching its own input manifest but differing from the governed producer. Its
unique process bytes remain protected pending durable source custody.

## Nordic pollen plan

The [Nordic plan custody record](nordic-pollen-plan-custody.json) retains the
exact 969-byte text and SHA-256 of an unexecuted v5 configuration. It listed
Denmark as unavailable and proposed only Finnish and Norwegian holdouts. The
governed [country pollen study](../../regions/nordic/direct-pollen/RESULTS.md)
now scores Denmark, Finland and Norway with explicit denominators. The old
one-file directory had no open handle, and a bounded source, documentation,
configuration and data search found no consumer. It was retired after its exact
text was verified in the custody record. Its historical assumptions do not
supersede the governed study.

## Rootsi replay process custody

The [replay custody record](rootsi-replay-process-custody.json) covers two
inactive interrupted structural-review directories. Eight result files match
the existing private review custody by exact SHA-256. The ninth file is a
distinct manifest, now retained in the private source store with its own
metadata receipt; it differs from the two earlier manifests only in a producer
hash. The historical producer bytes for that hash are unavailable, so the
manifest does not authenticate a new scientific transformation. The source
workbooks, unqualified rights and refused LRA use are unaffected. Both
interrupted directories were retired after file, handle and bounded consumer
checks.
