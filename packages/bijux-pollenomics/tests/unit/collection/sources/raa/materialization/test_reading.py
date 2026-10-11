"""Actual SQLite write, view, journal and source-identity counterexamples."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sqlite3

import pytest

from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    read_only_database,
)


def fixture_database(path: Path) -> tuple[str, int]:
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE "source rows"(id TEXT, value INTEGER)')
        connection.execute('INSERT INTO "source rows" VALUES (?, ?)', ("Å😀", 0))
        connection.execute('INSERT INTO "source rows" VALUES (?, ?)', ("empty", None))
        connection.execute('CREATE VIEW source_view AS SELECT * FROM "source rows"')
        connection.execute("PRAGMA application_id=1196444487")
    content = path.read_bytes()
    return sha256(content).hexdigest(), len(content)


def test_read_only_sqlite_preserves_zero_null_unicode_and_source(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source ? query.gpkg"
    digest, size = fixture_database(path)
    with read_only_database(
        path, expected_sha256=digest, expected_byte_count=size
    ) as db:
        assert [
            tuple(row)
            for row in db.execute('SELECT * FROM "source rows" ORDER BY rowid')
        ] == [
            ("Å😀", 0),
            ("empty", None),
        ]
        assert db.execute("PRAGMA application_id").fetchone()[0] == 1196444487
        assert len(db.execute('PRAGMA table_info("source rows")').fetchall()) == 2
    assert sha256(path.read_bytes()).hexdigest() == digest
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize(
    "sql",
    [
        'INSERT INTO "source rows" VALUES ("bad",1)',
        'DELETE FROM "source rows"',
        "PRAGMA query_only=OFF",
        "PRAGMA trusted_schema=ON",
        "PRAGMA application_id=0",
        "ATTACH DATABASE ':memory:' AS other",
        "SELECT load_extension('unowned')",
        "SELECT * FROM source_view",
    ],
)
def test_writes_attachments_extensions_and_source_views_refuse(
    tmp_path: Path, sql: str
) -> None:
    path = tmp_path / "source.gpkg"
    digest, size = fixture_database(path)
    with (
        read_only_database(
            path, expected_sha256=digest, expected_byte_count=size
        ) as db,
        pytest.raises(sqlite3.DatabaseError),
    ):
        db.execute(sql).fetchall()


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_sidecars_cannot_be_silently_ignored_by_immutable_mode(
    tmp_path: Path, suffix: str
) -> None:
    path = tmp_path / "source.gpkg"
    digest, size = fixture_database(path)
    path.with_name(path.name + suffix).write_bytes(b"")
    with (
        pytest.raises(ValueError, match="standalone"),
        read_only_database(path, expected_sha256=digest, expected_byte_count=size),
    ):
        pytest.fail("sidecar was ignored")


def test_symlink_and_changed_or_falsely_typed_identity_refuse(tmp_path: Path) -> None:
    path = tmp_path / "source.gpkg"
    digest, size = fixture_database(path)
    link = tmp_path / "linked.gpkg"
    link.symlink_to(path)
    for candidate, expected_hash, expected_size in [
        (link, digest, size),
        (path, "0" * 64, size),
        (path, digest, True),
    ]:
        with (
            pytest.raises(ValueError),
            read_only_database(
                candidate,
                expected_sha256=expected_hash,
                expected_byte_count=expected_size,
            ),
        ):
            pytest.fail("invalid source identity admitted")


def test_external_source_mutation_is_detected_before_return(tmp_path: Path) -> None:
    path = tmp_path / "source.gpkg"
    digest, size = fixture_database(path)
    with (
        pytest.raises(ValueError, match="mismatch"),
        read_only_database(
            path, expected_sha256=digest, expected_byte_count=size
        ) as db,
    ):
        assert db.execute('SELECT count(*) FROM "source rows"').fetchone()[0] == 2
        with sqlite3.connect(path) as writer:
            writer.execute('UPDATE "source rows" SET value=9')
