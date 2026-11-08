"""Source stability and bounded output shared by the producer and saved-leaf reader."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import importlib.metadata as metadata
import importlib.util
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any, cast

from ..verification.contracts import RESOURCE_LIMITS
from .inputs import FrozenInputs, read_inputs, require


@dataclass(frozen=True)
class SourceGuard:
    """Bind the exact mathematical/import closure and worktree index, not a registry."""

    head: str
    index_sha256: str
    files: tuple[tuple[str, str], ...]


def source_guard(root: Path, inputs: FrozenInputs) -> SourceGuard:
    """Require committed consumed source and retain exact input identities."""
    base = Path(__file__).resolve().parent.parent
    files = [*base.rglob("*.py"), base.parent / "radial_envelope.py", root / "uv.lock"]
    files.extend(
        root / name for name in inputs.identities if not name.startswith("artifacts/")
    )
    names = sorted({path.resolve().relative_to(root).as_posix() for path in files})
    git = ["git", "--no-optional-locks", "--no-replace-objects", "-C", str(root)]
    require(
        subprocess.check_output(
            [*git, "rev-parse", "--show-toplevel"], text=True, timeout=30
        ).strip()
        == str(root),
        "Wrong scientific checkout root",
    )
    head = subprocess.check_output(
        [*git, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *names],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", head, "--", *names],
        check=True,
        capture_output=True,
        timeout=30,
    )
    index = Path(
        subprocess.check_output(
            [*git, "rev-parse", "--git-path", "index"], text=True, timeout=30
        ).strip()
    )
    if not index.is_absolute():
        index = root / index
    return SourceGuard(
        head,
        hashlib.sha256(index.read_bytes()).hexdigest(),
        tuple(
            (name, hashlib.sha256((root / name).read_bytes()).hexdigest())
            for name in names
        ),
    )


def environment(root: Path) -> dict[str, Any]:
    """Separate actual installed metadata from explicit owned source imports."""
    origins = {}
    for name, distribution in (
        ("bijux_pollenomics", "bijux-pollenomics"),
        ("bijux_pollenomics_dev", "bijux-pollenomics-dev"),
        ("bijux_pollenomics_lra", "bijux-pollenomics-lra"),
        ("pollenomics", "pollenomics"),
    ):
        expected = root / "packages" / distribution / "src"
        spec = importlib.util.find_spec(name)
        require(
            spec is not None
            and spec.origin is not None
            and Path(spec.origin).resolve().is_relative_to(expected),
            "Foreign first-party source origin",
        )
        module = importlib.import_module(name)
        require(
            Path(cast(str, module.__file__)).resolve().is_relative_to(expected),
            "Foreign imported first-party source",
        )
        origins[name] = str(Path(cast(str, module.__file__)).relative_to(root))
    versions = {
        name: metadata.version(name)
        for name in (
            "bijux-pollenomics",
            "bijux-pollenomics-dev",
            "bijux-pollenomics-lra",
            "pollenomics",
            "numpy",
            "scipy",
            "pandas",
            "setuptools",
            "wheel",
        )
    }
    return {
        "python": sys.version,
        "owned_import_origins": origins,
        "ambient_distribution_versions": versions,
        "native_prefix_recaptured": False,
    }


def fresh_output(root: Path, output: Path) -> Path:
    """Confine a new process-owned output directory without overwriting predecessors."""
    require(
        output.resolve() == output
        and output.is_relative_to(root / "artifacts")
        and output != root / "artifacts"
        and not output.exists()
        and not any(path.is_symlink() for path in (output, *output.parents)),
        "Fresh owned artifact output required",
    )
    output.mkdir(parents=True)
    return output


def write_json(output: Path, name: str, value: object) -> bytes:
    """Reserve space for closure and outside process logs inside the original 5MB."""
    require(
        Path(name).name == name and not (output / name).exists(),
        "Output member already exists or escapes owner",
    )
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    total = sum(path.stat().st_size for path in output.iterdir() if path.is_file())
    require(total + len(raw) <= 4_850_000, "Original product byte allocation exceeded")
    (output / name).write_bytes(raw)
    return raw


def peak_rss() -> int:
    """Normalize the platform's observed peak RSS without implying an OS quota."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def check_terminal(
    root: Path,
    protocol: Path,
    before: SourceGuard,
    inputs: FrozenInputs,
    started: float,
    output: Path,
) -> dict[str, Any]:
    """Fail closed on source/input changes or any original terminal resource excess."""
    after_inputs = read_inputs(root, protocol)
    require(
        after_inputs.identities == inputs.identities
        and source_guard(root, after_inputs) == before,
        "Consumed law, input or source changed",
    )
    elapsed = time.monotonic() - started
    rss = peak_rss()
    output_bytes = sum(
        path.stat().st_size for path in output.iterdir() if path.is_file()
    )
    require(
        elapsed < RESOURCE_LIMITS["wall_seconds"],
        "Original process wall ceiling exceeded",
    )
    require(
        rss <= RESOURCE_LIMITS["peak_rss_bytes_posthoc"],
        "Original RSS ceiling exceeded",
    )
    require(
        output_bytes <= RESOURCE_LIMITS["all_output_bytes"],
        "Original output ceiling exceeded",
    )
    return {
        "elapsed_seconds": elapsed,
        "peak_rss_bytes": rss,
        "product_bytes_before_terminal_receipt": output_bytes,
        "source_and_index_unchanged": True,
        "inputs_unchanged": True,
        "rss_policy": "observed peak so far inside the running child; final external peak-RSS/output postcheck required, no OS memory quota asserted",
        "process_wall_policy": "internal partial-process check; external 180-second whole-process supervisor and final RSS/all-output postcheck required; 160-second cooperative integration clock",
    }
