from __future__ import annotations

AADR_DATAVERSE_PERSISTENT_ID = "doi:10.7910/DVN/FFIDCW"
AADR_DATAVERSE_API_URL = (
    "https://dataverse.harvard.edu/api/datasets/:persistentId/"
    "?persistentId=doi:10.7910/DVN/FFIDCW"
)
AADR_DATAVERSE_VERSIONS_URL = (
    "https://dataverse.harvard.edu/api/datasets/:persistentId/versions"
    "?persistentId=doi:10.7910/DVN/FFIDCW"
)
AADR_DOWNLOAD_URL_TEMPLATE = (
    "https://dataverse.harvard.edu/api/access/datafile/{file_id}"
)
REQUEST_HEADERS = {"User-Agent": "bijux-pollenomics/1.0"}

__all__ = [
    "AADR_DATAVERSE_API_URL",
    "AADR_DATAVERSE_PERSISTENT_ID",
    "AADR_DATAVERSE_VERSIONS_URL",
    "AADR_DOWNLOAD_URL_TEMPLATE",
    "REQUEST_HEADERS",
]
