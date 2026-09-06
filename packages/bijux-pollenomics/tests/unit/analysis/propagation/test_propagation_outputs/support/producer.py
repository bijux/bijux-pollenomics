"""Producer identity helpers for propagation output tests."""

from __future__ import annotations

import hashlib
import json

from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID as PRODUCT_PROPAGATION_PRODUCER_ID,
)
from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_SOURCE_PATHS,
)
from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_VERSION as PRODUCT_PROPAGATION_PRODUCER_VERSION,
)

from tests.support.repository import REPOSITORY_ROOT as TEST_REPOSITORY_ROOT

REPOSITORY_ROOT = TEST_REPOSITORY_ROOT
PROPAGATION_PRODUCER_ID = PRODUCT_PROPAGATION_PRODUCER_ID
PROPAGATION_PRODUCER_VERSION = PRODUCT_PROPAGATION_PRODUCER_VERSION


def producer_digest() -> str:
    """Hash the ordered product source closure declared by the producer."""
    records = [
        {
            "path": relative_name,
            "sha256": hashlib.sha256(
                (REPOSITORY_ROOT / relative_name).read_bytes()
            ).hexdigest(),
        }
        for relative_name in PROPAGATION_PRODUCER_SOURCE_PATHS
    ]
    return hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


PROPAGATION_PRODUCER_DIGEST = producer_digest()
