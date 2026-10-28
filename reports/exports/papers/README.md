# Standalone main-paper accounts

These A4 PDFs preserve the canonical [main-paper accounts](../../science/paper-accounts.md):
assumptions, worked findings, original versus repository results, tables,
diagrams, citations, unresolved causes and reproduction/source-request routes.
They can be read without opening the repository or website. Opening linked
underlying evidence requires network access or a separately supplied source
copy; restricted raw source packets are not embedded.

| Paper | Standalone PDF |
| --- | --- |
| Githumbi et al. (2022), LandClim II | [Regional reconstruction](landclim-regional-reconstruction.pdf) |
| Theuerkauf and Couwenberg (2024) | [LOVE and LOVEoptim](love-optimized-local-inference.pdf) |
| Sugita (2007a) | [REVEALS theory](regional-reveals-theory.pdf) |
| Sugita (2007b) | [LOVE theory](local-love-theory.pdf) |
| Hellman et al. (2008a) | [Regional validation](southern-sweden-regional-validation.pdf) |
| Hellman et al. (2008b) | [Sampling and parameters](southern-sweden-sampling-design.pdf) |
| Gaillard et al. (2010) | [Southern Swedish figure comparison](southern-sweden-validation-synthesis.pdf) |
| Cui et al. (2014) | [Småland maps](smaland-historical-map-reference.pdf) |
| Tabares et al. (2021) | [Namibian observations](namibia-modern-pollen-vegetation-reference.pdf) |

The [manifest](manifest.json) binds each PDF to its canonical source and
committed renderer, compiler versions, deterministic clock and build receipts.
The [layout record](visual-review.json) records model inspection of every page,
font embedding, representative Unicode, extractable text order and citations.
All retained pages are readable without clipping. Every paper includes its nine-field scientific verification and limits account. Six exports retain their reviewed source revision; LandClim, REVEALS theory and Namibia were separately rebuilt after safe line-break corrections to long paths or inline formulas. Their per-paper records identify the actual source revision and producer. These PDFs are untagged;
this review does not establish assistive-technology accessibility, actual
colleague comprehension or qualified scientific approval.

Repository citations use full commit-pinned GitHub URLs; primary DOI citations
remain direct. Local path resolution and PDF annotations are checked. Online
availability of the newly committed repository pages remains unverified.
Partial primary-paper access and missing scientific data retain the statuses
in the canonical reports; a portable export cannot strengthen those findings.

Run `python3 reports/exports/papers/verify.py` from the repository root to
reconcile inventory, source revisions, producer hashes, retained PDFs and
page-review identities. `python3 reports/verify.py` includes that check.
The producer check reads the exact historical renderer revision declared by
each export, including separately rebuilt papers. A later renderer revision
does not change an already reviewed PDF's provenance. Current canonical report
text, retained PDF bytes and page-review identities must still match.
Changes to a canonical account invalidate its PDF until it is rebuilt and
reviewed; changes to source admission require the owning scientific review too.

To rebuild the retained candidate, use the producer/source revision recorded
in the manifest, the locked `reports` extra and the fonts/toolchain described
in the [renderer instructions](../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/README.md).
From that repository checkout, write to an absent artifacts directory:

```sh
SOURCE_DATE_EPOCH=1790812800 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.reader_reports \
  --repository . --inventory reports/science/paper-accounts.csv \
  --output artifacts/jobs/paper-pdf-replay
```

Keep the source revision fixed to reproduce its URL annotations. A later
revision can contain identical report text but produce different PDF bytes
because the commit-pinned links differ. Font/compiler changes also require
new layout verification. Retain only accepted PDFs and their reviewed
manifest; build intermediates stay under `artifacts/`.
