"""Freeze exact country-reader branches, global lookups and published comparands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from source_inputs import pin


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def physical(path: Path, kind: str | None = None) -> str:
    require(
        path.is_absolute() and ".." not in path.parts,
        "Normalized absolute input role required",
    )
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "Input role ancestor alias refused",
    )
    value = (
        "file"
        if path.is_file()
        else "directory"
        if path.is_dir()
        else "absent"
        if not path.exists()
        else "special"
    )
    require(
        value != "special" and (kind is None or value == kind),
        "Input role physical kind differs",
    )
    if value == "file":
        require(path.stat().st_nlink == 1, "Hardlinked input role refused")
    return value


def discover(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    """Observe declared is_file/is_dir and exact two source-owned glob memberships."""
    files: set[str] = set()
    statuses: dict[str, str] = {}
    required = set(declaration["required_data"])
    roles = [*declaration["required_data"], *declaration["optional_data"]]
    require(len(roles) == len(set(roles)), "Duplicate named data role")
    for name in roles:
        value = physical(root / name)
        require(value in {"file", "absent"}, "A data file role became a directory")
        require(name not in required or value == "file", "Required source input absent")
        statuses[name] = value
        if value == "file":
            files.add(name)
    directories = {}
    for name in declaration["species_roots"]:
        kind = physical(root / name)
        require(
            kind in {"directory", "absent"}, "Species directory role is not a directory"
        )
        directories[name] = kind
    globs = {}
    for role, pattern in declaration["glob_roles"].items():
        members = []
        for path in root.glob(pattern):
            members.append(path.relative_to(root).as_posix())
            require(
                len(members) <= 512,
                "Bounded country glob membership exceeded before hashing",
            )
        members.sort()
        require(len(members) == len(set(members)), "Duplicate glob membership")
        for name in members:
            physical(root / name, "file")
        if role == "human_release_annotations":
            require(bool(members), "AADR annotation release is empty")
        files.update(members)
        globs[role] = members
    published = declaration["published_root"]
    for role in declaration["published_roles"]:
        name = published + "/" + role["relative_path"]
        kind = physical(root / name)
        require(kind in {"file", "absent"}, "Published comparand role changed kind")
        if role["relative_path"] in declaration["published_required"]:
            require(kind == "file", "Original upstream/scientific comparand absent")
        statuses[name] = kind
        if kind == "file":
            files.add(name)
    history = published + "/land-use-replay/receipt.json"
    physical(root / history, "file")
    statuses[history] = "file"
    files.add(history)
    assets = root / published / "_map_assets"
    assets_kind = physical(assets)
    require(
        assets_kind in {"directory", "absent"}, "Published asset root has wrong kind"
    )
    asset_directories = []
    if assets_kind == "directory":
        for path in sorted(assets.rglob("*")):
            kind = physical(path)
            require(kind in {"file", "directory"}, "Published asset missing/special")
            name = path.relative_to(root).as_posix()
            if kind == "file":
                files.add(name)
                require(
                    len(files) <= 2048,
                    "Bounded country input membership exceeded before hashing",
                )
            else:
                asset_directories.append(name)
    require(
        len(files) <= 2048 and len(asset_directories) <= 1024,
        "Bounded country input or asset directory count exceeded",
    )
    return {
        "files": sorted(files),
        "named_file_presence": statuses,
        "species_directory_presence": directories,
        "glob_membership": globs,
        "published_assets_kind": assets_kind,
        "published_asset_directories": asset_directories,
    }


def freeze(
    root: Path, declaration: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selection = discover(root, declaration)
    selection["original_native_glob_orders"] = native_orders(root, declaration)
    selection["source_input_metadata"] = [
        {
            "path": name,
            "bytes": (root / name).stat().st_size,
            "mtime_ns": (root / name).stat().st_mtime_ns,
        }
        for name in selection["files"]
    ]
    require(
        sum(row["bytes"] for row in selection["source_input_metadata"])
        <= declaration["maximum_input_bytes"],
        "Prospective input ceiling exceeded before body hash; source review required before changing budget",
    )
    for row in selection["source_input_metadata"]:
        if Path(row["path"]).suffix in {".json", ".geojson"}:
            require(
                row["bytes"] <= declaration["maximum_single_JSON_bytes"],
                "Single JSON input ceiling exceeded before body hash",
            )
    rows = [pin(root / name) for name in selection["files"]]
    require(
        [row["bytes"] for row in rows]
        == [row["bytes"] for row in selection["source_input_metadata"]],
        "Input size changed while freezing hashes",
    )
    verify_selection(root, declaration, selection)
    return selection, rows


def verify_selection(
    root: Path, declaration: dict[str, Any], selection: dict[str, Any]
) -> None:
    expected = {
        key: value
        for key, value in selection.items()
        if key not in {"source_input_metadata", "original_native_glob_orders"}
    }
    require(
        discover(root, declaration) == expected,
        "Country input presence/glob/asset namespace changed",
    )
    for row in selection["source_input_metadata"]:
        path = root / row["path"]
        physical(path, "file")
        require(
            path.stat().st_size == row["bytes"]
            and path.stat().st_mtime_ns == row["mtime_ns"],
            "Input size/mtime changed",
        )


def native_orders(root: Path, declaration: dict[str, Any]) -> dict[str, list[str]]:
    result = {}
    for role, pattern in declaration["glob_roles"].items():
        rows = []
        for path in root.glob(pattern):
            physical(path, "file")
            rows.append(path.relative_to(root).as_posix())
            require(len(rows) <= 512, "Bounded native input glob order exceeded")
        result[role] = rows
    return result
