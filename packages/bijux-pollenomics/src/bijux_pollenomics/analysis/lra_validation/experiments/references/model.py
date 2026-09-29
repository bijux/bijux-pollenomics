"""Validated relative paths and exact byte identities for experiment inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
import re

from ...contracts import ValidationRefusal


def object_mapping(value: object, name: str) -> dict[str, object]:
    """Admit a JSON object without manufacturing or coercing keys."""
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValidationRefusal("invalid_experiment", f"{name} must be an object")
    return dict(value)


@dataclass(frozen=True)
class InputReference:
    """A relative file identity whose contents can be opened after fold admission."""

    path: str
    sha256: str

    @classmethod
    def parse(cls, value: object, name: str) -> InputReference:
        row = object_mapping(value, name)
        if set(row) != {"path", "sha256"}:
            raise ValidationRefusal("invalid_experiment_reference", name)
        path = row["path"]
        digest = row["sha256"]
        if (
            not isinstance(path, str)
            or not path
            or "\\" in path
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValidationRefusal("invalid_experiment_reference", name)
        return cls(path, digest)
