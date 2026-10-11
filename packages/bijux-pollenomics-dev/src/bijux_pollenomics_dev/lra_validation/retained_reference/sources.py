"""Bind installed consumer origins and current calculation sources independently of R."""

from __future__ import annotations

import hashlib
from importlib import util
from pathlib import Path
import sys
from typing import Any

from bijux_pollenomics_dev.lra_validation.reference_replay import _replay_source_hashes

ROOTS = {
    "bijux_pollenomics_dev": "packages/bijux-pollenomics-dev/src",
    "bijux_pollenomics": "packages/bijux-pollenomics/src",
    "bijux_pollenomics_lra": "packages/bijux-pollenomics-lra/src",
    "pollenomics": "packages/pollenomics/src",
}


def _digest(path: Path) -> str:
    if (
        any(member.is_symlink() for member in (path, *path.parents))
        or not path.is_file()
    ):
        raise ValueError("Current consumer source is not regular")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture_sources(repository: Path) -> dict[str, Any]:
    """Keep canonical replay keys separate from the new consumer's physical closure."""
    repository = repository.resolve(strict=True)
    canonical = _replay_source_hashes(repository)
    installed = Path(__file__).absolute().parent
    environment = Path(sys.prefix).resolve(strict=True)
    if (
        not installed.resolve(strict=True).is_relative_to(environment)
        or "site-packages" not in installed.parts
    ):
        raise ValueError("Retained consumer must originate in installed site-packages")
    relative = Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
        "lra_validation/retained_reference"
    )
    source = repository / relative
    source_names = {
        path.name for path in source.iterdir() if path.suffix in {".py", ".json"}
    }
    installed_names = {
        path.name for path in installed.iterdir() if path.suffix in {".py", ".json"}
    }
    if not source_names or source_names != installed_names:
        raise ValueError("Installed retained consumer member population differs")
    closure = dict(canonical)
    origins = {}
    for name in sorted(source_names):
        expected = _digest(source / name)
        if _digest(installed / name) != expected:
            raise ValueError("Installed retained consumer bytes differ: " + name)
        closure[(relative / name).as_posix()] = expected
        origins[(relative / name).as_posix()] = str((installed / name).resolve())
    for name, module in tuple(sys.modules.items()):
        package = name.split(".")[0]
        if package not in ROOTS and package != "lra_oracle":
            continue
        supplied = getattr(module, "__file__", None)
        if not isinstance(supplied, str):
            raise ValueError(
                "Current first-party module lacks physical source: " + name
            )
        supplied_path = Path(supplied).absolute()
        _digest(supplied_path)
        origin = supplied_path.resolve(strict=True)
        if package == "lra_oracle":
            reference = repository / "packages/bijux-pollenomics-lra/tests/reference"
            if not origin.is_relative_to(reference):
                raise ValueError("Current oracle module escaped canonical source")
            path = origin.relative_to(repository).as_posix()
        else:
            if (
                not origin.is_relative_to(environment)
                or "site-packages" not in origin.parts
            ):
                raise ValueError(
                    "Current first-party import escaped installed source: " + name
                )
            suffix = origin.parts[origin.parts.index("site-packages") + 1 :]
            path = (Path(ROOTS[package]) / Path(*suffix)).as_posix()
        expected = _digest(repository / path)
        if _digest(origin) != expected:
            raise ValueError("Current installed first-party bytes differ: " + name)
        closure[path] = expected
        origins[path] = str(origin)
    resource_package = "bijux_pollenomics_lra"
    resource_spec = util.find_spec(resource_package)
    if resource_spec is None or resource_spec.origin is None:
        raise ValueError("Installed LRA resource package is absent")
    _digest(Path(resource_spec.origin).absolute())
    resource_root = Path(resource_spec.origin).resolve(strict=True).parent
    if (
        not resource_root.is_relative_to(environment)
        or "site-packages" not in resource_root.parts
    ):
        raise ValueError("Installed LRA resources escaped installed source")
    resource_relative = Path(ROOTS[resource_package]) / resource_package
    source_resource_root = repository / resource_relative
    source_resources = {
        path.relative_to(source_resource_root)
        for path in source_resource_root.rglob("*")
        if path.suffix in {".npz", ".json"}
    }
    installed_resources = {
        path.relative_to(resource_root)
        for path in resource_root.rglob("*")
        if path.suffix in {".npz", ".json"}
    }
    if source_resources != installed_resources:
        raise ValueError("Installed LRA resource member population differs")
    for resource in sorted(source_resources):
        key = (resource_relative / resource).as_posix()
        expected = _digest(source_resource_root / resource)
        if (
            canonical.get(key) != expected
            or _digest(resource_root / resource) != expected
        ):
            raise ValueError("Installed LRA resource bytes differ: " + key)
        origins[key] = str((resource_root / resource).resolve(strict=True))
    return {
        "canonical_replay_inputs_sha256": canonical,
        "consumer_inputs_sha256": dict(sorted(closure.items())),
        "physical_origins": dict(sorted(origins.items())),
    }


def require_unchanged_sources(
    repository: Path, captured: dict[str, Any]
) -> dict[str, Any]:
    """Permit newly observed imports only while their canonical source was already bound."""
    current = capture_sources(repository)
    if (
        current["canonical_replay_inputs_sha256"]
        != captured["canonical_replay_inputs_sha256"]
    ):
        raise ValueError("Current canonical calculation source changed")
    for path, expected in captured["consumer_inputs_sha256"].items():
        if current["consumer_inputs_sha256"].get(path) != expected:
            raise ValueError("Current consumer source changed: " + path)
    for path, expected in current["consumer_inputs_sha256"].items():
        if captured["consumer_inputs_sha256"].get(path) != expected:
            raise ValueError("Current consumer imported an unbound source: " + path)
    for path, origin in captured["physical_origins"].items():
        if current["physical_origins"].get(path) != origin:
            raise ValueError("Current consumer physical origin changed: " + path)
    return current
