"""Finite literal authority inputs held stable through one RAÄ decision."""

from __future__ import annotations

from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
import stat
from types import TracebackType

from ....core.filesystem import BoundedInputTree
from .inventory import decode_source_object

INPUT_PATHS = {
    "raw_inventory": "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
    "raw_summary": "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
    "normalized_metadata": "raa/normalized/sweden_archaeology_layer.json",
    "normalized_density": "raa/normalized/sweden_archaeology_density.geojson",
    "scientific_review": "raa/review/spatiotemporal_review.json",
    "membership_ledger": "raa/derived/sweden_archaeology_density_membership.json",
    "boundary_manifest": "boundaries/raw/source_manifest.json",
    "sweden_boundary": "boundaries/raw/sweden.geojson",
    "norway_boundary": "boundaries/raw/norway.geojson",
    "denmark_boundary": "boundaries/raw/denmark.geojson",
    "finland_boundary": "boundaries/raw/finland.geojson",
}
REVIEW_INPUT_ROLES = tuple(
    role
    for role in INPUT_PATHS
    if role
    not in {
        "scientific_review",
        "norway_boundary",
        "denmark_boundary",
        "finland_boundary",
    }
)
INPUT_MAX_BYTES = {
    "raw_inventory": 256 * 1024 * 1024,
    "raw_summary": 1024 * 1024,
    "normalized_metadata": 1024 * 1024,
    "normalized_density": 1024 * 1024,
    "scientific_review": 256 * 1024,
    "membership_ledger": 256 * 1024 * 1024,
    "boundary_manifest": 64 * 1024,
    "sweden_boundary": 4 * 1024 * 1024,
    "norway_boundary": 4 * 1024 * 1024,
    "denmark_boundary": 4 * 1024 * 1024,
    "finland_boundary": 4 * 1024 * 1024,
}
AUTHORITY_TOTAL_MAX_BYTES = 532 * 1024 * 1024
_MISSING_CODES = {
    "normalized_density": "missing_density_surface",
    "membership_ledger": "missing_density_membership",
}


class RaaAuthorityInputError(ValueError):
    """A finite input refusal, preserving missing, budget and custody distinctions."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        """Retain machine-readable reasons without claiming source absence on drift."""
        super().__init__(", ".join(reasons))
        self.reason_codes = reasons


class RaaAuthorityInputs:
    """Seal eleven literal inputs before reading any bounded source body."""

    def __init__(self, root: Path) -> None:
        """Define one operation, not a reusable admission cache."""
        self.root = Path(root).absolute()
        self._stack = ExitStack()
        self._trees: dict[str, BoundedInputTree] = {}
        self._buffers: dict[str, bytes] = {}
        self._receipts: dict[str, dict[str, object]] = {}
        self._entered = False
        self._active = False

    def _preflight(self) -> None:
        missing: list[str] = []
        total = 0
        for role, relative in INPUT_PATHS.items():
            try:
                node = (self.root / relative).lstat()
            except FileNotFoundError:
                missing.append(_MISSING_CODES.get(role, f"missing_{role}"))
                continue
            if not stat.S_ISREG(node.st_mode) or node.st_nlink != 1:
                raise RaaAuthorityInputError(("invalid_authority_input_custody",))
            total += node.st_size
            if (
                node.st_size > INPUT_MAX_BYTES[role]
                or total > AUTHORITY_TOTAL_MAX_BYTES
            ):
                raise RaaAuthorityInputError(
                    ("authority_input_resource_budget_exceeded",)
                )
        if missing:
            raise RaaAuthorityInputError(tuple(missing))

    def __enter__(self) -> RaaAuthorityInputs:
        """Inventory every slot and retain all seals before the first byte read."""
        if self._entered:
            raise ValueError("RAÄ authority inputs belong to one operation")
        self._entered = True
        self._preflight()
        try:
            for role, relative in INPUT_PATHS.items():
                path = self.root / relative
                self._trees[role] = self._stack.enter_context(
                    BoundedInputTree(
                        path.parent,
                        max_bytes=INPUT_MAX_BYTES[role],
                        max_files=1,
                        selected=path.name,
                    )
                )
            if (
                sum(
                    tree.files[(self.root / INPUT_PATHS[role]).name][4]
                    for role, tree in self._trees.items()
                )
                > AUTHORITY_TOTAL_MAX_BYTES
            ):
                raise RaaAuthorityInputError(
                    ("authority_input_resource_budget_exceeded",)
                )
            for tree in self._trees.values():
                tree.check()
        except RaaAuthorityInputError:
            self._stack.close()
            raise
        except (OSError, ValueError) as error:
            self._stack.close()
            raise RaaAuthorityInputError(
                ("invalid_authority_input_custody",)
            ) from error
        except BaseException:
            self._stack.close()
            raise
        self._active = True
        return self

    def read(self, role: str) -> bytes:
        """Read one exact sealed buffer, rejecting unknown roles before path access."""
        if not self._active or role not in self._trees:
            raise ValueError("RAÄ authority input role is outside its active operation")
        if role not in self._buffers:
            try:
                raw = self._trees[role].read(
                    self.root / INPUT_PATHS[role], max_bytes=INPUT_MAX_BYTES[role]
                )
            except (OSError, ValueError) as error:
                raise RaaAuthorityInputError(("authority_input_changed",)) from error
            self._buffers[role] = raw
            self._receipts[role] = {
                "path": INPUT_PATHS[role],
                "sha256": sha256(raw).hexdigest(),
                "byte_count": len(raw),
            }
        return self._buffers[role]

    def load_object(self, role: str) -> dict[str, object]:
        """Strictly decode the exact buffer used by this operation's byte receipt."""
        return decode_source_object(self.read(role).decode("utf-8"))

    def receipt(self, role: str) -> dict[str, object]:
        """Return the literal path, digest and byte count of the captured buffer."""
        self.read(role)
        return dict(self._receipts[role])

    def boundary_reader(self, path: Path) -> bytes:
        """Supply captured bytes only for this profile's five boundary inputs."""
        for role, relative in INPUT_PATHS.items():
            if (role.endswith("_boundary") or role == "boundary_manifest") and (
                Path(path).absolute() == self.root / relative
            ):
                return self.read(role)
        raise ValueError("RAÄ boundary reader path is outside its literal profile")

    def validate(self) -> None:
        """Recheck all names and content pins before a decision can be admitted."""
        if not self._active:
            raise ValueError("RAÄ authority input operation is not active")
        try:
            for tree in self._trees.values():
                tree.check()
            for tree in self._trees.values():
                tree.validate()
            for tree in self._trees.values():
                tree.check()
        except (OSError, ValueError) as error:
            raise RaaAuthorityInputError(("authority_input_changed",)) from error

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close every held descriptor on success or refusal."""
        self._active = False
        self._stack.close()
