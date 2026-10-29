"""Preserve reviewed input identities and lexical launch entries across preparation."""

from __future__ import annotations

from collections.abc import Iterable
import hashlib
import os
from pathlib import Path
from typing import Any


def pin(path: Path) -> dict[str, Any]:
    if (
        not path.is_absolute()
        or ".." in path.parts
        or path.is_symlink()
        or not path.is_file()
    ):
        raise ValueError("Custody pin must name an absolute regular physical file")
    with path.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": str(path), "sha256": checksum, "bytes": path.stat().st_size}


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    name = row["path"]
    if (
        not isinstance(name, str)
        or not Path(name).is_absolute()
        or ".." in Path(name).parts
        or type(row.get("bytes")) is not int
        or row["bytes"] < 0
        or not isinstance(row.get("sha256"), str)
        or len(row["sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in row["sha256"])
    ):
        raise ValueError("Malformed custody row")
    return {key: row[key] for key in ("path", "sha256", "bytes")}


def incoming_rows(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    incoming: dict[str, dict[str, Any]] = {}
    for row in rows:
        normalized = normalize_row(row)
        name = normalized["path"]
        if name in incoming:
            raise ValueError("Duplicate custody row within one input group")
        incoming[name] = normalized
    return incoming


def exact_union(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for group in groups:
        incoming = incoming_rows(group)
        for name, row in incoming.items():
            if name in unique and unique[name] != row:
                raise ValueError(
                    "Cannot rebaseline an already authenticated input: " + name
                )
        unique.update(incoming)
    return [unique[name] for name in sorted(unique)]


def verify_rows(rows: Iterable[dict[str, Any]]) -> None:
    for row in exact_union(rows):
        if pin(Path(row["path"])) != row:
            raise ValueError("Originally authenticated input changed: " + row["path"])


def entry_aliases(entries: Iterable[Path]) -> list[dict[str, str]]:
    aliases: dict[str, dict[str, str]] = {}
    for entry in entries:
        if not entry.is_absolute() or ".." in entry.parts:
            raise ValueError("Launch entry must be absolute and normalized")
        pending = [entry]
        visited: set[Path] = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            for component in reversed((path, *path.parents)):
                if component.is_symlink():
                    raw = os.readlink(component)
                    resolved = component.resolve(strict=True)
                    aliases[str(component)] = {
                        "path": str(component),
                        "target": raw,
                        "resolved": str(resolved),
                    }
                    target = (
                        Path(raw) if Path(raw).is_absolute() else component.parent / raw
                    )
                    pending.append(Path(os.path.normpath(target)))
        if not entry.is_file():
            raise ValueError("Launch entry must resolve to a regular executable")
    return [aliases[name] for name in sorted(aliases)]


def verify_entry_aliases(rows: list[dict[str, str]], entries: list[str]) -> None:
    if entry_aliases(Path(name) for name in entries) != rows:
        raise ValueError("Lexical launch-entry alias chain changed")


class InputScope:
    """An immutable initial authority extended only by conflict-checked new inputs."""

    def __init__(self, rows: Iterable[dict[str, Any]], entries: Iterable[Path]) -> None:
        self._rows = incoming_rows(rows)
        self.entries = [str(path) for path in entries]
        self.aliases = entry_aliases(Path(name) for name in self.entries)
        self.source_namespaces: list[dict[str, Any]] = []

    @property
    def rows(self) -> list[dict[str, Any]]:
        return [dict(self._rows[name]) for name in sorted(self._rows)]

    def extend(self, rows: Iterable[dict[str, Any]]) -> None:
        incoming = incoming_rows(rows)
        for name, row in incoming.items():
            if name in self._rows and self._rows[name] != row:
                raise ValueError(
                    "Cannot rebaseline an already authenticated input: " + name
                )
        self._rows.update(incoming)

    def declared(self, path: Path, checksum: str) -> None:
        row = pin(path)
        if row["sha256"] != checksum:
            raise ValueError("Declared reference changed before freeze: " + str(path))
        self.extend([row])

    def capture(self, paths: Iterable[Path]) -> None:
        self.extend(pin(path) for path in sorted(set(paths)))

    def source_namespace(
        self, root: Path, names: Iterable[str], aliases: list[dict[str, str]]
    ) -> None:
        self.source_namespaces.append(
            {"root": str(root), "names": sorted(names), "aliases": aliases}
        )

    def verify(self) -> None:
        for namespace in self.source_namespaces:
            root = Path(namespace["root"])
            actual = []
            for entry in root.rglob("*"):
                relative = entry.relative_to(root)
                if (
                    namespace.get("skip_artifacts", True)
                    and relative.parts[0] == "artifacts"
                ):
                    continue
                if entry.is_symlink() or entry.is_file():
                    actual.append(relative.as_posix())
                elif not entry.is_dir():
                    raise ValueError("Source namespace contains an unlisted special")
            if sorted(actual) != namespace["names"]:
                raise ValueError("Source namespace membership changed")
            for row in namespace["aliases"]:
                entry = root / row["path"]
                if (
                    not entry.is_symlink()
                    or os.readlink(entry) != row["target"]
                    or not entry.resolve(strict=True).is_relative_to(root)
                ):
                    raise ValueError("Source namespace alias changed")
        verify_rows(self.rows)
        verify_entry_aliases(self.aliases, self.entries)

    def bind(self, plan: dict[str, Any], input_key: str = "input_pins") -> None:
        self.extend(plan.get(input_key, []))
        self.verify()
        plan[input_key] = list(self.rows)
        plan["qualified_input_namespaces"] = self.source_namespaces
        plan["runtime_entry_raw_aliases"] = self.aliases
        plan["runtime_entry_lexical_paths"] = self.entries
