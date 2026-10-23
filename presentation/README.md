# Research presentations

These three PDF briefings describe the same governed research from different
reader needs:

| Audience | LaTeX source | Final PDF |
| --- | --- | --- |
| Project and collaborators | [Big picture](big-picture.tex) | [Big picture PDF](big-picture.pdf) |
| Implementers | [Developer](developer.tex) | [Developer PDF](developer.pdf) |
| Researchers | [Scientific evidence](scientific-evidence.tex) | [Scientific evidence PDF](scientific-evidence.pdf) |

The retained decks were compiled from Git revision `86d7c77ad` on
23 October 2026: 14 big-picture, 13 developer and 43 scientific pages.
The three compiler commands completed successfully in 8.27 seconds overall.
Local review inspected all 70 pages and enlarged changed or dense slides;
all fonts are embedded and all 112 citation annotations match their authored
paths and existing local targets. No rendering defect was observed. This is
numerical, machine and model visual review; independent human comprehension,
tagged accessibility and online availability remain unqualified.

Run `python3 presentation/build.py` from the repository root with `latexmk`
and a working TeX distribution. Intermediate files and the compiler log go
to `artifacts/jobs/presentation/`; only the final PDFs are retained here.
The build requires committed, unchanged copies of the three authored TeX
files, `shared.tex` and `build.py`. The download manifest records their actual
Git revision, compiler commands and exits, and PDF byte identities. A cited
report is an evidence reference, not a compiled input. Review scientific claims
and run the relevant report validators before building; changing ordinary
prose or unrelated code does not require refreshing an inventory of hashes.
The compiler recorder refuses undeclared repository inputs. Historical
`source-lock.json` and export contexts retain their original execution epochs;
they are not rewritten to describe a new build.
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


## Retained scientific deck publication

The [16 October 2026 publication packet](https://github.com/bijux/bijux-pollenomics/tree/891664fe4579c6ef0d9481fe1b0ae7df307ce438/presentation) preserves the original [big-picture PDF](https://github.com/bijux/bijux-pollenomics/blob/891664fe4579c6ef0d9481fe1b0ae7df307ce438/presentation/big-picture.pdf), [developer PDF](https://github.com/bijux/bijux-pollenomics/blob/891664fe4579c6ef0d9481fe1b0ae7df307ce438/presentation/developer.pdf) and [scientific-evidence PDF](https://github.com/bijux/bijux-pollenomics/blob/891664fe4579c6ef0d9481fe1b0ae7df307ce438/presentation/scientific-evidence.pdf), with their five project build-source inputs and recorded publication context. Its retention commit is separate from the original producer identifier `0caba19fdca39e183dce2b1a3929d1b94495cc21`; two reviewed TeX overlays are declared in the retained context.

The historical 121-entry watchlist contains cited evidence as well as project inputs. The retained source context owns 119 exact watchlisted source bodies; two noncompiler citation bodies retain their identities without a portable public-source counterpart. The publication packet retains all five project build-source files. Its machine checks and bounded model review remain scoped historical observations; unfamiliar-human review, tagged accessibility and the PPTX decision remain open. Current PDFs and their five-input build authority remain unchanged.
