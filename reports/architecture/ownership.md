# Why we separate research decisions from generated reports

## Our decision

We use root [`reports/`](../README.md) as the reader's route from a question
to a result, its source and its limits. A domain report owns one scientific
interpretation. The [claim index](../evidence-index.md) links that
interpretation to the governed numeric rows and maintained producer. The
[`reports/needed/`](../needed/README.md) register holds genuine unanswered
source questions; completed work and execution plans do not belong there.

We keep `docs/report/` as an active governed output and website source tree
while its producers still write there. We move a result only with its
producer, tests, manifest and incoming citations, so it has one numeric
owner after the move. A former website path may remain as a short citation
to that owner. Selected rights-safe explanations appear under `docs/public/`;
the [PDF briefings](../../presentation/README.md) cite locked report versions.
We treat untracked `artifacts/` as disposable. Any current consumer that still
requires an old run path violates this ownership boundary and needs migration.

This separation matters because the current `docs/report/` tree has multiple
owners. The repository publisher, source consumers, numerical studies and
website assets do not share one regeneration command. An isolated
`publish-reports` run can repeat its own outputs without reproducing every
tracked file produced by those other owners. We therefore require a
producer-specific replay and tracked-byte comparison before claiming that a
migrated result is reproducible. The [report verifier](../verify.py) checks
reader inventory, local links and selected source identities; the
[scientific verifier](../../docs/report/pollen-reconstruction/verify_report.py)
checks its governed result set. Neither alone proves a full clean-tree
rebuild. The [rebuild policy](../../configs/ci/reproducible-report-build.json)
must be satisfied against every actual producer before that broader claim.

Our source-bound vegetation results illustrate the boundary: the
[Färskesjön](../science/vegetation-reference/farskesjon/plot_support.py),
[Småland historical-map](../science/vegetation-reference/smaland-historical-maps/coverage.py)
and [published-figure](../science/vegetation-reference/southern-sweden-figure/compare.py)
producers and numeric outputs live beside the
[vegetation decision](../science/vegetation-reference.md). Their exact
source replays do not create an independent measured-vegetation pair for our
predictions. The current science report states that limit directly.

We keep private licensed inputs in the qualified source store and record
their acquisition conditions and content identities with the consuming
domain. The tracked report should explain a result and its missing inputs
without requiring the private bytes to be present. Historical run
directories, deletion receipts and archive-member inventories do not belong
in this reader library.
