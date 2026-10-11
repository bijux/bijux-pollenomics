# Neotoma lake-parameter evidence for Nordic pollen candidates

The exact site-evidence source projection retains 54 site identities and
their collection-unit context in the external source-data store. The
[lake-parameter review](report.json) joins those identities to an exact public
[Neotoma lakeparameters API](https://api.neotomadb.org/v2.0/data/dbtables/lakeparameters?limit=1000&offset=0)
capture: 24,554 lake-parameter rows and 21 parameter types. Five parameter
rows match five candidate sites. The source-site and capture SHA-256 digests in
`report.json` bind the review to its inputs; site evidence, capture and page
receipts are retained under `neotoma/lakeparameters/` in that store.
This removes the source dependency on the disposable `artifacts/v3` run.

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

The [replay reader](verify.py) verifies the capture manifest and every page,
rebuilds all source joins through the production consumer, and compares the
exact retained review bytes:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/neotoma/lakeparameters/verify.py \
  --capture-root /path/to/private/source/store/neotoma/lakeparameters
```
