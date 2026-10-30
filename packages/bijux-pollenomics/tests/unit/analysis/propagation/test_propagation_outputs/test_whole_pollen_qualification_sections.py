"""Whole-pollen normative sections must be mappings before claim validation."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.propagation.outputs.contracts import (
    _validate_propagation_contract_identity,
)
from bijux_pollenomics.analysis.propagation.outputs.models import (
    PropagationOutputRefusalError,
)

from .support.model import MODEL, PROPAGATION_CONTRACT_VERSION


def _qualified_model() -> dict[str, Any]:
    """Reuse the existing owned normative fixture with explicit qualification flags."""
    model = deepcopy(MODEL)
    model["pair_compatibility"] = {
        "whole_pollen_resolution": {
            "heterogeneous_taxa_warning_required": True,
            "interpretive_strength_cap": "exploratory_aggregate",
        }
    }
    return model


def _validate(root: Path, model: dict[str, Any]) -> None:
    """Call the real validator with rehashed owned JSON accepted by its YAML parser."""
    root.mkdir(exist_ok=True)
    body = json.dumps(model, sort_keys=True, allow_nan=False).encode()
    path = root / "propagation-model.v1.yaml"
    path.write_bytes(body)
    _validate_propagation_contract_identity(
        path,
        schema_root=root,
        propagation_contract_version=PROPAGATION_CONTRACT_VERSION,
        propagation_contract_digest=hashlib.sha256(body).hexdigest(),
    )


def test_qualified_owned_normative_mapping_is_accepted(tmp_path: Path) -> None:
    """The declared qualified fixture remains a real current accepted baseline."""
    _validate(tmp_path / "schema", _qualified_model())


@pytest.mark.parametrize(
    "defect", ("missing_pair", "pair_list", "missing_whole", "whole_list")
)
def test_missing_or_nonmapping_qualifications_refuse_after_valid_baseline(
    tmp_path: Path, defect: str
) -> None:
    """Missing sections are actual stronger refusals, independent of input digests."""
    model = _qualified_model()
    root = tmp_path / "schema"
    _validate(root, model)
    if defect == "missing_pair":
        model.pop("pair_compatibility")
    elif defect == "pair_list":
        model["pair_compatibility"] = []
    elif defect == "missing_whole":
        model["pair_compatibility"] = {}
    else:
        model["pair_compatibility"] = {"whole_pollen_resolution": []}
    with pytest.raises(PropagationOutputRefusalError) as caught:
        _validate(root, model)
    assert caught.value.reason_code == "invalid_propagation_identity"
