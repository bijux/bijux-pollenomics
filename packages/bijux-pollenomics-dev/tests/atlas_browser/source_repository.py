"""Exercise synthetic replay records with imported-source custody tested separately."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch


def generate_fixture_candidate(
    repository: Path, destination: Path, module: str
) -> dict[str, Any]:
    """Call the real renderer over tiny data without copying maintained packages."""
    assert module in {"source_detail_candidate", "nordic_source_candidate"}
    generator = importlib.import_module(
        "bijux_pollenomics_dev.ci.atlas_browser." + module
    )
    function = getattr(generator, "generate_" + module)
    with patch.object(generator, "observed_source_inputs", return_value={}) as observed:
        receipt = cast(dict[str, Any], function(repository, destination))
    observed.assert_called_once_with(repository.resolve())
    inputs = cast(dict[str, str], receipt["inputs_sha256"])
    assert inputs
    for relative, expected in inputs.items():
        assert (
            hashlib.sha256((repository / relative).read_bytes()).hexdigest() == expected
        )
    return receipt
