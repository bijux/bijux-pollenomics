"""Optional metadata dependencies require independently declared source identities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_document import source_resources as owner


@pytest.mark.parametrize(
    "field", ["expected_manifest_sha256", "expected_context_sha256"]
)
@pytest.mark.parametrize("invalid", [None, True, "A" * 64, "0" * 63, " " + "0" * 64])
def test_federation_input_refuses_nonliteral_independent_digest(
    tmp_path: Path, field: str, invalid: Any
) -> None:
    constructor = owner.AtlasAncillaryFederationInput
    values: dict[str, Any] = {
        "directory": tmp_path,
        "expected_manifest_sha256": "1" * 64,
        "context_directory": tmp_path,
        "expected_context_sha256": "2" * 64,
        "capsule_sources": {},
    }
    values[field] = invalid
    with pytest.raises(ValueError):
        constructor(**values)


def test_federation_requires_native_archive_and_owned_input_type(
    tmp_path: Path,
) -> None:
    constructor = owner.AtlasAncillaryFederationInput
    source = constructor(tmp_path, "1" * 64, tmp_path, "2" * 64, {})
    with pytest.raises(ValueError, match="archive"):
        owner.AtlasResourceCatalogueInput(tmp_path, "3" * 64, ancillary=source)
    invalid_owner: Any = {}
    with pytest.raises(ValueError, match="owner|input"):
        owner.AtlasResourceCatalogueInput(
            tmp_path,
            "3" * 64,
            archive=owner.AtlasResourceArchiveInput(
                tmp_path, "4" * 64, "/data/source/"
            ),
            ancillary=invalid_owner,
        )


@pytest.mark.parametrize(
    "resolvers", [[], {"not-a-digest": Path(".")}, {"1" * 64: "/source"}]
)
def test_capsule_resolver_is_explicit_and_not_coerced(
    tmp_path: Path, resolvers: Any
) -> None:
    constructor = owner.AtlasAncillaryFederationInput
    with pytest.raises(ValueError):
        constructor(tmp_path, "1" * 64, tmp_path, "2" * 64, resolvers)
