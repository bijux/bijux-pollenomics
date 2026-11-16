"""Native reads must stay attached to the originally admitted source file."""

import os
from pathlib import Path
import sqlite3
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.raa.materialization import reading
from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    inspect_database_identity,
)

from .test_reading import fixture_database


def _replacement(path: Path) -> Path:
    replacement = path.with_name("replacement.gpkg")
    replacement.write_bytes(path.read_bytes())
    with sqlite3.connect(replacement) as writer:
        writer.execute('UPDATE "source rows" SET value=9')
    return replacement


@pytest.mark.parametrize("equal_bytes", [False, True])
def test_changed_attachment_refuses_before_any_sqlite_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, equal_bytes: bool
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    replacement = _replacement(path)
    if equal_bytes:
        replacement.write_bytes(path.read_bytes())
    original = inspect_database_identity
    connections = []

    def inspected(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        path.rename(tmp_path / "held-original.gpkg")
        os.replace(replacement, path)
        return result

    native_connect = sqlite3.connect

    def connected(*args: Any, **kwargs: Any) -> Any:
        connections.append(args[0])
        return native_connect(*args, **kwargs)

    monkeypatch.setattr(reading, "inspect_database_identity", inspected)
    monkeypatch.setattr(sqlite3, "connect", connected)
    with (
        pytest.raises(ValueError),
        reading.read_only_database(path, expected_sha256=pin, expected_byte_count=size),
    ):
        pytest.fail("Changed source attachment admitted")
    assert connections == []


def test_native_open_uses_held_descriptor_and_refuses_substitution_before_queries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    replacement = _replacement(path)
    native_connect = sqlite3.connect
    connections = []
    queries: list[str] = []

    def connected(database: str, **kwargs: Any) -> Any:
        assert database.startswith("file:/dev/fd/")
        path.rename(tmp_path / "held-original.gpkg")
        os.replace(replacement, path)
        result = native_connect(database, **kwargs)
        result.set_trace_callback(queries.append)
        connections.append(result)
        return result

    monkeypatch.setattr(sqlite3, "connect", connected)
    with (
        pytest.raises(ValueError),
        reading.read_only_database(path, expected_sha256=pin, expected_byte_count=size),
    ):
        pytest.fail("Changed source attachment admitted")
    assert queries == [] and len(connections) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        sqlite3.Connection.execute(connections[0], "SELECT 1")


def test_cursor_stops_before_the_next_native_row_after_in_place_change(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as db,
    ):
        cursor = db.execute('SELECT * FROM "source rows" ORDER BY rowid')
        assert tuple(next(cursor)) == ("Å😀", 0)
        with sqlite3.connect(path) as writer:
            writer.execute('UPDATE "source rows" SET value=9')
        next(cursor)
        pytest.fail("Changed source row returned")


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_new_auxiliary_state_refuses_before_the_next_source_query(
    tmp_path: Path, suffix: str
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as db,
    ):
        path.with_name(path.name + suffix).write_bytes(b"")
        db.execute('SELECT * FROM "source rows"').fetchall()
        pytest.fail("Auxiliary source state was ignored")


def test_primary_failure_survives_source_custody_cleanup_failure(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    primary = RuntimeError("generated consumer failure")
    with (
        pytest.raises(RuntimeError) as caught,
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as db,
    ):
        assert db.execute('SELECT count(*) FROM "source rows"').fetchone()[0] == 2
        path.rename(tmp_path / "held-original.gpkg")
        raise primary
    assert caught.value is primary
    assert any("source cleanup failed" in note for note in primary.__notes__)


def test_positive_native_descriptor_connection_and_cursor_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    native_connect = sqlite3.connect
    descriptors: list[int] = []

    def connected(database: str, **kwargs: Any) -> Any:
        descriptors.append(int(database.split("?", 1)[0].rsplit("/", 1)[1]))
        assert kwargs["uri"] is True and database.endswith("?mode=ro&immutable=1")
        return native_connect(database, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connected)
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as db:
        cursor = db.execute('SELECT * FROM "source rows" ORDER BY rowid')
        assert [tuple(row) for row in cursor] == [("Å😀", 0), ("empty", None)]
        assert os.fstat(descriptors[0]).st_ino == path.stat().st_ino
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
    with pytest.raises(sqlite3.ProgrammingError):
        sqlite3.Connection.execute(db, "SELECT 1")
    with pytest.raises((ValueError, sqlite3.ProgrammingError)):
        next(cursor)


def test_identity_hash_refuses_changed_leaf_before_reading_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    replacement = _replacement(path)
    replacement_inode = replacement.stat().st_ino
    native_open, native_read = os.open, os.read
    changed = False
    replacement_reads: list[int] = []

    def opened(name: Any, *args: Any, **kwargs: Any) -> int:
        nonlocal changed
        if name == path.name and kwargs.get("dir_fd") is not None and not changed:
            path.rename(tmp_path / "held-original.gpkg")
            os.replace(replacement, path)
            changed = True
        return native_open(name, *args, **kwargs)

    def read(descriptor: int, count: int) -> bytes:
        raw = native_read(descriptor, count)
        if os.fstat(descriptor).st_ino == replacement_inode:
            replacement_reads.append(len(raw))
        return raw

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    with pytest.raises(ValueError):
        inspect_database_identity(path, expected_sha256=pin, expected_byte_count=size)
    assert changed and replacement_reads == []


@pytest.mark.parametrize(
    "size",
    [
        "default",
        0,
        -1,
        1,
        2,
        None,
        1.5,
        2**63,
        2**31 - 1,
        2**31,
        -(2**31),
        -(2**31) - 1,
    ],
)
def test_fetchmany_matches_native_argument_and_arraysize_semantics(
    tmp_path: Path, size: Any
) -> None:
    path = tmp_path / "source.gpkg"
    pin, count = fixture_database(path)
    query = 'SELECT * FROM "source rows" ORDER BY rowid'

    def result(cursor: sqlite3.Cursor) -> list[tuple[Any, ...]]:
        cursor.arraysize = 2
        rows = cursor.fetchmany() if size == "default" else cursor.fetchmany(size)
        return [tuple(row) for row in rows]

    failure: type[TypeError] | type[OverflowError] | type[ValueError] | None = None
    expected: list[tuple[Any, ...]] = []
    with sqlite3.connect(path) as native:
        try:
            expected = result(native.execute(query))
        except (TypeError, OverflowError, ValueError) as error:
            failure = type(error)
        else:
            failure = None
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=count
    ) as current:
        if failure is not None:
            with pytest.raises(failure):
                result(current.execute(query))
        else:
            assert result(current.execute(query)) == expected


def test_fetchmany_preserves_none_factory_rows_before_later_native_rows(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)

    def factory(_cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> Any:
        return None if row[0] == "Å😀" else row[0]

    query = 'SELECT * FROM "source rows" ORDER BY rowid'
    with sqlite3.connect(path) as native:
        native.row_factory = factory
        expected = native.execute(query).fetchmany(2)
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as current:
        current.row_factory = factory
        observed = current.execute(query).fetchmany(2)
    assert expected == [None, "empty"] and observed == expected


def test_factory_mutation_stops_batch_before_a_later_row_callback(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    calls = []

    def factory(_cursor: sqlite3.Cursor, row: tuple[Any, ...]) -> None:
        calls.append(row[0])
        with sqlite3.connect(path) as writer:
            writer.execute('UPDATE "source rows" SET value=9')
        return

    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as current,
    ):
        current.row_factory = factory
        current.execute('SELECT * FROM "source rows" ORDER BY rowid').fetchmany(2)
        pytest.fail("Changed source returned a batch")
    assert calls == ["Å😀"]
