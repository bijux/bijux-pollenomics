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

The separate [LandClim II site metadata](https://doi.pangaea.de/10.1594/PANGAEA.937075)
reports `ABB` at the same coordinates with 107 samples and `siteradius` **98 m**
in workbook row 968 (tracked workbook SHA-256
`2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb`).
The area-equivalent circular radius of the EPD event's 3 ha is
`sqrt(30000 m² / π) = 97.7205 m`; a 98 m circle has area 3.0172 ha. This
numeric agreement supports the modern site-area lineage, but LandClim may
derive the radius from that same EPD metadata. It is not independent lake
measurement or evidence that the radius applied throughout the Holocene.

The separate [ABBO age-control comparison](../abbo-age-controls/README.md)
matches all six published radiocarbon dates to the Neotoma chronology's dated
controls. Its calibrated control limits do not supply uncertainty bounds for
the interpolated ages of individual pollen samples.

## Reproduce

Use the locked repository environment described in
[Installation and Setup](../../../../public/pollenomics/operations/installation-and-setup.md#reproduce-the-repository-environment).
Configure the external source store containing
`epd/pangaea/abbo-pollen-profile-pangaea-738429.tsv`; the table remains outside
the product under its stated CC-BY-NC-3.0 terms. Run from the repository root
into an absent directory under `artifacts/`:

```sh
POLLENOMICS_PYTHON=artifacts/root/check-venv/bin/python
: "${POLLENOMICS_SOURCE_ROOT:?configure the retained external source store}"
POLLENOMICS_OUTPUT=artifacts/jobs/abbo-profile-replay
mkdir -p artifacts/jobs
test ! -e "$POLLENOMICS_OUTPUT" &&
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics-lra/src:packages/pollenomics/src \
  "$POLLENOMICS_PYTHON" -B -m \
    bijux_pollenomics_dev.source_completion.neotoma.abbo_profile \
    --repository . \
    --source-root "$POLLENOMICS_SOURCE_ROOT" \
    --output "$POLLENOMICS_OUTPUT" &&
  cmp "$POLLENOMICS_OUTPUT/report.json" \
    docs/report/source-relations/neotoma/abbo-profile/report.json
```

The qualified wrapper checks the exact descriptor, external table and
sequence inputs before publishing. The configured execution owner at source
`d9e6883db64be68d8d5b229d8390438f4ddf74c2` reproduced the complete retained
1,784-byte report in both reference and replay lanes. Current technical
ownership does not establish historical acquisition, broader source-use
authority or LRA admission.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The ABBO profile binds 107 depths and 535 selected taxon cells to a published PANGAEA profile under an explicit 100× depth relation.

**Unsupported claim.** A likely shared source trajectory is not independent vegetation truth, source-wide depth-unit authority or historical basin geometry.

**Actual verification performed.** The profile receipt and five named-taxonomical comparison summaries retain their original scope, including conflicting collection dates. At d9e6883db64be68d8d5b229d8390438f4ddf74c2, the configured qualified wrapper reproduced the complete retained 1,784-byte report in reference and replay lanes using the same clean-source plan, exact external descriptor and retained table; no new download or scientific admission.

**Remaining input or review.** Collection-date semantics, sample-age uncertainty and historical basin/count/PPE/use qualifications remain open.

**Cause category.** Cross-source profile lineage has narrower scope than source admission.

**Consequence.** The 3 ha event area/97.7205 m equivalent radius cannot be applied to all Holocene ages.

**Precise next acceptance route.** Resolve core/date and time-specific or explicitly justified basin assumptions with qualified age/count/taxon inputs.

**Negative or refused result.** 2002-06-15 versus 2002-01-01 collection dates remain unreconciled; no LRA input or historical geometry admitted.

**Matched denominator.** 107 sample depths×5 selected taxa=535 compared positions; source missing-row zeros remain a different evidence state from explicit rows.

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-profile/report.json](report.json) (SHA-256 `c29738753e25a99767776cfecfbdaebe0c3a4394c38df91b72bb2c4c944c6263`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-age-controls/report.json](../abbo-age-controls/report.json) (SHA-256 `629efd8c18ce6b3ab570d36cf4c3ebbb99a180d1018cdb8eec2ecfa268039445`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
