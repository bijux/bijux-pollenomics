"""Reproducible production driver for the Neotoma relational snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from ...boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_RELEASE_PAGE_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from ...boundaries.store import load_country_boundaries
from ..country import build_neotoma_site_country_decisions
from ..materialization import materialize_neotoma_relational_snapshot
from ..relational import CountryAttributionInput, build_neotoma_relational_snapshot
from .boundary_authority import load_boundary_authority
from .command_line import parse_alias, parser, run_cli
from .constants import (
    EXPECTED_RAW_PART_COUNT,
    PRODUCTION_CONFIG_SCHEMA,
    PRODUCTION_DRIVER_ID,
    PRODUCTION_DRIVER_VERSION,
    RAW_ARCHIVE_LABEL,
    RAW_DATASET_TYPE,
    RAW_ENDPOINT,
    RAW_SOURCE,
    SHA256_PATTERN,
)
from .execution_api import (
    _build_id as _build_id,
)
from .execution_api import (
    _load_validated_boundary_authority as _load_validated_boundary_authority,
)
from .execution_api import (
    _load_validated_raw_archive as _load_validated_raw_archive,
)
from .execution_api import (
    _parser as _parser,
)
from .execution_api import (
    load_validated_neotoma_raw_archive as load_validated_neotoma_raw_archive,
)
from .execution_api import (
    main as main,
)
from .execution_api import (
    run_neotoma_relational_production as run_neotoma_relational_production,
)
from .identity import build_id
from .models import (
    NeotomaProductionConfig as NeotomaProductionConfig,
)
from .models import (
    NeotomaProductionReport as NeotomaProductionReport,
)
from .models import (
    _BoundaryAuthority as _BoundaryAuthority,
)
from .models import (
    _RawArchive as _RawArchive,
)
from .raw_archive import load_raw_archive
from .validation import (
    canonical_digest,
    expect_equal,
    integer,
    integer_list,
    json_object,
    mapping,
    non_negative_integer,
    positive_integer,
    read_regular_file,
    validated_input_directory,
    validated_output_target,
)
from .validation_api import (
    _canonical_digest as _canonical_digest,
)
from .validation_api import (
    _download_dataset_id as _download_dataset_id,
)
from .validation_api import (
    _expect_equal as _expect_equal,
)
from .validation_api import (
    _integer as _integer,
)
from .validation_api import (
    _integer_list as _integer_list,
)
from .validation_api import (
    _json_object as _json_object,
)
from .validation_api import (
    _mapping as _mapping,
)
from .validation_api import (
    _non_negative_integer as _non_negative_integer,
)
from .validation_api import (
    _parse_alias as _parse_alias,
)
from .validation_api import (
    _positive_integer as _positive_integer,
)
from .validation_api import (
    _read_regular_file as _read_regular_file,
)
from .validation_api import (
    _validated_input_directory as _validated_input_directory,
)
from .validation_api import (
    _validated_output_target as _validated_output_target,
)
from .workflow import run_production

__all__ = [
    "NeotomaProductionConfig",
    "NeotomaProductionReport",
    "load_validated_neotoma_raw_archive",
    "main",
    "run_neotoma_relational_production",
]

_SHA256_PATTERN = SHA256_PATTERN
for _definition in (
    NeotomaProductionConfig,
    NeotomaProductionReport,
    _RawArchive,
    _BoundaryAuthority,
    run_neotoma_relational_production,
    load_validated_neotoma_raw_archive,
    _load_validated_raw_archive,
    _load_validated_boundary_authority,
    _build_id,
    _validated_output_target,
    _validated_input_directory,
    _read_regular_file,
    _json_object,
    _download_dataset_id,
    _mapping,
    _integer,
    _positive_integer,
    _non_negative_integer,
    _integer_list,
    _expect_equal,
    _canonical_digest,
    _parse_alias,
    _parser,
    main,
):
    _definition.__module__ = __name__
