"""Retain original cache identities while copying only complete tracked Neotoma consumer execution sources."""

from __future__ import annotations

from pathlib import Path
import re
import tomllib
from typing import Any

from source_inputs import incoming_rows, pin


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def cache_bytecode(relative: Path, tracked: set[str]) -> bool:
    if relative.suffix not in {".pyc", ".pyo"}:
        return False
    if relative.parent.name == "__pycache__":
        return (
            re.fullmatch(
                r".+\.(?:cpython|pypy)-[0-9]+(?:-pytest-[0-9]+\.[0-9]+\.[0-9]+)?(?:\.opt-[0-9]+)?\.py[co]",
                relative.name,
            )
            is not None
        )
    return relative.with_suffix(".py").as_posix() in tracked


def project(
    root: Path,
    snapshot: dict[str, Any],
    original_rows: list[dict[str, Any]],
    tracked_paths: set[str],
    metadata_omissions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    rows = incoming_rows(original_rows)
    metadata_omissions = metadata_omissions or {}
    require(
        snapshot["root"] == str(root) and snapshot["excluded"] == [],
        "Complete original source namespace required",
    )
    entries = snapshot["entries"]
    require(
        all(value["kind"] in {"file", "directory"} for value in entries.values()),
        "Original aliases/specials refused",
    )
    original_files = {
        str(root / name) for name, value in entries.items() if value["kind"] == "file"
    }
    require(set(rows) == original_files, "Original source ledger misses regular files")
    require(
        tracked_paths <= original_files,
        "Tracked source/resource missing from original namespace",
    )
    tracked_relative = {
        Path(name).relative_to(root).as_posix() for name in tracked_paths
    }
    require(
        set(metadata_omissions) <= original_files
        and not set(metadata_omissions) & tracked_paths,
        "Exact generated omission must exist and remain untracked",
    )
    selected = []
    omitted = []
    omitted_metadata = []
    for name, row in sorted(rows.items()):
        relative = Path(name).relative_to(root)
        if name in tracked_paths:
            require(
                relative.suffix not in {".pyc", ".pyo"},
                "Tracked bytecode is not an execution source",
            )
            selected.append(row)
        elif name in metadata_omissions:
            require(
                row == metadata_omissions[name],
                "Exact generated metadata bytes changed",
            )
            omitted_metadata.append(
                {
                    **row,
                    "role": "omitted_configured_generated_version_metadata_identity_only",
                    "executed_or_copied": False,
                    "source_equivalence_claimed": False,
                }
            )
        else:
            require(
                cache_bytecode(relative, tracked_relative),
                "Untracked non-cache source/resource refused",
            )
            omitted.append(
                {
                    **row,
                    "role": "omitted_unselected_cache_bytecode_identity_only",
                    "executed_or_copied": False,
                    "source_equivalence_claimed": False,
                }
            )
    projected = {}
    removed_dirs = []
    for name, value in entries.items():
        if value["kind"] == "file":
            if str(root / name) in tracked_paths:
                projected[name] = value
        elif "__pycache__" not in Path(name).parts or any(
            Path(selected_name).is_relative_to(name)
            for selected_name in tracked_relative
        ):
            projected[name] = value
        else:
            removed_dirs.append(name)
    require(
        {name for name, row in projected.items() if row["kind"] == "file"}
        == tracked_relative,
        "Projected tracked source membership differs",
    )
    return {
        "selected_rows": selected,
        "omitted_bytecode_rows": omitted,
        "omitted_generated_metadata_rows": omitted_metadata,
        "projected_namespace": {
            "root": str(root),
            "excluded": [],
            "entries": projected,
        },
        "omitted_cache_directories": sorted(removed_dirs),
        "original_regular_file_count": len(rows),
    }


def authorize_metadata(
    root: Path, descriptor: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    relative = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
    )
    configured = "src/bijux_pollenomics_lra/_build_version.py"
    require(
        descriptor["relative_module"] == relative
        and descriptor["configured_version_file"] == configured
        and descriptor["producer_owner"] == "tool.hatch.build.hooks.vcs.version-file",
        "Only the declared hatch-vcs generated version module can be omitted",
    )
    require(
        descriptor["copied_or_executed"] is False
        and descriptor["model_or_version_equivalence_authority"] is False,
        "Generated metadata is not numerical/version authority",
    )
    module = root / relative
    require(
        not any(node.is_symlink() for node in (module, *module.parents))
        and pin(module) == descriptor["module_pin"],
        "Original configured metadata pin differs",
    )
    wanted = {
        str(root / "packages/bijux-pollenomics-lra" / name)
        for name in ["pyproject.toml", ".gitignore"]
    }
    rows = incoming_rows(descriptor["configuration"])
    require(
        set(rows) == wanted, "Exact version-producer configuration closure required"
    )
    for name, row in rows.items():
        path = Path(name)
        require(
            not any(node.is_symlink() for node in (path, *path.parents))
            and pin(path) == row,
            "Generated version ownership configuration changed",
        )
    configuration = tomllib.loads(
        (root / "packages/bijux-pollenomics-lra/pyproject.toml").read_text()
    )
    require(
        configuration["build-system"]["build-backend"] == "hatchling.build"
        and configuration["tool"]["hatch"]["version"]["source"] == "vcs"
        and any(
            item.startswith("hatch-vcs")
            for item in configuration["build-system"]["requires"]
        ),
        "Configured generated version producer ownership differs",
    )
    require(
        configuration["tool"]["hatch"]["build"]["hooks"]["vcs"]["version-file"]
        == configured,
        "Configured version producer differs",
    )
    ignore = (
        (root / "packages/bijux-pollenomics-lra/.gitignore").read_text().splitlines()
    )
    require(configured in ignore, "Exact generated-version ignore rule missing")
    return {str(module): descriptor["module_pin"]}
