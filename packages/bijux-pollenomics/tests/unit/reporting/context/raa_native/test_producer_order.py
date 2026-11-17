"""Use generated native POINTs through the maintained producer and aggregate reader."""

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from pyproj import Transformer
import pytest

from bijux_pollenomics.collection.sources.raa.point_grid import (
    NativePointGridLimits,
    materialize_raa_native_point_grid,
)
from bijux_pollenomics.reporting.context.raa_native import (
    NativeRegistrySource,
    capture_native_registry_context,
)
from tests.unit.collection.sources.raa.geometry.support import (
    A,
    database,
    gpkg,
    identity,
    point,
)


@pytest.mark.parametrize(
    "positions",
    [((13.5, 55.5), (12.5, 56.5)), ((12.5, 55.5), (13.5, 56.5))],
    ids=["west-resets-next-latitude", "both-axes-increase"],
)
def test_current_native_producer_csv_is_accepted(
    tmp_path: Path, positions: tuple[tuple[float, float], tuple[float, float]]
) -> None:
    source = database(tmp_path)
    second = "22222222-2222-2222-2222-222222222222"
    forward = Transformer.from_crs(4619, 3006, always_xy=True)
    with sqlite3.connect(source) as connection:
        connection.execute(
            "UPDATE lamning SET antikvariskbedomning=?", ("Fornlämning",)
        )
        connection.execute(
            "INSERT INTO lamning(fid,uuid,antikvariskbedomning) VALUES(2,?,?)",
            (second, "Fornlämning"),
        )
        for fid, (key, position) in enumerate(
            zip((A, second), positions, strict=True), 1
        ):
            e, n = forward.transform(*position, errcheck=True)
            connection.execute(
                "INSERT INTO point(fid,geometri,lamning_uuid) VALUES(?,?,?)",
                (fid, gpkg(point(e, n)), key),
            )
    digest, size = identity(source)
    output = tmp_path / "private-generated-product"
    product = materialize_raa_native_point_grid(
        source,
        expected_sha256=digest,
        expected_byte_count=size,
        destination=output,
        limits=NativePointGridLimits(2, 2, 61, 1024 * 1024),
    )
    raw = (output / "cell-counts.csv").read_bytes()
    expected = [(int(lon), int(lat), 1) for lon, lat in positions]
    assert (
        raw
        == (
            "west_longitude,south_latitude,uuid_count\n"
            + "".join(f"{w},{s},{n}\n" for w, s, n in expected)
        ).encode()
    )
    snapshot = capture_native_registry_context(
        output,
        expected_report_sha256=product.report_sha256,
        expected_counts_sha256=sha256(raw).hexdigest(),
        source=NativeRegistrySource(
            digest,
            size,
            "2026-09-13T00:00:00Z",
            "https://pub.raa.se/generated.gpkg",
            "Public Domain; media excluded",
        ),
    )
    assert snapshot.counts_bytes == raw
    assert json.loads(snapshot.context_bytes)["counts"]["included_uuids"] == 2
    assert len(json.loads(snapshot.cells_bytes)["features"]) == 2
