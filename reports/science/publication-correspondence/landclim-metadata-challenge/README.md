# Our independent LandClim metadata check

We retained an executed independent check of the LandClim full-study metadata
bundle. Its [exact result](result.json) reports eight passing checks and nine
adversarial edits that the candidate reader rejected. The candidate used the
pinned public workbook and inventory to reconstruct all five bundle outputs,
checked 1,128 metadata rows and 4,512 explicit requirement refusals, and
compared two isolated generations. We compared the result's five output hashes
with the [current governed files](../../../../docs/report/publication-replay/landclim-study-inputs/README.md):
all five still match exactly. The result was produced against historical
candidate commit `912cb7645d0a1d05750443b552830116b8313a1b`; matching output
bytes support the bounded metadata conclusion on today's retained product, not
unchanged code identity.

The result's verdict is `pass_scoped_metadata_bundle`. Its source boundary
explicitly reports zero authenticated historical pollen counts, zero historical
chronologies, zero historical/current revision matches, zero cleared per-sequence
rights and no publication-specific R execution. We do not use this metadata
check as full ESSD reproduction, empirical LRA admission or ecological accuracy.
The [custody receipt](../../../architecture/artifact-custody/landclim-metadata-challenge.json)
binds all 58 original run files and the historical challenge source to a
private archive. The archive can be used to inspect the old procedure and
adversarial products; it does not provide missing historical study inputs.

From the repository root, check that the retained verdict and five exact
product identities still agree:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/publication-correspondence/landclim-metadata-challenge/verify.py
```
