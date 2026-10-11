"""Fully rehashed retained changes cannot replace raw payload/CRS validation."""

from hashlib import sha256
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.raa.geometry import (
    audit_raa_geometry,
    inspect_raa_geometry_audit,
)
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
)

from .support import add_geometry, database, gpkg, identity, point


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "geometry",
        "owner",
        "crs",
        "summary",
        "boundary",
        "extra_file",
        "duplicate_key",
    ],
)
def test_raw_replay_owns_retained_admission(tmp_path: Path, mutation: str) -> None:
    source = database(tmp_path)
    add_geometry(source, "point", gpkg(point()))
    pin, size = identity(source)
    audit = audit_raa_geometry(
        source,
        expected_sha256=pin,
        expected_byte_count=size,
        destination=tmp_path / "audit",
    )
    manifest = audit.manifest()
    manifest_path = audit.directory / "manifest.json"
    rows_path = audit.directory / "geometry.ndjson"
    rows = [json.loads(line) for line in rows_path.read_bytes().splitlines()]
    if mutation == "geometry":
        rows[1]["geometry"]["coordinate_extrema_xy"] = [10, 10, 20, 20]
    elif mutation == "owner":
        rows[1]["source_fields"]["lamning_uuid"] = "other"
    elif mutation == "crs":
        rows[0]["crs"]["transport_axis_order"] = "northing_first"
    elif mutation == "summary":
        rows[-1]["geometry_occurrences"] = 999
        manifest["summary"] = rows[-1]
    elif mutation == "boundary":
        cast(dict[str, object], manifest["boundary"])["scientific_admission"] = True
    elif mutation == "extra_file":
        (audit.directory / "extra").write_text("foreign")
    encoded = b"".join(canonical_bytes(row) for row in rows)
    rows_path.write_bytes(encoded)
    manifest["files"] = {
        "geometry.ndjson": {
            "sha256": sha256(encoded).hexdigest(),
            "byte_count": len(encoded),
            "record_count": len(rows),
        }
    }
    content = canonical_bytes(manifest)
    if mutation == "duplicate_key":
        content = content.replace(b"{", b'{"schema_version":"wrong",', 1)
    manifest_path.write_bytes(content)
    if mutation == "none":
        verified = inspect_raa_geometry_audit(
            audit.directory,
            expected_manifest_sha256=sha256(content).hexdigest(),
            source_path=source,
            expected_source_sha256=pin,
            expected_source_byte_count=size,
        )
        assert verified.manifest_sha256 == audit.manifest_sha256
    else:
        with pytest.raises(ValueError):
            inspect_raa_geometry_audit(
                audit.directory,
                expected_manifest_sha256=sha256(content).hexdigest(),
                source_path=source,
                expected_source_sha256=pin,
                expected_source_byte_count=size,
            )
    assert identity(source) == (pin, size)
