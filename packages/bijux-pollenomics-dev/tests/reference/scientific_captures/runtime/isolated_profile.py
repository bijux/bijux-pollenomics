"""Isolated standard-library profile, exact aliases and recursive native dependencies."""

from __future__ import annotations

import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from typing import Any

from contracts import BASE, BASE_SHA, PREFIX, pin, require, sha

UNUSED = PREFIX / "lib/python3.11/site-packages"
UNUSED_LINK = "../../../../../../../../../lib/python3.11/site-packages"
UNUSED_TARGET = Path("/opt/homebrew/lib/python3.11/site-packages")
INSPECTOR = Path("/Library/Developer/CommandLineTools/usr/bin/otool-classic")
INSPECTOR_SHA = "ef0b500f6cb89910209839f66cab6100bb86defd7ebbfa2188a44ff5784a58b9"
FORBIDDEN_ENVIRONMENT = {
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "_PYTHON_HOST_PLATFORM",
    "__PYVENV_LAUNCHER__",
}

MAGIC = {
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
    b"\xca\xfe\xba\xbf",
    b"\xbf\xba\xfe\xca",
}


def alias(path: Path, root: Path) -> dict[str, Any]:
    target = path.resolve(strict=True)
    if path == UNUSED:
        require(
            os.readlink(path) == UNUSED_LINK and target == UNUSED_TARGET,
            "Unused site alias identity changed",
        )
        return {
            "path": str(path),
            "link": os.readlink(path),
            "target": str(target),
            "scope": "unused-site-packages-excluded",
        }
    require(
        target.is_relative_to(root),
        f"Undeclared alias escaped {root}: {path} -> {target}",
    )
    return {
        "path": str(path),
        "link": os.readlink(path),
        "target": str(target),
        "scope": "pinned-tree-alias",
    }


def tree(root: Path) -> tuple[set[Path], list[dict[str, Any]]]:
    require(
        root.is_dir() and root.resolve() == root,
        f"Physical runtime root required: {root}",
    )
    files: set[Path] = set()
    aliases = []
    for current, dirs, names in os.walk(root, followlinks=False):
        for name in list(dirs):
            path = Path(current) / name
            if path.is_symlink():
                aliases.append(alias(path, root))
                dirs.remove(name)
        for name in names:
            path = Path(current) / name
            if path.is_symlink():
                aliases.append(alias(path, root))
            else:
                require(path.is_file(), f"Nonregular runtime member: {path}")
                files.add(path)
    return files, sorted(aliases, key=lambda row: row["path"])


def check_aliases(rows: list[dict[str, Any]]) -> bool:
    return all(
        Path(r["path"]).is_symlink()
        and os.readlink(r["path"]) == r["link"]
        and str(Path(r["path"]).resolve(strict=True)) == r["target"]
        for r in rows
    )


def require_environment(environment: dict[str, str]) -> None:
    require(
        not any(
            key.startswith("DYLD_") or key in FORBIDDEN_ENVIRONMENT
            for key in environment
        ),
        "Undeclared loader/platform environment key",
    )


def absent_path(path: Path) -> bool:
    return not path.exists() and not path.is_symlink()


def tree_membership(root: Path) -> list[dict[str, str]]:
    require(
        root.is_dir() and root.resolve() == root, "Physical namespace root required"
    )
    rows = []
    for current, directories, names in os.walk(root, followlinks=False):
        for name in directories + names:
            path = Path(current) / name
            kind = (
                "alias"
                if path.is_symlink()
                else "directory"
                if path.is_dir()
                else "file"
                if path.is_file()
                else "special"
            )
            require(kind != "special", "Nonregular namespace member: " + str(path))
            rows.append({"path": path.relative_to(root).as_posix(), "kind": kind})
        directories[:] = [
            name for name in directories if not (Path(current) / name).is_symlink()
        ]
    return sorted(rows, key=lambda row: row["path"])


def validate_inspector(path: Path, wanted_sha: str) -> None:
    require(
        path.is_file() and not path.is_symlink() and sha(path) == wanted_sha,
        "Native inspector bytes differ",
    )
    with path.open("rb") as stream:
        header = stream.read(12)
    require(
        len(header) == 12 and header[:4] == b"\xcf\xfa\xed\xfe",
        "Native inspector must be a thin arm64 executable",
    )
    cpu, subtype = struct.unpack("<II", header[4:])
    require(
        cpu == 0x0100000C and subtype == 0,
        "Native inspector has no ordinary arm64 slice",
    )


def loader_commands(listing: str) -> tuple[list[str], set[str]]:
    rpaths: list[str] = []
    install_ids: set[str] = set()
    lines = listing.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "cmd LC_ID_DYLIB":
            install_ids.update(
                match.group(1)
                for candidate in lines[i + 1 : i + 5]
                if (match := re.match(r"\s*name (.+) \(offset \d+\)", candidate))
            )
        if line.strip() == "cmd LC_RPATH":
            rpaths.extend(
                match.group(1)
                for candidate in lines[i + 1 : i + 5]
                if (match := re.match(r"\s*path (.+) \(offset \d+\)", candidate))
            )
    return rpaths, install_ids


def dependency_load_names(output: str, binary: Path) -> list[str]:
    headers = {str(binary) + ":", str(binary) + " (architecture arm64):"}
    lines = output.splitlines()
    require(bool(lines) and lines[0] in headers, "Native dependency header differs")
    names = []
    for line in lines[1:]:
        if line in headers:
            continue
        match = re.fullmatch(r"\s+(.+) \(compatibility version [^)]*\)", line)
        require(match is not None, "Malformed or non-arm64 native dependency row")
        assert match is not None
        names.append(match.group(1))
    return names


def profile_guard() -> dict[str, Any]:
    require_environment(dict(os.environ))
    require(
        Path(sys.executable).absolute() == BASE and sha(BASE) == BASE_SHA,
        "Exact isolated base executable required",
    )
    require(
        sys.version_info[:3] == (3, 11, 13)
        and sys.prefix == sys.base_prefix == str(PREFIX),
        "Base framework version/prefix differs",
    )
    require(
        sys.flags.isolated == 1
        and sys.flags.no_site == 1
        and sys.flags.dont_write_bytecode == 1,
        "-I -S -B required",
    )
    expected = [
        str(PREFIX / "lib/python311.zip"),
        str(PREFIX / "lib/python3.11"),
        str(PREFIX / "lib/python3.11/lib-dynload"),
    ]
    # Helper scripts explicitly add their own authenticated source directory only.
    actual = [p for p in sys.path if p != str(Path(__file__).resolve().parent)]
    require(
        actual == expected and absent_path(Path(expected[0])),
        "Isolated stdlib path/absent zip changed",
    )
    require(
        str(UNUSED_TARGET) not in sys.path
        and not any("site-packages" in p for p in sys.path),
        "Ambient package path admitted",
    )
    return {
        "profile": "isolated-base-standard-library",
        "python": pin(BASE),
        "version": sys.version,
        "prefix": sys.prefix,
        "sys_path": actual,
        "absent_stdlib_zip": expected[0],
        "site_initialization_disabled": True,
        "scientific_installed_runtime": False,
    }


def expand_dependency(value: str, owner: Path, executable: Path) -> Path:
    if value.startswith("@loader_path/"):
        return owner.parent / value.removeprefix("@loader_path/")
    if value.startswith("@executable_path/"):
        return executable.parent / value.removeprefix("@executable_path/")
    require(not value.startswith("@"), "Unknown native loader token: " + value)
    path = Path(value)
    require(path.is_absolute(), "Relative native dependency is undeclared: " + value)
    return path


def native_closure(
    seeds: set[Path],
) -> tuple[set[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    validate_inspector(INSPECTOR, INSPECTOR_SHA)
    files: set[Path] = {INSPECTOR}
    edges: list[dict[str, Any]] = []
    aliases = []
    queue = [INSPECTOR]
    for path in sorted(seeds):
        with path.open("rb") as stream:
            if stream.read(4) in MAGIC:
                queue.append(path)
    visited: set[Path] = set()
    while queue:
        image = queue.pop()
        if image in visited:
            continue
        visited.add(image)
        files.add(image)
        text = subprocess.check_output(
            [str(INSPECTOR), "-arch", "arm64", "-L", str(image)], text=True, timeout=15
        )
        commands = subprocess.check_output(
            [str(INSPECTOR), "-arch", "arm64", "-l", str(image)], text=True, timeout=15
        )
        rpaths, install_ids = loader_commands(commands)
        dependencies = dependency_load_names(text, image)
        for declared in dependencies:
            if declared in install_ids:
                edges.append(
                    {
                        "image": str(image),
                        "declared": declared,
                        "scope": "LC_ID_DYLIB-self-identity",
                    }
                )
                continue
            if declared.startswith(("/usr/lib/", "/System/Library/")):
                edges.append(
                    {
                        "image": str(image),
                        "declared": declared,
                        "scope": "apple-system-image",
                        "authority": "pinned-sw-vers-and-kernel-release",
                        "physical_file_sha_claimed": False,
                    }
                )
                continue

            if declared.startswith("@rpath/"):
                choices = [
                    expand_dependency(r, image, BASE) / declared.removeprefix("@rpath/")
                    for r in rpaths
                ]
            else:
                choices = [expand_dependency(declared, image, BASE)]
            existing = [p for p in choices if p.is_file()]
            targets = {p.resolve(strict=True) for p in existing}
            require(
                len(targets) == 1,
                f"Missing/ambiguous native dependency in {image}: {declared}; candidates={choices}",
            )
            target = next(iter(targets))
            # Preserve every lexical dependency alias, including ancestor links.
            for lexical in existing:
                for part in (lexical, *lexical.parents):
                    if part.is_symlink():
                        aliases.append(
                            {
                                "path": str(part),
                                "link": os.readlink(part),
                                "target": str(part.resolve(strict=True)),
                                "scope": "native-dependency-alias",
                            }
                        )
            edges.append(
                {
                    "image": str(image),
                    "declared": declared,
                    "scope": "physical-native-dependency",
                    "resolved": pin(target),
                    "lexical_candidates": [str(p) for p in existing],
                }
            )
            if target not in visited:
                queue.append(target)
    unique = {r["path"]: r for r in aliases}
    return files, edges, [unique[k] for k in sorted(unique)]


def runtime_inputs() -> tuple[set[Path], dict[str, Any]]:
    guard = profile_guard()
    files, aliases = tree(PREFIX)
    # These are the exact maintained replay, common launcher and observer stdlib
    # imports. Unused bundled extensions remain physically pinned but are not
    # relabelled as loaded or required launch contexts.
    for name in (
        "argparse",
        "collections",
        "ctypes",
        "hashlib",
        "json",
        "pathlib",
        "resource",
        "runpy",
        "signal",
        "subprocess",
        "time",
        "traceback",
        "typing",
        "math",
    ):
        __import__(name)
    seeds = {BASE, PREFIX / "Python"}
    origins = []
    for name, module in sorted(sys.modules.items()):
        value = getattr(module, "__file__", None)
        if value:
            path = Path(value).resolve()
            require(
                path.is_relative_to(PREFIX)
                or path.is_relative_to(Path(__file__).resolve().parent),
                f"Unowned stdlib preparation import: {name}: {path}",
            )
            origins.append({"module": name, "file": pin(path)})
            if path.is_relative_to(PREFIX):
                seeds.add(path)
    native, edges, dependency_aliases = native_closure(seeds)
    files.update(native)
    files.update((INSPECTOR, Path("/usr/bin/sw_vers")))
    preparation_native = raw_process_snapshot()
    for value in preparation_native["native_images"]:
        if not sealed_system_image(value):
            require(
                Path(value).resolve(strict=True) in files,
                "Mapped preparation image outside declared native closure: " + value,
            )
    system = subprocess.check_output(["/usr/bin/sw_vers"], text=True, timeout=15)
    return files, {
        **guard,
        "framework_root": str(PREFIX),
        "framework_membership": tree_membership(PREFIX),
        "native_inspector": pin(INSPECTOR),
        "native_inspector_architecture": "explicit ordinary arm64",
        "tree_aliases": aliases,
        "native_aliases": dependency_aliases,
        "native_edges": edges,
        "stdlib_preparation_import_origins": origins,
        "native_dependency_seeds": [str(p) for p in sorted(seeds)],
        "actual_preparation_process_snapshot": preparation_native,
        "system_authority": {"sw_vers": system, "uname": list(os.uname())},
        "omission_scope": "Exact unused framework site-packages alias is not traversed. -I -S excludes site/user/environment package initialization. All framework regular files are pinned; recursive non-system native dependency closure is resolved for the executable/framework and actually imported required stdlib extensions. Other bundled native extensions remain pinned, not claimed executed. Apple system images use exact OS authority, not invented file hashes.",
    }


def wall_within_bound(elapsed: float, bound: int) -> bool:
    return (
        type(elapsed) in (int, float)
        and math.isfinite(elapsed)
        and 0 <= elapsed <= bound
    )


def system_unchanged(authority: dict[str, Any]) -> bool:
    return bool(
        subprocess.check_output(["/usr/bin/sw_vers"], text=True, timeout=15)
        == authority["sw_vers"]
        and list(os.uname()) == authority["uname"]
    )


def raw_process_snapshot() -> dict[str, Any]:
    """Actual current-process namespace and mapped images; called only by root-owned native steps."""
    import ctypes

    handle = ctypes.CDLL(None)
    count = handle._dyld_image_count
    count.restype = ctypes.c_uint
    name = handle._dyld_get_image_name
    name.argtypes = [ctypes.c_uint]
    name.restype = ctypes.c_char_p
    images = []
    for index in range(count()):
        value = name(index)
        require(value is not None, f"Native image name missing: {index}")
        images.append(value.decode("utf-8"))
    namespaces = []
    for key, module in sorted(sys.modules.items()):
        value = getattr(module, "__file__", None)
        namespaces.append(
            {"module": key, "file": str(Path(value).resolve()) if value else None}
        )
    return {"pid": os.getpid(), "native_images": images, "namespace": namespaces}


def sealed_system_image(path: str) -> bool:
    return path.startswith(
        (
            "/usr/lib/",
            "/System/Library/",
            "/System/Volumes/Preboot/Cryptexes/OS/usr/lib/",
            "/System/Volumes/Preboot/Cryptexes/OS/System/Library/",
        )
    )


def qualify_process_snapshot(
    raw: dict[str, Any], pins: list[dict[str, Any]], source: Path
) -> None:
    expected = {row["path"]: row for row in pins}
    for value in raw["native_images"]:
        require(
            type(value) is str and Path(value).is_absolute(),
            "Native image must be an absolute path",
        )
        if sealed_system_image(value):
            continue
        path = Path(value).resolve(strict=True)
        require(
            str(path) in expected and pin(path) == expected[str(path)],
            "Unowned or changed mapped native image: " + value,
        )
    for row in raw["namespace"]:
        if row["file"] is not None:
            path = Path(row["file"])
            require(
                path.is_relative_to(PREFIX) or path.is_relative_to(source),
                "Namespace outside isolated stdlib/owned source: "
                + row["module"]
                + ": "
                + str(path),
            )
            require(
                str(path) in expected and pin(path) == expected[str(path)],
                "Unpinned namespace origin: " + str(path),
            )
