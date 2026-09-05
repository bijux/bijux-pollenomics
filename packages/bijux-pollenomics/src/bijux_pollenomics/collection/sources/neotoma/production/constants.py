from __future__ import annotations

import re

EXPECTED_RAW_PART_COUNT = 9
RAW_SOURCE = "Neotoma"
RAW_DATASET_TYPE = "pollen"
RAW_ENDPOINT = "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
RAW_ARCHIVE_LABEL = "raw/neotoma_pollen_dataset_downloads"
PRODUCTION_DRIVER_ID = "bijux-pollenomics.neotoma-relational-production"
PRODUCTION_DRIVER_VERSION = "1"
PRODUCTION_CONFIG_SCHEMA = "neotoma-relational-production-config.v1"
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
