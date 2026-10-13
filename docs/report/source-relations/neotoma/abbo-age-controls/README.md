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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/abborrtjarnen-source-method.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/abborrtjarnen-source-method.md) (source SHA-256 `264420c81e18a6ee56b0b612e657f881fa26829a9cc060114d69b15d2491120f`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
