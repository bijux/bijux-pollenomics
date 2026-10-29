# Scientific execution reference sources

These reference programs retain the exact first-party source bodies used by
scientific capture controllers, observers and their controls. Their ownership is
organized by scientific domain, source family and execution responsibility.
Shared byte-identical consumers and runtime validators have one reference owner.
Distinct captured versions of a source role remain in ordinary Git history.

Capture transports bind a reference path and its exact ancestor revision, Git
blob, SHA-256 and byte length. Readers authenticate those source bytes in memory;
they do not import the reference programs. Original relative paths, bare imports
and interpreter assumptions remain part of the captured source. A reference
storage revision does not establish that those programs ran at that revision or
that relocation preserves their execution behavior.

The original execution candidates, input identities, scientific outputs and
failed outcomes remain in their captures. Active capture readers live in
`bijux_pollenomics_dev.ci.report_rebuild.scientific_captures`; the strict Git
transport is documented in its sibling `retained_source` package. Superseded
reference bodies stay available through the exact source revisions named by the
transports, independently of the current checkout's source version.
