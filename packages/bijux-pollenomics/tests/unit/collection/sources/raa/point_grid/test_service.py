"""Generated native UUID populations never borrow historical WFS semantics."""

from __future__ import annotations

import csv
from hashlib import sha256
import importlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
from types import ModuleType
from typing import Any

from pyproj import Transformer
import pytest

from ..geometry.support import A, add_geometry, database, gpkg, identity, point


def producer() -> tuple[ModuleType, Any]:
    name = "bijux_pollenomics.collection.sources.raa.point_grid"
    assert importlib.util.find_spec(name) is not None, (
        "Native UUID POINT consumer is missing"
    )
    module = importlib.import_module(name)
    return module, module.materialize_raa_native_point_grid


def run(path: Path, destination: Path, **limits: object) -> Any:
    module, produce = producer()
    budget = {
        "max_uuid_records": 100,
        "max_geometry_rows": 100,
        "max_point_bytes": 1024,
        "max_output_bytes": 1024 * 1024,
        **limits,
    }
    digest, size = identity(path)
    return produce(
        path,
        expected_sha256=digest,
        expected_byte_count=size,
        destination=destination,
        limits=module.NativePointGridLimits(**budget),
    )


def selected(path: Path) -> None:
    with sqlite3.connect(path) as con:
        con.execute("UPDATE lamning SET antikvariskbedomning=?", ("Fornlämning",))


def native_point(longitude: float = 15.5, latitude: float = 60.5) -> bytes:
    east, north = Transformer.from_crs(4619, 3006, always_xy=True).transform(
        longitude, latitude
    )
    return gpkg(point(east, north))


def rows(output: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in (output / "uuid-dispositions.ndjson").read_text().splitlines()
    ]


def test_exact_native_point_is_one_uuid_in_declared_sweref_cell(tmp_path: Path) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    output = tmp_path / "grid"
    result = run(source, output)
    report = result.report()
    assert {p.name for p in output.iterdir()} == {
        "uuid-dispositions.ndjson",
        "cell-counts.csv",
        "report.json",
    }
    assert (
        result.directory == output
        and result.report_sha256
        == sha256((output / "report.json").read_bytes()).hexdigest()
    )
    (row,) = rows(output)
    assert row["native_lamning_uuid"] == A and row["native_class"] == "Fornlämning"
    assert row["raw_point_occurrences"] == row["valid_point_occurrences"] == 1
    assert row["disposition"] == "included" and row["grid_cell"] == [15, 60]
    assert row["source_xy_metres"][0] > 100000 and row["source_xy_metres"][1] > 6000000
    assert list(
        csv.DictReader(io.StringIO((output / "cell-counts.csv").read_text()))
    ) == [{"west_longitude": "15", "south_latitude": "60", "uuid_count": "1"}]
    assert (
        report["counts"]["source_uuids"]
        == report["counts"]["selected_class_uuids"]
        == report["counts"]["included_uuids"]
        == 1
    )
    assert sum(report["dispositions"].values()) == 1 and report["cell_count_total"] == 1
    assert (
        report["grid"]["crs"] == "EPSG:4619"
        and report["projection"]["always_xy"] is True
    )
    assert (
        report["boundary"]["country_assignment"] == "not_performed"
        and report["boundary"]["chronology_admission"] is False
    )
    assert report["boundary"]["historical_WFS_density_equivalence"] is False
    assert (
        A not in (output / "report.json").read_text()
        and A not in (output / "cell-counts.csv").read_text()
    )
    report["counts"]["included_uuids"] = 999
    assert result.report()["counts"]["included_uuids"] == 1


@pytest.mark.parametrize("second", [None, native_point()])
def test_two_raw_occurrences_never_collapse_to_one_valid_uuid(
    tmp_path: Path, second: object
) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    add_geometry(source, "point", second, fid=2)
    result = run(source, tmp_path / "grid")
    (row,) = rows(result.directory)
    assert row["raw_point_occurrences"] == 2 and row["valid_point_occurrences"] == (
        1 if second is None else 2
    )
    assert (
        row["disposition"] == "multiple_primary_point_occurrences"
        and row["grid_cell"] is None
    )
    assert (
        result.report()["counts"]["included_uuids"] == 0
        and result.report()["cell_count_total"] == 0
    )
    assert (
        result.directory / "cell-counts.csv"
    ).read_text() == "west_longitude,south_latitude,uuid_count\n"


@pytest.mark.parametrize("value", [None, b"bad", gpkg(point(float("inf"), 6500000))])
def test_single_unusable_source_point_is_accounted_without_zero_fill(
    tmp_path: Path, value: object
) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", value)
    result = run(source, tmp_path / "grid")
    (row,) = rows(result.directory)
    assert row["raw_point_occurrences"] == 1 and row["valid_point_occurrences"] == 0
    assert row["disposition"] == "unsupported_sole_point" and row["grid_cell"] is None


def test_uncertainty_and_other_primary_roles_cannot_supply_point(
    tmp_path: Path,
) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "lämningar_sverige_lägesosäkerhet", native_point())
    add_geometry(source, "linestring", native_point())
    result = run(source, tmp_path / "grid")
    (row,) = rows(result.directory)
    assert row["raw_point_occurrences"] == 0 and row["valid_point_occurrences"] == 0
    assert (
        row["uncertainty_occurrences"] == 1
        and row["disposition"] == "no_primary_point_occurrence"
    )
    assert result.report()["geometry_role_rows"]["linestring"] == 1


def test_class_filter_is_exact_and_precedes_point_location(tmp_path: Path) -> None:
    source = database(tmp_path)
    with sqlite3.connect(source) as con:
        con.execute("UPDATE lamning SET antikvariskbedomning=?", (" Fornlämning ",))
    add_geometry(source, "point", native_point())
    result = run(source, tmp_path / "grid")
    (row,) = rows(result.directory)
    assert (
        row["native_class"] == " Fornlämning "
        and row["disposition"] == "unselected_native_class"
    )
    assert result.report()["counts"]["selected_class_uuids"] == 0


@pytest.mark.parametrize(
    "table", ["point", "polygon", "lämningar_sverige_lägesosäkerhet"]
)
def test_orphan_geometry_owner_refuses_whole_input(tmp_path: Path, table: str) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, table, None)
    with sqlite3.connect(source) as con:
        con.execute(
            f'UPDATE "{table}" SET lamning_uuid=?',
            ("00000000-0000-0000-0000-000000000002",),
        )
    with pytest.raises(ValueError, match="owner"):
        run(source, tmp_path / "grid")
    assert not (tmp_path / "grid").exists()


def test_duplicate_native_uuid_refuses_before_publication(tmp_path: Path) -> None:
    source = database(tmp_path)
    with sqlite3.connect(source) as con:
        con.execute("INSERT INTO lamning(fid,uuid) VALUES(2,?)", (A,))
    with pytest.raises(ValueError, match="duplicate"):
        run(source, tmp_path / "grid")
    assert not (tmp_path / "grid").exists()


@pytest.mark.parametrize("kind", ["metadata", "point_header"])
def test_conflicting_crs_is_input_refusal(tmp_path: Path, kind: str) -> None:
    source = database(tmp_path)
    selected(source)
    if kind == "metadata":
        with sqlite3.connect(source) as con:
            con.execute("UPDATE gpkg_spatial_ref_sys SET definition='unsupported'")
    else:
        add_geometry(source, "point", gpkg(point(1, 2), srs=4326))
    with pytest.raises(ValueError, match="CRS"):
        run(source, tmp_path / "grid")
    assert not (tmp_path / "grid").exists()


@pytest.mark.parametrize(
    "limit,value",
    [
        ("max_uuid_records", True),
        ("max_geometry_rows", 0),
        ("max_point_bytes", -1),
        ("max_output_bytes", 1.5),
    ],
)
def test_limits_are_native_positive_integers(
    tmp_path: Path, limit: str, value: object
) -> None:
    source = database(tmp_path)
    with pytest.raises(ValueError, match="positive"):
        run(source, tmp_path / "grid", **{limit: value})


def test_oversized_point_blob_refuses_instead_of_discarding_occurrence(
    tmp_path: Path,
) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", b"x" * 128)
    with pytest.raises(ValueError, match="point.*byte"):
        run(source, tmp_path / "grid", max_point_bytes=64)
    assert not (tmp_path / "grid").exists()


def test_existing_output_is_never_replaced(tmp_path: Path) -> None:
    source = database(tmp_path)
    destination = tmp_path / "grid"
    destination.mkdir()
    (destination / "foreign").write_text("retained")
    with pytest.raises(FileExistsError):
        run(source, destination)
    assert (destination / "foreign").read_text() == "retained"


def test_non_blob_point_text_is_never_decoded_into_python(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import contextmanager

    module, _ = producer()
    service = importlib.import_module(module.__name__ + ".service")
    source = database(tmp_path)
    selected(source)
    marker = "unbounded-point-text-" * 4096
    add_geometry(source, "point", marker)
    actual = service.read_only_database
    decoded = []

    @contextmanager
    def observe(*args: Any, **kwargs: Any) -> Any:
        with actual(*args, **kwargs) as connection:

            def text_factory(raw: bytes) -> str:
                if raw.startswith(b"unbounded-point-text-"):
                    decoded.append(len(raw))
                return raw.decode("utf-8")

            connection.text_factory = text_factory
            yield connection

    monkeypatch.setattr(service, "read_only_database", observe)
    result = run(source, tmp_path / "grid")
    (row,) = rows(result.directory)
    assert (
        row["disposition"] == "unsupported_sole_point"
        and row["raw_point_occurrences"] == 1
    )
    assert decoded == [], (
        "Malformed TEXT geometry crossed the bounded native payload boundary"
    )


def test_source_mutation_before_publication_refuses_before_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, _ = producer()
    service = importlib.import_module(module.__name__ + ".service")
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    actual = service._write_product
    fired = []

    def changed(*args: Any, **kwargs: Any) -> Any:
        with sqlite3.connect(source) as con:
            con.execute("UPDATE lamning SET antikvariskbedomning=?", ("changed",))
        fired.append(True)
        return actual(*args, **kwargs)

    monkeypatch.setattr(service, "_write_product", changed)
    with pytest.raises(ValueError, match="source|Source|Input|input"):
        run(source, tmp_path / "grid")
    assert fired and not (tmp_path / "grid").exists()


def test_original_parent_substitution_is_refused_inside_attachment_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, _ = producer()
    service = importlib.import_module(module.__name__ + ".service")
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    parent = tmp_path / "destination"
    parent.mkdir()
    retained = tmp_path / "original-destination"
    actual = service.publish_owned_replacement
    fired = []

    def changed(*args: Any, **kwargs: Any) -> Any:
        parent.rename(retained)
        parent.mkdir()
        (parent / "foreign").write_text("foreign")
        fired.append(True)
        return actual(*args, **kwargs)

    monkeypatch.setattr(service, "publish_owned_replacement", changed)
    with pytest.raises(ValueError):
        run(source, parent / "grid")
    assert fired and {p.name for p in parent.iterdir()} == {"foreign"}
    assert retained.is_dir() and (parent / "foreign").read_text() == "foreign"


def test_candidate_substitution_preserves_both_namespaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, _ = producer()
    service = importlib.import_module(module.__name__ + ".service")
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    actual = service.publish_owned_replacement
    retained = []

    def changed(writer: Any, *args: Any, **kwargs: Any) -> Any:
        old = writer.root.with_name("retained-original")
        writer.root.rename(old)
        writer.root.mkdir()
        (writer.root / "foreign").write_text("foreign")
        retained.append((old, writer.root))
        return actual(writer, *args, **kwargs)

    monkeypatch.setattr(service, "publish_owned_replacement", changed)
    with pytest.raises(ValueError):
        run(source, tmp_path / "grid")
    assert retained and not (tmp_path / "grid").exists()
    old, foreign = retained[0]
    assert (old / "report.json").is_file() and (
        foreign / "foreign"
    ).read_text() == "foreign"


def test_whole_uuid_ledger_and_sparse_cells_have_disjoint_conservation(
    tmp_path: Path,
) -> None:
    source = database(tmp_path)
    selected(source)
    keys = [f"00000000-0000-0000-0000-{value:012d}" for value in range(1, 9)]
    with sqlite3.connect(source) as con:
        for fid, key in enumerate(keys[1:], 2):
            con.execute(
                "INSERT INTO lamning(fid,uuid,antikvariskbedomning) VALUES(?,?,?)",
                (fid, key, "other" if fid == 2 else "Fornlämning"),
            )
        values = [
            (keys[0], native_point()),
            (keys[3], native_point()),
            (keys[3], None),
            (keys[4], b"bad"),
            (keys[5], gpkg(point(500000, 0))),
            (keys[6], native_point(15.9, 60.7)),
            (keys[7], native_point(16.1, 61.1)),
        ]
        con.executemany("INSERT INTO point(lamning_uuid,geometri) VALUES(?,?)", values)
        con.execute(
            'INSERT INTO "lämningar_sverige_lägesosäkerhet"(lamning_uuid,geometri) VALUES(?,?)',
            (keys[2], b"not_point_location"),
        )
    result = run(source, tmp_path / "grid")
    ledger = rows(result.directory)
    report = result.report()
    assert [r["native_lamning_uuid"] for r in ledger] == keys
    assert [r["disposition"] for r in ledger] == [
        "included",
        "unselected_native_class",
        "no_primary_point_occurrence",
        "multiple_primary_point_occurrences",
        "unsupported_sole_point",
        "unsupported_projection_or_location",
        "included",
        "included",
    ]
    assert report["counts"] == {
        "source_uuids": 8,
        "selected_class_uuids": 7,
        "included_uuids": 3,
        "raw_point_occurrences": 7,
        "valid_point_occurrences": 5,
    }
    assert sum(report["dispositions"].values()) == 8 and report["cell_count_total"] == 3
    cells = list(
        csv.DictReader(io.StringIO((result.directory / "cell-counts.csv").read_text()))
    )
    assert cells == [
        {"west_longitude": "15", "south_latitude": "60", "uuid_count": "2"},
        {"west_longitude": "16", "south_latitude": "61", "uuid_count": "1"},
    ]
    assert result.directory.stat().st_mode & 0o777 == 0o700


def test_complete_output_byte_budget_refuses_without_final_partial_tree(
    tmp_path: Path,
) -> None:
    source = database(tmp_path)
    selected(source)
    add_geometry(source, "point", native_point())
    with pytest.raises(ValueError, match="byte budget"):
        run(source, tmp_path / "grid", max_output_bytes=128)
    assert not (tmp_path / "grid").exists()
