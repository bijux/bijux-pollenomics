"""Confined serialized products and in-memory source/runtime guards."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any

import numpy as np


def _git_state(repository: Path) -> tuple[str, bytes]:
    return (
        subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip(),
        (repository / ".git/index").read_bytes(),
    )


class StudyError(ValueError):
    """A source, numerical, serialization or resource contract failed."""


def _plain(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, Path):
        return str(value)
    return value


def _payload(value: Any) -> bytes:
    return (json.dumps(_plain(value), indent=2, allow_nan=False) + "\n").encode()


def _pin(path: Path, repository: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.resolve() != path:
        raise StudyError("Ordinary canonical source/product file required")
    raw = path.read_bytes()
    return {
        "path": path.relative_to(repository).as_posix(),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _write(path: Path, value: Any, maximum: int) -> dict[str, Any]:
    raw = _payload(value)
    if len(raw) > maximum:
        raise StudyError("Scientific product exceeds the declared byte ceiling")
    with path.open("xb") as stream:
        stream.write(raw)
    return {
        "path": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _read_product(directory: Path, pin: dict[str, Any]) -> dict[str, Any]:
    name = pin["path"]
    if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."}:
        raise StudyError("A product member must be a direct filename")
    path = directory / name
    if path.is_symlink() or not path.is_file():
        raise StudyError("Ordinary serialized product required")
    raw = path.read_bytes()
    if len(raw) != pin["bytes"] or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise StudyError("Serialized scientific product changed")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise StudyError("Scientific product must be an object")
    return value


def _source_check(repository: Path, packet: dict[str, Any]) -> None:
    for expected in packet["source_files"]:
        relative = Path(expected["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise StudyError("Repository-relative scientific source required")
        path = repository / relative
        if path.stat().st_size != expected["bytes"]:
            raise StudyError("Consumed scientific source size changed")
        actual = _pin(path, repository)
        if any(actual[key] != expected[key] for key in ("path", "bytes", "sha256")):
            raise StudyError("Consumed scientific source changed")


def _loaded_code(repository: Path) -> dict[Path, bytes]:
    paths = set()
    for module in tuple(sys.modules.values()):
        name = getattr(module, "__file__", None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(repository / "packages") and path.suffix == ".py":
                paths.add(path)
    return {path: path.read_bytes() for path in paths}


def _resource_check(
    started: float,
    output: Path,
    limits: dict[str, Any],
    *,
    wall_key: str = "producer_wall_seconds",
) -> dict[str, Any]:
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_bytes = rss if sys.platform == "darwin" else rss * 1024
    size = sum(path.stat().st_size for path in output.iterdir() if path.is_file())
    if (
        elapsed > limits[wall_key]
        or rss_bytes > limits["max_rss_bytes"]
        or size > limits["max_output_bytes"]
    ):
        raise StudyError("Conditional study exceeded its declared resource bound")
    return {
        "elapsed_seconds": elapsed,
        "peak_rss_bytes": rss_bytes,
        "product_bytes": size,
    }
