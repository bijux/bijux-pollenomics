# Retained public data downloads

`downloads.json` owns the exact fifty GeoJSON files served with the retained
scientific reports and browser observations. The manifest identifies each
committed source, byte count, hash and public purpose. The Swedish sequence
map's original GeoJSON remains a runtime resource of its independently
reconstructed report descriptor.

`admission.py` derives the publication policy from the accepted shared policy
and those exact download paths. The owning MkDocs configuration records the
adapter and manifest hashes, so the canonical source checkpoint binds both.
Admission and final verification reproduce the same effective policy. Missing,
changed, additional, wildcard, private or foreign source paths are refused;
all shared private-content, HTML, CSP, size and file-count checks remain active.

Python and R producer sources, numerical oracle arrays, raw execution logs,
original MOV footage and the source-only checksum manifest remain in Git.
They are excluded from the website. Published source references link to the
committed repository owners; the existing MP4 remains the fieldwork video.

Run `make docs-publication-controls` after changing this adapter or manifest.
These focused controls validate the download boundary. They do not run the
scientific producers or replace final source-bound publication verification.
