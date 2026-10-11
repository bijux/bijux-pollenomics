# Canonical paper PDF exports

This maintainer command converts the reports named in
`reports/science/paper-accounts.csv` to standalone A4 PDFs. The canonical
Markdown reports remain the editorial authority. Conversion preserves their
text, tables, citations and the declared flowchart grammar; it refuses
unsupported markup instead of dropping it.

Install the developer package's `reports` extra, or use the repository's
locked development environment. External prerequisites are `latexmk`,
XeLaTeX and Graphviz `dot`, with STIX Two Text, Arial and Menlo fonts available
to the TeX installation. Builds embed the selected font subsets. The report
renderer uses these named fonts rather than claiming identical layout across
unqualified systems; the receipt records compiler versions.

From the repository root, choose an output directory that does not exist:

```sh
SOURCE_DATE_EPOCH=1790812800 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.reader_reports \
  --repository . --inventory reports/science/paper-accounts.csv \
  --output artifacts/jobs/paper-pdf-export
```

The inventory and all canonical reports must match the identified committed
revision. `--paper-id` selects one paper while still checking the complete
inventory. Local citation targets are resolved inside the repository and
converted to commit-pinned GitHub URLs. The command validates their local
existence; remote availability is explicitly unverified. Publisher and DOI
URLs remain direct. Offline reading includes the complete report and diagrams;
linked raw evidence requires a separate copy or network access.

Every export has a receipt recording source, producer, TeX, diagram and PDF
hashes, tool versions and the deterministic clock. Logs and intermediate files
stay beside each PDF under `artifacts/`. Diagram compilation is limited to 25
seconds and each report's LaTeX compilation to 180 seconds. There are no
automatic retries. A timeout or compile error refuses that export; inspect its
log, correct the owned source or environment, and rerun into a new directory.

Build success does not promote a PDF. Inspect every page, font embedding,
text extraction and citations against the receipt before retaining an export
under `reports/exports/papers/`. PDFs are currently untagged; text extraction
and model layout review do not establish assistive-technology accessibility
or actual reader comprehension. Source permissions, missing scientific inputs
and qualified review retain the statuses stated in the canonical reports.
