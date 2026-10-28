"""Authenticate serialized spatial predictions and their consumed source state."""

from __future__ import annotations

import hashlib
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any

from .inputs import canonical, decode, require


def file_sha(path: Path) -> str:
    """Hash a source without duplicating its large payload in memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def code_state(repository: Path) -> dict[str, Any]:
    """Bind maintained Python bytes, HEAD and index across an owned run."""
    names = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--", "packages"], cwd=repository
        )
        .decode()
        .split("\0")
    )
    paths = [repository / name for name in names if name.endswith(".py")]
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    return {
        "head": head,
        "index_sha256": file_sha(repository / ".git/index"),
        "python_files": {
            str(path.relative_to(repository)): file_sha(path) for path in paths
        },
    }


def check_sources(repository: Path, archive: Path, packet: dict[str, Any]) -> None:
    """Recheck all exact source identities, including unopened outcome bytes."""
    for pin in packet["sources"]:
        if pin["storage"] == "archive_object":
            path = archive / "objects" / pin["sha256"][:2] / pin["sha256"]
        else:
            require(pin["storage"] == "repository", "Unknown source storage")
            relative = Path(pin["path"])
            require(
                not relative.is_absolute() and ".." not in relative.parts,
                "Relative source required",
            )
            path = repository / relative
        require(
            path.is_file()
            and not any(parent.is_symlink() for parent in (path, *path.parents))
            and path.stat().st_size == pin["bytes"]
            and file_sha(path) == pin["sha256"],
            "Consumed scientific source changed",
        )


def write(directory: Path, name: str, value: Any, maximum: int) -> dict[str, Any]:
    """Write one exclusive canonical JSON member below the declared byte bound."""
    require(
        Path(name).name == name and name not in {"", ".", ".."},
        "Direct member name required",
    )
    raw = canonical(value) + b"\n"
    require(len(raw) <= maximum, "Scientific member exceeds output ceiling")
    with (directory / name).open("xb") as stream:
        stream.write(raw)
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def reopen(directory: Path, pin: dict[str, Any]) -> Any:
    """Authenticate the closed bytes before allowing their scientific consumer."""
    name = pin["path"]
    require(
        type(name) is str and Path(name).name == name and name not in {"", ".", ".."},
        "Direct member name required",
    )
    path = directory / name
    require(
        path.is_file() and not path.is_symlink(), "Ordinary scientific member required"
    )
    raw = path.read_bytes()
    require(
        len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
        "Serialized scientific member changed",
    )
    return decode(raw)


def resources(
    started: float, output: Path, limits: dict[str, Any], *, observer: bool = False
) -> dict[str, Any]:
    """Enforce the prospective wall, peak-memory and aggregate-output ceilings."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    facts = {
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
        "output_bytes": sum(
            path.stat().st_size for path in output.iterdir() if path.is_file()
        ),
    }
    require(
        facts["elapsed_seconds"]
        <= limits["observer_wall_seconds" if observer else "producer_wall_seconds"]
        and facts["peak_rss_bytes"] <= limits["max_rss_bytes"]
        and facts["output_bytes"] <= limits["max_output_bytes"],
        "Spatial study exceeded its prospective resource bound",
    )
    return facts
