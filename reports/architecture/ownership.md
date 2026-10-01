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
