"""Compatibility alias for domain-owned atlas candidate construction."""

import sys

from ....adna.governance.atlas_candidates import service as _implementation
from ....adna.governance.atlas_candidates.service import (
    build_tracked_animal_atlas_evidence_rows as build_tracked_animal_atlas_evidence_rows,
)

sys.modules[__name__] = _implementation
