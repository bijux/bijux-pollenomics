"""Bind a calculation to unchanged installed code and resource bytes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
from typing import cast

from ....core import owned_tree
from ..engine.discovery import EngineBinding
from ..engine.errors import LRARefusal


def file_inventory(root: Path) -> dict[str, str]:
    """Hash files including resources, excluding only interpreter bytecode caches."""
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


@dataclass(frozen=True)
class CodeIdentity:
    """An immutable pre-computation inventory of engine and host adapter files."""

    canonical_json: str

    def payload(self) -> dict[str, dict[str, str]]:
        return cast(dict[str, dict[str, str]], json.loads(self.canonical_json))


def capture_code_identity(binding: EngineBinding) -> CodeIdentity:
    """Refuse an unlocatable engine rather than recording an empty code identity."""
    filename = binding.api.__file__
    if filename is None or not Path(filename).is_file():
        raise LRARefusal(
            "engine_identity_unavailable", "Installed API file is unavailable"
        )
    payload = {
        "engine_files": file_inventory(Path(filename).parent),
        "host_adapter_files": file_inventory(Path(__file__).parents[1]),
        "host_publication_files": {
            "core/owned_tree.py": hashlib.sha256(
                Path(owned_tree.__file__).read_bytes()
            ).hexdigest()
        },
        "runtime_environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            **{
                name: metadata.version(name)
                for name in ("bijux-pollenomics", "numpy", "scipy", "pandas")
            },
            **{
                name: os.environ.get(name, "unset")
                for name in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                )
            },
        },
    }
    return CodeIdentity(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def verify_code_identity(binding: EngineBinding, expected: CodeIdentity) -> None:
    if capture_code_identity(binding) != expected:
        raise LRARefusal(
            "lra_code_changed_during_run",
            "Engine or host adapter code/resources changed during computation or serialization",
        )
