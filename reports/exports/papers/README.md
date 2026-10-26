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
The library contains **nine PDFs and 53 pages**. Every paper includes its
nine-field scientific verification and limits account. The five Sugita, Hellman
and Namibia exports reflect their supplied full primary sources; their **29
pages** were individually inspected after native text, font, citation and
physical-bounds checks. Four other PDFs retain their exact historical bytes,
source/producer/build identities and page-review records. Three inherited
historical source/receipt identities are now explicit in the manifest because
the shared inventory has changed.

The first Hellman regional export compiled successfully but lost the
“at least” symbol in its selected font. That layout-refused candidate and
its diagnostics remain under `artifacts/raa-reconciliation/paper-exports/`.
Only the separately committed wording repair was rebuilt; no numerical or
scientific finding changed. The other four updated candidates retain source
revision `84a0f2bec7906a247573a2b73c111b752ec17491`; Hellman regional uses
`133447b8ae71754d9799355b9c6af48f2fa74711`. All accepted pages are readable
without clipping or missing glyphs. Per-paper records identify the actual
source, producer and receipt. These PDFs are untagged;
this review does not establish assistive-technology accessibility, actual
colleague comprehension or qualified scientific approval.

Repository citations use full commit-pinned GitHub URLs; primary DOI citations
remain direct. Local path resolution and PDF annotations are checked. Online
availability of the newly committed repository pages remains unverified.
Full main-paper receipt and missing original numerical/scientific inputs retain
the separate statuses in the canonical reports; a portable export cannot
strengthen scientific acceptance.

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
  .venv/bin/python -B -m bijux_pollenomics_dev.reader_reports \
  --repository . --inventory reports/science/paper-accounts.csv \
  --paper-id regional-reveals-theory \
  --output artifacts/jobs/regional-reveals-paper-pdf-replay
```

Select one `--paper-id` from the manifest and its actual source revision; the
command checks the whole committed inventory but builds only that paper. Keep
the source revision fixed to reproduce its URL annotations. A later
revision can contain identical report text but produce different PDF bytes
because the commit-pinned links differ. Font/compiler changes also require
new layout verification. Retain only accepted PDFs and their reviewed
manifest; build intermediates stay under `artifacts/`.
