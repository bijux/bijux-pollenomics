"""Keep current source dependencies physically stable across native body handoffs."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from ...capture.receipts import _object, _safe_root
from ...resource_catalogue.archive.files import _digest
from .validation import MAX_BYTES, MAX_FILES, MAX_MEMBER_BYTES


class _CurrentContextSeals:
    """Refuse physical drift; semantic authority remains with maintained validators."""

    def __init__(
        self,
        *,
        context_directory: Path,
        expected_context_sha256: str,
        native_archive_directory: Path,
        expected_native_archive_sha256: str | None = None,
        _max_bytes: int = MAX_BYTES,
        _max_files: int = MAX_FILES,
    ) -> None:
        # Ancestry supplies its existing larger complete-source profile.
        if (
            type(_max_bytes) is not int
            or not 0 < _max_bytes <= 768 * 1024 * 1024
            or type(_max_files) is not int
            or not 0 < _max_files <= 40960
        ):
            raise ValueError("Current source dependency profile is not finite")
        self._max_bytes, self._max_files = _max_bytes, _max_files
        self._context_root = _safe_root(context_directory)
        self._native_root = _safe_root(native_archive_directory)
        self._context_pin = expected_context_sha256
        self._native_pin = expected_native_archive_sha256
        self._stack = ExitStack()
        self._trees: dict[tuple[Path, str | None], BoundedInputTree] = {}
        self._members: dict[tuple[int, int], int] = {}
        self._used = self._active = False

    def _seal(self, directory: Path, selected: str | None = None) -> BoundedInputTree:
        root = _safe_root(directory)
        key = root, selected
        if key not in self._trees:
            tree = self._stack.enter_context(
                BoundedInputTree(
                    root,
                    max_bytes=self._max_bytes,
                    max_files=self._max_files,
                    selected=selected,
                )
            )
            for stamp in tree.files.values():
                self._members[stamp[0], stamp[1]] = stamp[4]
            if (
                len(self._members) > self._max_files
                or sum(self._members.values()) > self._max_bytes
            ):
                raise ValueError(
                    "Current source dependency closure exceeds finite bounds"
                )
            self._trees[key] = tree
        return self._trees[key]

    def _pin(self, path: Path, pin: str) -> dict[str, Any]:
        tree = self._seal(path.parent, path.name)
        raw = tree.read(path, max_bytes=MAX_MEMBER_BYTES)
        if sha256(raw).hexdigest() != pin:
            raise ValueError("Current source dependency identity differs")
        return _object(raw)

    def __enter__(self) -> _CurrentContextSeals:
        """Seal only current metadata dependencies, never unselected native bodies."""
        if type(self) is not _CurrentContextSeals:
            raise ValueError("Current source operation requires its exact private type")
        if self._used:
            raise ValueError("Current source operation cannot be reused")
        self._used = True
        try:
            self._seal(self._context_root)
            context = self._pin(self._context_root / "manifest.json", self._context_pin)
            native_pin = context["native_archive"]["manifest_sha256"]
            if self._native_pin is not None and native_pin != self._native_pin:
                raise ValueError("Current source independent native anchor differs")
            native = self._pin(self._native_root / "manifest.json", native_pin)
            self._seal(self._native_root / "catalogue")
            self._pin(
                self._native_root / "catalogue/manifest.json",
                native["catalogue_manifest_sha256"],
            )
            claim = context["native_archive"]
            self._pin(
                self._native_root / "catalogue/source-inventory.json",
                claim["current_roster_sha256"],
            )
            captures = claim["metadata_capture_manifest_sha256s"]
            if (
                not isinstance(captures, list)
                or len(captures) > MAX_FILES
                or any(not _digest(pin) for pin in captures)
            ):
                raise ValueError("Current metadata dependency identities are malformed")
            for capture_pin in captures:
                self._seal(self._native_root / "captures" / capture_pin)
            historical = claim["historical_metadata_part_sha256s"]
            if not isinstance(historical, list) or any(
                not _digest(pin) for pin in historical
            ):
                raise ValueError("Current historical metadata identities are malformed")
            if historical:
                root = self._native_root / "captures/original-metadata"
                self._pin(
                    root / "manifest.json", claim["original_relational_manifest_sha256"]
                )
                found = set()
                for name, member in native["files"].items():
                    if (
                        name.startswith("captures/original-metadata/")
                        and member["sha256"] in historical
                    ):
                        path = self._native_root / name
                        self._seal(path.parent, path.name)
                        found.add(member["sha256"])
                if found != set(historical):
                    raise ValueError("Current historical metadata seal closure differs")
            self._active = True
            self.check()
            return self
        except (KeyError, TypeError, AttributeError) as error:
            self._close()
            raise ValueError(
                "Current source dependency metadata is malformed"
            ) from error
        except BaseException:
            self._close()
            raise

    def check(self) -> None:
        """Refuse changed permission inputs before the next native entity is opened."""
        if type(self) is not _CurrentContextSeals or not self._active:
            raise ValueError("Current source operation is not active")
        for tree in self._trees.values():
            tree.check()

    def _close(self) -> None:
        self._active = False
        self._trees.clear()
        self._members.clear()
        self._stack.close()

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        """Check success and always close descriptors without masking a primary error."""
        try:
            if kind is None:
                self.check()
        finally:
            self._close()


def context_seals(options: Mapping[str, Any]) -> _CurrentContextSeals:
    """Create a fresh private lifetime from the public API's independent anchors."""
    return _CurrentContextSeals(
        context_directory=options["context_directory"],
        expected_context_sha256=options["expected_context_sha256"],
        native_archive_directory=options["native_archive_directory"],
        expected_native_archive_sha256=options.get("expected_native_archive_sha256"),
    )
