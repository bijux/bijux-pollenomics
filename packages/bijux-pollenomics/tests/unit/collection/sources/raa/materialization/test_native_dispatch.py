"""Native dispatch cannot lift the bounded admitted-source read contract."""

from collections.abc import Callable
from contextlib import closing, suppress
from pathlib import Path
import sqlite3
import sys
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.raa.materialization import reading
from bijux_pollenomics.collection.sources.raa.materialization.custody import (
    SourceConnection,
)

from .test_reading import fixture_database
from .test_source_custody import _replacement


@pytest.mark.parametrize("surface", ["connection", "cursor"])
def test_script_dispatch_cannot_read_a_revoked_source(
    tmp_path: Path, surface: str
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    observed: list[Any] = []
    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as connection,
    ):

        def spy(value: Any) -> Any:
            observed.append(value)
            return value

        connection.create_function("spy", 1, spy)
        target = connection if surface == "connection" else connection.cursor()
        path.rename(tmp_path / "detached.gpkg")
        target.executescript('SELECT spy(value) FROM "source rows";')
    assert observed == []


@pytest.mark.parametrize("method", ["serialize", "backup", "blobopen"])
def test_native_transfer_handles_cannot_expose_a_revoked_source(
    tmp_path: Path, method: str
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    observed: list[Any] = []
    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as connection,
    ):
        path.rename(tmp_path / "detached.gpkg")
        if method == "serialize":
            observed.append(len(connection.serialize()))
        elif method == "backup":
            from contextlib import closing

            with closing(sqlite3.connect(":memory:")) as target:
                connection.backup(target)
                observed.append(
                    target.execute('SELECT count(*) FROM "source rows"').fetchone()[0]
                )
        else:
            with connection.blobopen("source rows", "id", 1, readonly=True) as stream:
                observed.append(len(stream.read()))
    assert observed == []


def test_deserialize_cannot_replace_the_admitted_native_database(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    replacement = _replacement(path).read_bytes()
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as connection:
        with pytest.raises(ValueError):
            connection.deserialize(replacement)
        assert (
            connection.execute(
                'SELECT value FROM "source rows" ORDER BY rowid'
            ).fetchone()[0]
            == 0
        )


@pytest.mark.parametrize("surface", ["connection", "cursor"])
def test_script_and_bulk_dml_refuse_without_callbacks_or_binding_reads(
    tmp_path: Path, surface: str
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    calls = []

    def spy(value: Any) -> Any:
        calls.append(value)
        return value

    def bindings() -> Any:
        calls.append("bindings")
        yield ("unexpected", 1)

    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as connection:
        connection.create_function("spy", 1, spy)
        target = connection if surface == "connection" else connection.cursor()
        with pytest.raises(ValueError, match="executescript"):
            target.executescript(
                'SELECT spy(value) FROM "source rows"; SELECT spy(value) FROM "source rows";'
            )
        with pytest.raises(ValueError, match="executemany"):
            target.executemany('INSERT INTO "source rows" VALUES (?, ?)', bindings())
        assert (
            connection.execute('SELECT count(*) FROM "source rows"').fetchone()[0] == 2
        )
    assert calls == []


def test_python_dump_iterator_uses_guarded_source_cursors(tmp_path: Path) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    with (
        pytest.raises(ValueError),
        reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as connection,
    ):
        assert any("Å😀" in statement for statement in connection.iterdump())
        deferred = connection.iterdump()
        path.rename(tmp_path / "detached.gpkg")
        with pytest.raises(ValueError):
            next(deferred)


@pytest.mark.parametrize("replacement", [None, "permit"])
def test_authorizer_replacement_cannot_attach_unadmitted_database(
    tmp_path: Path, replacement: str | None
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    foreign = _replacement(path)
    observed: list[Any] = []
    try:
        with reading.read_only_database(
            path, expected_sha256=pin, expected_byte_count=size
        ) as connection:
            connection.set_authorizer(
                None if replacement is None else lambda *args: sqlite3.SQLITE_OK
            )
            connection.execute("ATTACH DATABASE ? AS foreign_capture", (str(foreign),))
            observed.extend(
                tuple(row)
                for row in connection.execute(
                    'SELECT value FROM foreign_capture."source rows"'
                )
            )
    except ValueError:
        pass
    assert observed == []


def test_extension_enable_and_load_refuse_before_native_loader_callbacks(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    extension = tmp_path / "generated-invalid-extension.dylib"
    extension.write_bytes(b"generated invalid library fixture")
    events = []
    active = [True]
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as connection:

        def audit(event: str, args: tuple[Any, ...]) -> None:
            if (
                active[0]
                and event in {"sqlite3.enable_load_extension", "sqlite3.load_extension"}
                and args[0] is connection
            ):
                events.append(event)

        sys.addaudithook(audit)
        try:
            try:
                connection.enable_load_extension(True)
                with suppress(sqlite3.Error):
                    connection.load_extension(str(extension))
            except ValueError:
                pass
        finally:
            active[0] = False
    assert events == []


def test_native_refusals_do_not_depend_on_a_writable_connection_flag() -> None:
    with closing(sqlite3.connect(":memory:", factory=SourceConnection)) as connection:
        connection.bind_source(lambda: None)
        connection.execute("CREATE TABLE generated(id TEXT)")
        connection.execute("INSERT INTO generated VALUES ('fixture')")
        with closing(sqlite3.connect(":memory:")) as target:
            actions: tuple[Callable[[], object], ...] = (
                lambda: connection.executescript("SELECT 1;"),
                lambda: connection.executemany(
                    "INSERT INTO generated VALUES (?)", [("new",)]
                ),
                connection.serialize,
                lambda: connection.deserialize(b"generated"),
                lambda: connection.backup(target),
                lambda: connection.blobopen("generated", "id", 1, readonly=True),
                lambda: connection.set_authorizer(None),
                lambda: connection.enable_load_extension(True),
                lambda: connection.load_extension("generated-never-opened.dylib"),
                lambda: connection.setconfig(0, True),
            )
            for action in actions:
                with pytest.raises(ValueError):
                    action()
        assert connection.execute("SELECT count(*) FROM generated").fetchone()[0] == 1


def test_extension_disable_remains_available_without_lifting_loader_policy(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.gpkg"
    pin, size = fixture_database(path)
    with reading.read_only_database(
        path, expected_sha256=pin, expected_byte_count=size
    ) as connection:
        connection.enable_load_extension(False)
        with pytest.raises(ValueError, match="load_extension"):
            connection.load_extension(str(tmp_path / "never-opened.dylib"))
        assert (
            connection.execute('SELECT count(*) FROM "source rows"').fetchone()[0] == 2
        )
