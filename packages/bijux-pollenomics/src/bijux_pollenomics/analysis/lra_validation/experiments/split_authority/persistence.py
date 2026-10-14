"""Persist and bind outcome-free experiment splits before numerical work."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from pathlib import Path

from ...contracts import Fold, ValidationRefusal, canonical_json, manifest_sha256


@dataclass(frozen=True)
class PrefitSplitAuthority:
    """Exact split bytes retained before fitting and checked before publication."""

    directory: Path
    members: tuple[tuple[str, bytes], ...]
    folds_sha256: str

    def verify(self) -> None:
        """Refuse removed, replaced or changed split authority without rewriting it."""
        try:
            if self.directory.is_symlink() or not self.directory.is_dir():
                raise ValueError("Split directory is not a regular owned directory")
            for name, expected in self.members:
                path = self.directory / name
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or path.read_bytes() != expected
                ):
                    raise ValueError("Frozen experiment split bytes differ")
        except (OSError, ValueError) as error:
            raise ValidationRefusal("experiment_split_changed", str(error)) from error


def freeze_experiment_split(
    directory: Path,
    folds: tuple[Fold, ...],
    *,
    manifest: Mapping[str, object] | None = None,
) -> PrefitSplitAuthority:
    """Write existing split members exclusively before any reconstruction or fit.

    The producer supplies its outcome-free canonical folds. Block-local profiles
    also retain their existing full record/alias manifest. No labels, thresholds
    or scientific admission defaults are inferred at this persistence boundary.
    """
    if directory.is_symlink() or not directory.is_dir():
        raise ValidationRefusal(
            "invalid_experiment_split", "Regular owned split directory required"
        )
    if not folds or len({fold.fold_id for fold in folds}) != len(folds):
        raise ValidationRefusal(
            "invalid_experiment_split", "Nonempty unique folds required"
        )
    rows = [fold.as_dict() for fold in folds]
    members = [("folds.json", (canonical_json(rows) + "\n").encode())]
    if manifest is not None:
        members.append(
            ("split_manifest.json", (canonical_json(dict(manifest)) + "\n").encode())
        )
    for name, _ in members:
        path = directory / name
        if path.exists() or path.is_symlink():
            raise ValidationRefusal("experiment_split_exists", str(path))
    for name, content in members:
        with (directory / name).open("xb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    authority = PrefitSplitAuthority(directory, tuple(members), manifest_sha256(rows))
    authority.verify()
    return authority
