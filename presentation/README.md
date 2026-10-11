# Research presentations

These three PDF briefings describe the same governed research from different
reader needs:

| Audience | LaTeX source | Final PDF |
| --- | --- | --- |
| Project and collaborators | [Big picture](big-picture.tex) | [Big picture PDF](big-picture.pdf) |
| Implementers | [Developer](developer.tex) | [Developer PDF](developer.pdf) |
| Researchers | [Scientific evidence](scientific-evidence.tex) | [Scientific evidence PDF](scientific-evidence.pdf) |

Run `python3 presentation/build.py` from the repository root with `latexmk`
and a working TeX distribution. Intermediate files and the compiler log go
to `artifacts/jobs/presentation/`; only the final PDFs are retained here.
The build checks the SHA-256 identities of cited reports, package contracts
and slide sources in `source-lock.json`. If one changes, review its affected
slides, then update that lock deliberately before rebuilding. This guard
prevents an older PDF from being silently presented as current evidence.
Each compiler invocation has a 180-second timeout. A timeout preserves its
log and refuses the build; inspect the affected source or TeX environment and
rerun after correction.

Each result slide names its repository evidence path. The reports under
[`reports/`](../reports/README.md) lead to numeric tables, input manifests,
reproduction commands and limitations. Source-specific results, previously
inspected development outcomes and still-open external inputs are stated on
the slides. The PDFs contain summaries and repository paths, not private
raw source material.

For a detailed offline source account, use the
[standalone main-paper PDFs](../reports/exports/papers/README.md).
The editable format currently delivered for these decks is LaTeX, with PDF
for reading and presentation. PowerPoint-compatible PPTX files are not yet
provided. Whether collaborators require PPTX remains a pending format
decision; LaTeX availability does not establish PowerPoint editability.
Actual audience reading checks remain open. The PDFs are untagged, so font
embedding and model visual review do not establish assistive-technology
accessibility.
