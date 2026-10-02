# How we own research reports

## Our decision

We maintain [root reports](../README.md) as the reader's path from a research
question to our decision, evidence and limits. The [claim index](../evidence-index.md)
links each interpretation to its numeric result and producer. The
[open evidence register](../needed/README.md) names the source questions that
still require an answer. A reader should not need a run directory or a backlog
to understand a result.

We keep `docs/report/` as a governed output tree because the publisher, source
consumers and numerical studies still own distinct paths there. Moving a
result requires moving or redirecting its producer, manifest, tests and
incoming citations together. A former website path may remain as a short
pointer to the new owner. We publish rights-safe explanations through
[`docs/public/`](../../docs/public/pollenomics/science/index.md) and lock the
sources cited by the [PDF briefings](../../presentation/README.md).

| Content | Owner and durable location | Reader route |
| --- | --- | --- |
| Research interpretation | Domain page under `reports/science/` or `reports/architecture/` | [Research library](../README.md) |
| Numeric result and exact source identity | Its maintained producer and governed output under `docs/report/` or the owning root study | [Claim index](../evidence-index.md) |
| Private source bytes | Qualified external source store, with repository source identity and permitted-use account | [Source cohort account](../science/source-cohorts.md) |
| Unanswered source question | `reports/needed/` until a source-bound result or decision resolves it | [Open evidence register](../needed/README.md) |
| Public explanation | Rights-safe page and version-locked briefing | [Public science](../../docs/public/pollenomics/science/index.md) |

## Why one rebuild command is insufficient

The [repository publisher policy](../../configs/ci/reproducible-report-build.json)
owns its country, region and foundation outputs. Independent producers own
other source, method and study results. Some publisher summaries read those
independent outputs, so the reducer receives verified owner files while it
builds summaries and removes them from the publisher-owned output afterward.
The final inventory assigns each report path one owner and compares the
combined output with tracked `docs/report/` in two independent lanes.

A producer replay binds its declared input bytes, command and exact output
paths. We review the input closure as well as the byte comparison; a matching
file does not authenticate a missing source, establish reuse rights or prove
that all other report owners have been rebuilt. The
[reader verifier](../verify.py) checks root pages, links and selected source
identities. The [scientific verifier](../../docs/report/pollen-reconstruction/verify_report.py)
checks its governed results. A complete report-tree rebuild is a separate
acceptance decision.

The current tracked report tree contains 1,938 files. Its navigation registry
indexes 1,934 surfaces and deliberately excludes its four registry/review
metadata files. Each indexed Markdown surface and its layout row carries the exact content
hash used by that consumer. Machine-readable products keep their domain
manifest identities, avoiding recursive hashes through the scientific
manifest that binds the portal outputs. The portal producer regenerates
11 navigation and inventory files from the other governed report inputs;
two isolated runs agree on all 11 outputs. This is a secondary consumer
check of existing result bytes. It does not independently reproduce the
scientific producers, the publisher's country bundles or the whole report
tree. Automated layout signals do not establish actual reader comprehension
or qualified scientific review.


## Current output declarations

The [output ownership inventory](../../configs/ci/report-ownership.json)
assigns every tracked report path exactly one declaration. Its population is
1,938 paths: 709 declared publisher paths, 125 original-R retained source
files, ten generated study outputs, 62 maintained source files, seven
maintained reader accounts and 1,025 paths with unresolved output custody.
These role counts describe the current declarations. They do not measure
how many outputs have been independently reproduced.

The publisher path set comes from the independent assembly inventoried at
product `bdc8c0d95`. All 709 paths remain tracked. A current publisher assembly
must still establish its exact output membership before full-tree acceptance.
The new declaration keeps the current-R and Linux-R raw outputs unresolved;
the original-R source category applies only to its separately authenticated
125-file bundle. A maintained source file or editorial account requires
source custody and review, rather than an invented generated-output proof.

Check the declaration without executing the scientific studies:

```sh
python -m bijux_pollenomics_dev.ci.report_rebuild.ownership --repository .
```

The checker compares the exact tracked namespace, path-set digest and unique
owner assignments; it rejects missing or extra paths, unsafe source paths
and generated owners that consume their own declared outputs. Adding
`--require-resolved` refuses any unresolved declaration. Even when every role
is resolved, this inventory check does not replace independent owner
manifests, retained-source certificate validation or the two-lane full-tree
comparison. Those checks remain with the existing report rebuild verifier.

The [method correspondence](../science/method-correspondence.md),
[publication correspondence](../science/publication-correspondence.md),
[observed-pollen synthesis](../science/pollen-prediction.md) and
[vegetation-reference decision](../science/vegetation-reference.md) state
their scientific scopes independently. Reproducing a numerical report cannot
turn a direct-pollen score into LRA validation or create a matched measured
vegetation pair.

Local `artifacts/` contains disposable execution products. We retain unique
source identities and lasting results with their domain owners before
retiring a run. Root reports explain the decision and its evidence; archive
member lists, deletion receipts and transient run names stay out of the
reader library.
