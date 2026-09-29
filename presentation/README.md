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

Each result slide names its repository evidence path. The reports under
[`reports/`](../reports/README.md) lead to numeric tables, input manifests,
reproduction commands and limitations. Source-specific results, previously
inspected development outcomes and still-open external inputs are stated on
the slides. The PDFs contain summaries and repository paths, not private
raw source material.
