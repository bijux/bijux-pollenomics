# Neotoma lake-parameter evidence for Nordic pollen candidates

The exact site-evidence source projection retains 54 site identities and
their collection-unit context in the external source-data store. The
[lake-parameter review](report.json) joins those identities to an exact public
[Neotoma lakeparameters API](https://api.neotomadb.org/v2.0/data/dbtables/lakeparameters?limit=1000&offset=0)
capture: 24,554 lake-parameter rows and 21 parameter types. Five parameter
rows match five candidate sites. The source-site and capture SHA-256 digests in
`report.json` bind the review to its inputs; site evidence, capture and page
receipts are retained under `neotoma/lakeparameters/` in that store.

| Country | Site | Native parameter | Value | Candidate pollen samples |
| --- | --- | --- | ---: | ---: |
| Sweden | Klotjärnen | maximum depth (m) | 6 | 110 |
| Sweden | Lillsjön | maximum depth (m) | 2.2 | 81 |
| Norway | Liten Cap’pesjav’ri | surface area (ha) | 2.5 | 72 |
| Norway | Over Gunnarsfjorden | surface area (ha) | 5 | 116 |
| Norway | Over Kobbkrokvatnet | surface area (ha) | 1.7 | 69 |

The three Norwegian site-level `area` fields are numerically different from
their lake-parameter `Area` fields and have no qualified unit or basin meaning
in this review. The three reported surface areas are not sample-age-specific
basin dimensions. The capture used serial live offset pages rather than a
transactional snapshot, so absence among the other 49 candidate sites is not
certified. No candidate is admitted to LRA from these values; historical basin
geometry, taxon/PPE/count support and target-independent modeling inputs still
need source-specific qualification. The data are from Neotoma and its original
contributors; the [source policy review](../../../../public/pollenomics-data/sources/neotoma.md)
records attribution and use terms.

The [replay reader](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/source-relations/neotoma/lakeparameters/verify.py) verifies the capture manifest and every page,
rebuilds all source joins through the production consumer, and compares the
exact retained review bytes:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/lakeparameters/verify.py \
  --capture-root /path/to/private/source/store/neotoma/lakeparameters
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** Five lake-parameter rows join five of 54 retained Nordic candidate sites in the captured API pages.

**Unsupported claim.** Maximum water depth is not lake radius; live offset pagination cannot certify absence for 49 unmatched sites.

**Actual verification performed.** Earlier verification: Read the five exact source rows, parameter labels, country counts and retained-page consistency posture; no API recapture or basin fit. Separately, the unchanged maintained reader returned native zero as a checker, and an independent complete source-page reader reconstructed every report byte and typed value on source commit `82c8fc4ed3d847909d14162f51b77dc59ccc0a70`. The 24,554 rows, 21 parameter types, 54 original sites and five exact parameter/locator joins remain distinct from the current prerequisite cohort. The checker is not a report producer. No new HTTP capture, basin fit, LRA or human decision is claimed.

**Remaining input or review.** Historical/time-specific basin meaning, unqualified native area fields, count/taxon/PPE support and use review remain.

**Cause category.** Live pagination and site-level geometry are not complete historical basin evidence.

**Consequence.** Three source area leads do not admit any pollen sample to LRA.

**Precise next acceptance route.** Bind each site’s physical core and dated basin or justified static scenario, then review the remaining scientific inputs and source terms.

**Negative or refused result.** 49 sites lack an observed parameter row in this capture; absence is uncertified; 0 LRA samples admitted.

**Matched denominator.** 54 candidate sites; 24,554 captured parameter rows/21 types; 5 matched rows/sites: 2 Swedish depth and 3 Norwegian area values.

- [Retained qualification evidence: docs/report/source-relations/neotoma/lakeparameters/report.json](report.json) (SHA-256 `9c5c48936b10f62b2501a9d26ddad102d606929ee55fbe76614431e731a21fa7`).

- [Retained qualification evidence: reports/science/source-cohorts/neotoma-lake-source-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/neotoma-lake-source-custody.json) (SHA-256 `df23f600e89cfd4e285442b5f82480b95521216cad2363f25a91640623953024`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
