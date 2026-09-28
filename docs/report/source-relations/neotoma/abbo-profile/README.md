# Abborrtjärnen ABBO cross-source lineage

The [source-bound comparison](report.json) reads the governed Neotoma/EPD
native sequence and the separate [PANGAEA EPD pollen profile](https://doi.pangaea.de/10.1594/PANGAEA.738429).
It authenticates the downloaded PANGAEA text by SHA-256
`ee4671277fc4120c65f6fe4fa19fb1d302167e419d5419a55287d09c226ab154`
and the governed sequence tables through their manifest. The downloaded
PANGAEA text remains in the external source store under its stated
CC-BY-NC-3.0 terms; this report retains derived comparisons only.

Both sources identify core `ABBO`, investigator Thomas Giesecke and the same
rounded site coordinates. All **107** source depths match exactly when the
unlabeled Neotoma depth number is divided by 100 and compared with PANGAEA's
meter depth. Five named taxon columns (Alnus, Betula, Cyperaceae, Picea abies
and Poaceae) match the Neotoma reported count trajectory at every depth:
**535/535** compared cells, including PANGAEA zeros where Neotoma has no
reported row. This is strong evidence that the two records describe the same
sample series. It supports a centimeter interpretation of the native depth
numbers for ABBO only; the Neotoma source field remains labeled with an
unknown unit because that source does not state one.

The PANGAEA event reports a 3 ha lake and a **2002-06-15** core date. The
Neotoma collection-unit record gives **2002-01-01**. The records' date roles
or precision have not been reconciled. The reported area belongs to the
PANGAEA event metadata; it does not establish a historical lake outline or
time-specific basin geometry for the 107 pollen samples. This comparison
does not admit LRA inputs or independent vegetation truth.

The separate [ABBO age-control comparison](../abbo-age-controls/README.md)
matches all six published radiocarbon dates to the Neotoma chronology's dated
controls. Its calibrated control limits do not supply uncertainty bounds for
the interpolated ages of individual pollen samples.

## Reproduce

Download the profile from the DOI above into the external source store,
verify its SHA-256, then run from the product repository root into an absent
directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.source_completion.abbo_profile_lineage \
  --repository . \
  --profile /path/to/external/abbo-pollen-profile-pangaea-738429.tsv \
  --output artifacts/neotoma-abbo-lineage-replay
```

The output must match the retained report byte for byte. The producer refuses
changed source or sequence hashes, ambiguous depths and any mismatch in the
five compared count trajectories.
