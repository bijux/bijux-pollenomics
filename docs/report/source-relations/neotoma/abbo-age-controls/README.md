# Abborrtjärnen ABBO age-control correspondence

The author-published [ABBO age-determination table](https://doi.pangaea.de/10.1594/PANGAEA.740080)
contains six accelerator-mass-spectrometry radiocarbon dates for core `ABBO`.
Its source bytes have SHA-256
`9717f1600c62659a33a4901da16c6b5fc3dac7cc47f8c005e54909568929704d`.
The raw tabular file remains in the external `epd/pangaea` source store under
the table's **CC-BY-NC-3.0** terms. The governed [comparison receipt](report.json)
retains Neotoma-derived control values and exact-match outcomes, not a copy of
the published source table.

All **six** PANGAEA lab numbers match the Neotoma/EPD ABBO chronology `11516`
one to one. Depths match after multiplying the published meter values by 100
to compare with Neotoma's **unlabeled** native depth numbers; the profile
comparison supports a centimeter interpretation for ABBO. Dated thicknesses
match after millimeters-to-centimeters conversion. Radiocarbon ages and
older/younger errors match exactly after
converting published `ka BP` to Neotoma's `radiocarbon years BP`.
Neotoma separately supplies calibrated-BP control ages and older/younger
limits. Its seventh control is a core-top age of -52 cal BP at 648 cm, with
no matching published radiocarbon date. The Neotoma chronology labels its
age model **linear interpolation**. Radiocarbon and calibrated ages are never
substituted for one another.

The existing [pollen-profile correspondence](../abbo-profile/README.md)
already matches all 107 sample depths and 535 selected count cells to a
separate PANGAEA ABBO profile. Together these source checks strongly bind
the dated controls and pollen samples to the same named core. They do not
resolve the PANGAEA/Neotoma collection-date difference, furnish uncertainty
bounds for the interpolated ages of the 107 pollen samples, identify Rootsi
workbook rights, or establish age-specific lake geometry. **Zero ABBO LRA
samples are admitted.**

Reproduce from the repository root with the source file retained externally:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.abbo_age_controls \
  --repository . \
  --source ../bijux-pollenomics-data/epd/pangaea/abbo-age-determination-pangaea-740080.tsv \
  --output artifacts/jobs/abbo-age-controls-replay
```

The producer checks the external file's exact hash, citation, license, table
schema and every date field before writing its receipt. Source differences
require a new comparison rather than silent fallback.

## Current official-provider observation

On 16 October 2026, one HTTPS request to the official PANGAEA download URL
returned HTTP 200 and the complete 2,977-byte table with the SHA-256 above.
The [current-provider custody receipt](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/abbo-current-provider-custody.json)
binds the saved response, native execution and unchanged comparison. All six
lab/depth/radiocarbon-age/older-error/younger-error records match that comparison
using decimal unit conversion. The source records thickness in millimeters,
ages in ka BP relative to 1950 using the Libby convention, and six dated
materials; neither error confidence levels nor thickness-interval semantics
are inferred. Calibrated control ages remain separate.

An earlier request returned HTTP 400 because an explicit Accept header
conflicted with the URL's format query. Its response and failed execution
remain retained; removing that header enabled the successful observation.
This establishes current provider-byte custody, not the original acquisition
epoch or permission for analytical use under CC-BY-NC-3.0. The original
unresolved owner criterion, the 107 missing sample-age uncertainty bounds,
collection-date and historical-geometry questions, and zero admitted ABBO
LRA samples remain unchanged. No calibration or scientific model was run.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** Six published ABBO AMS dates match their Neotoma control lab/depth/age/error fields under explicit unit comparisons.

**Unsupported claim.** Calibrated control bounds do not supply sample-age uncertainty or historical lake geometry, and the core top is not a seventh published 14C date.

**Actual verification performed.** On 2026-10-16, a fresh official-provider GET returned HTTP 200, one complete 2,977-byte body matching the retained table SHA-256, and native/stage zero. Independently compared all six lab/depth/radiocarbon-age/older-error/younger-error records to the retained comparison using decimal unit conversion; no calibration, private-source replay or model. Preserved the earlier HTTP 400 response and failed native execution. Current byte custody does not reconstruct historical acquisition or establish analytical use authority; the original unresolved owner criterion, numerical results, permissions, human decisions and zero LRA admission remain unchanged.

**Remaining input or review.** Collection-date roles, 107 interpolated sample uncertainties, historical basin geometry and source analytical rights need resolution.

**Cause category.** Control correspondence does not define a sample-age posterior.

**Consequence.** Zero ABBO LRA samples are admitted despite strong control-source lineage.

**Precise next acceptance route.** Obtain the selected age model and sample-level uncertainty/support with qualified basin/count/taxon/use decisions.

**Negative or refused result.** The −52 cal BP core top lacks a matching published radiocarbon date; sample ages lack uncertainty bounds.

**Matched denominator.** 6 published dates/6 exact control matches versus 7 Neotoma controls and 107 pollen samples; ka 14C BP and cal BP remain distinct.

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-age-controls/report.json](report.json) (SHA-256 `629efd8c18ce6b3ab570d36cf4c3ebbb99a180d1018cdb8eec2ecfa268039445`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/abbo-profile/report.json](../abbo-profile/report.json) (SHA-256 `c29738753e25a99767776cfecfbdaebe0c3a4394c38df91b72bb2c4c944c6263`).

- [Retained qualification evidence: reports/science/source-cohorts/abbo-age-original-acceptance.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/abbo-age-original-acceptance.json) (SHA-256 `38b8edf5632f9104146dd3c2a0f505313ef836fbe1ee6d8c335040c14f6490e7`).

- [Retained qualification evidence: reports/science/source-cohorts/abbo-current-provider-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/abbo-current-provider-custody.json) (SHA-256 `a30ac256f25d088b2a1ba4a03d859605dc5fe846d02e185d4eb37e37aa589b8c`).

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
