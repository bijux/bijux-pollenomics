# Our LandClim metadata integrity check

We independently checked the LandClim full-study metadata bundle. The
[result](result.json) records eight passing checks and nine adversarial edits
that the tested reader rejected. It used the pinned public workbook and
inventory to reconstruct all five bundle outputs, checked 1,128 metadata rows
and 4,512 explicit requirement refusals, and compared two isolated
generations. All five result hashes still match the [governed
files](../../../../docs/report/publication-replay/landclim-study-inputs/README.md).
The independent checks ran against the source revision identified in the
machine result; current output identity does not prove current reader-code
identity or repeat those nine adversarial executions.

The result's verdict is `pass_scoped_metadata_bundle`. Its source boundary
explicitly reports zero authenticated historical pollen counts, zero historical
chronologies, zero historical/current revision matches, zero cleared per-sequence
rights and no publication-specific R execution. We do not use this metadata
check as full ESSD reproduction, empirical LRA admission or ecological accuracy.
The result and current-product hash check preserve that bounded verdict. They
do not provide the missing historical study inputs.

From the repository root, check that the retained verdict and five exact
product identities still agree:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/publication-correspondence/landclim-metadata-integrity/verify.py
```
