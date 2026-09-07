"""Tests for canonical direct SEAD UUID identities."""

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.source_keys.identities import (
    canonical_site_uuid,
)


def test_canonical_site_uuid_preserves_direct_source_value() -> None:
    value = "3d50fd2b-c1b1-4a45-b8ad-70ed033919a0"
    assert canonical_site_uuid(value) == value


@pytest.mark.parametrize(
    "value",
    (
        "not-a-uuid",
        "3D50FD2B-C1B1-4A45-B8AD-70ED033919A0",
        "{3d50fd2b-c1b1-4a45-b8ad-70ed033919a0}",
        "3d50fd2bc1b14a45b8ad70ed033919a0",
        " 3d50fd2b-c1b1-4a45-b8ad-70ed033919a0",
        None,
    ),
)
def test_canonical_site_uuid_rejects_malformed_or_noncanonical_values(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="canonical"):
        canonical_site_uuid(value)
