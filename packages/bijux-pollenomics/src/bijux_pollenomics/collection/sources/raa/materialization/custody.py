"""Keep every native SQLite read inside the admitted source attachment lifetime."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import closing
import operator
import sqlite3
from typing import Any, NoReturn, TypeVar, overload

_DEFAULT_FETCH_SIZE = object()

_CursorT = TypeVar("_CursorT", bound=sqlite3.Cursor)


def _refuse_native_surface(check: Callable[[], None], operation: str) -> NoReturn:
    check()
    raise ValueError(f"RAÄ source context does not permit native {operation}")


class SourceCursor(sqlite3.Cursor):
    """Check physical source custody before and after native row retrieval."""

    def _check(self) -> None:
        connection = self.connection
        if not isinstance(connection, SourceConnection):
            raise ValueError("RAÄ source cursor has no admitted connection")
        connection.check_source()

    def execute(self, sql: str, parameters: Any = ()) -> SourceCursor:
        """Execute one statement while the original source remains current."""
        self._check()
        super().execute(sql, parameters)
        self._check()
        return self

    def executescript(self, sql_script: str, /) -> SourceCursor:
        """Refuse scripts that step source rows outside the guarded iterator."""
        _refuse_native_surface(self._check, "executescript")

    def executemany(self, sql: str, parameters: Iterable[Any], /) -> SourceCursor:
        """Refuse bulk DML, which has no permitted read-only source operation."""
        _refuse_native_surface(self._check, "executemany")

    def __next__(self) -> Any:
        """Check source custody before exposing the next native row."""
        self._check()
        row = super().__next__()
        self._check()
        return row

    def fetchone(self) -> Any:
        """Return one native row under current source custody."""
        self._check()
        row = super().fetchone()
        self._check()
        return row

    def fetchall(self) -> list[Any]:
        """Collect remaining native rows with a custody check for each row."""
        return list(self)

    def fetchmany(self, size: Any = _DEFAULT_FETCH_SIZE) -> list[Any]:
        """Preserve native batch sizes while checking custody for each row."""
        self._check()
        count = operator.index(self.arraysize if size is _DEFAULT_FETCH_SIZE else size)
        # Native patch releases differ on zero, negative and integer size bounds.
        # A literal-only memory cursor validates that policy without source SQL.
        with (
            closing(sqlite3.connect(":memory:")) as policy,
            closing(policy.execute("SELECT NULL")) as probe,
        ):
            accepts_rows = bool(probe.fetchmany(count))
        self._check()
        if not accepts_rows:
            return []
        if count <= 0:
            return self.fetchall()
        rows = []
        for _ in range(count):
            try:
                row = next(self)
            except StopIteration:
                break
            rows.append(row)
        return rows


class SourceConnection(sqlite3.Connection):
    """Native read-only connection whose cursors retain the current source seal."""

    _check_source: Callable[[], None] | None = None
    _authorizer_sealed = False

    def bind_source(self, check: Callable[[], None]) -> None:
        """Attach one operation-local physical source check."""
        if self._check_source is not None:
            raise ValueError("RAÄ source connection cannot be rebound")
        self._check_source = check
        self.check_source()

    def check_source(self) -> None:
        """Refuse a detached or stale operation-local source."""
        if self._check_source is None:
            raise ValueError("RAÄ source connection has no active custody")
        self._check_source()

    @overload
    def cursor(self, factory: None = None) -> SourceCursor: ...

    @overload
    def cursor(self, factory: Callable[[sqlite3.Connection], _CursorT]) -> _CursorT: ...

    def cursor(
        self, factory: Callable[[sqlite3.Connection], sqlite3.Cursor] | None = None
    ) -> sqlite3.Cursor:
        """Keep custom factories from bypassing native cursor custody checks."""
        self.check_source()
        if factory not in (None, SourceCursor):
            raise ValueError("RAÄ source reads require a custody-checked cursor")
        return super().cursor(SourceCursor)

    def execute(self, sql: str, parameters: Any = ()) -> SourceCursor:
        """Route statement execution through a custody-checked native cursor."""
        return self.cursor().execute(sql, parameters)

    def executescript(self, sql_script: str, /) -> SourceCursor:
        """Refuse non-row script dispatch before native statement execution."""
        _refuse_native_surface(self.check_source, "executescript")

    def executemany(self, sql: str, parameters: Iterable[Any], /) -> SourceCursor:
        """Refuse bulk DML before consuming bindings or executing statements."""
        _refuse_native_surface(self.check_source, "executemany")

    def serialize(self, *, name: str = "main") -> bytes:
        """Refuse whole-database buffers outside the guarded row read profile."""
        _refuse_native_surface(self.check_source, "serialize")

    def deserialize(self, data: Any, /, *, name: str = "main") -> None:
        """Refuse substitution of an unadmitted in-memory database."""
        _refuse_native_surface(self.check_source, "deserialize")

    def backup(
        self,
        target: sqlite3.Connection,
        *,
        pages: int = -1,
        progress: Callable[[int, int, int], object] | None = None,
        name: str = "main",
        sleep: float = 0.250,
    ) -> None:
        """Refuse native transfer jobs outside the admitted row lifetime."""
        _refuse_native_surface(self.check_source, "backup")

    def blobopen(
        self,
        table: str,
        column: str,
        row: int,
        /,
        *,
        readonly: bool = False,
        name: str = "main",
    ) -> sqlite3.Blob:
        """Refuse raw handles whose reads cannot retain per-row custody checks."""
        _refuse_native_surface(self.check_source, "blobopen")

    def _seal_authorizer(self, callback: Any) -> None:
        self.check_source()
        if self._authorizer_sealed:
            raise ValueError("RAÄ source authorizer cannot be rebound")
        sqlite3.Connection.set_authorizer(self, callback)
        self._authorizer_sealed = True

    def set_authorizer(self, authorizer_callback: Any) -> None:
        """Refuse removal or replacement of the admitted source SQL policy."""
        _refuse_native_surface(self.check_source, "set_authorizer")

    def enable_load_extension(self, enabled: bool, /) -> None:
        """Permit disabling extensions while refusing any enable request."""
        self.check_source()
        if enabled:
            _refuse_native_surface(self.check_source, "enable_load_extension")
        native = getattr(sqlite3.Connection, "enable_load_extension", None)
        if native is not None:
            native(self, False)
        self.check_source()

    def load_extension(self, path: str, /, *, entrypoint: str | None = None) -> None:
        """Refuse direct native loading before any extension path lookup."""
        _refuse_native_surface(self.check_source, "load_extension")

    def setconfig(self, op: int, enable: bool = True, /) -> None:
        """Refuse configuration changes that can lift native connection guards."""
        _refuse_native_surface(self.check_source, "setconfig")
