"""Authenticate complete current R/Python trees and selected native dependencies."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Any

from contracts import pin, require

MACHO = {
    b"\xcf\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
    b"\xca\xfe\xba\xbf",
    b"\xbf\xba\xfe\xca",
    b"\xce\xfa\xed\xfe",
}


def tree(
    root: Path,
    *,
    external_files: dict[Path, Path] | None = None,
    unused_directory_aliases: dict[Path, Path] | None = None,
) -> tuple[list[Path], dict[str, str]]:
    require(
        root.is_absolute() and root.resolve() == root and root.is_dir(),
        "Physical tree root required",
    )
    external_files = external_files or {}
    unused_directory_aliases = unused_directory_aliases or {}
    files: set[Path] = set()
    aliases: dict[str, str] = {}
    visited: set[Path] = set()

    def visit(directory: Path) -> None:
        if directory in visited:
            return
        visited.add(directory)
        for path in sorted(directory.iterdir()):
            if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_symlink():
                target = path.resolve(strict=True)
                aliases[str(path)] = str(target)
                if not target.is_relative_to(root):
                    context = f"root={root}; alias={path}; target={target}"
                    if path in external_files:
                        require(
                            target == external_files[path]
                            and target.is_file()
                            and not target.is_symlink(),
                            f"External file alias differs: {context}",
                        )
                        pin(target)
                        files.add(target)
                        continue
                    require(
                        path in unused_directory_aliases
                        and target == unused_directory_aliases[path]
                        and target.is_dir(),
                        f"Tree alias escaped declared root: {context}",
                    )
                    continue
                if target.is_dir():
                    visit(target)
                else:
                    pin(target)
                    files.add(target)
            elif path.is_dir():
                visit(path)
            else:
                pin(path)
                files.add(path)

    visit(root)
    return sorted(files), aliases


def load_commands(text: str) -> list[dict[str, str]]:
    result = []
    command = None
    for line in text.splitlines():
        value = line.strip()
        if value.startswith("cmd "):
            command = value.split(" ", 1)[1]
        elif value.startswith("name ") and command in {
            "LC_LOAD_DYLIB",
            "LC_LOAD_WEAK_DYLIB",
            "LC_REEXPORT_DYLIB",
            "LC_LOAD_UPWARD_DYLIB",
        }:
            result.append(
                {"command": command, "path": value[5:].rsplit(" (offset ", 1)[0]}
            )
    return result


def runpaths(text: str) -> tuple[str, ...]:
    result = []
    command = None
    for line in text.splitlines():
        value = line.strip()
        if value.startswith("cmd "):
            command = value.split(" ", 1)[1]
        elif command == "LC_RPATH" and value.startswith("path "):
            result.append(value[5:].rsplit(" (offset ", 1)[0])
    return tuple(result)


def native_seeds(repository: Path, r_home: Path, library: Path) -> list[Path]:
    import json
    import re

    original = json.loads(
        (
            repository / "artifacts/science/native-reference-admission/plan.json"
        ).read_bytes()
    )
    roots = [
        Path(path).resolve(strict=True)
        for path in original["host_package_paths"].values()
    ]
    roots += [library, r_home / "library/jsonlite"]
    result = {r_home / "bin/Rscript", r_home / "bin/exec/R"}
    for root in roots:
        require(
            root.resolve() == root and root.is_dir(),
            "Native namespace seed root differs",
        )
        namespace = root / "NAMESPACE"
        if not namespace.is_file():
            continue
        text = namespace.read_text()
        declared = set(
            re.findall(r'(?m)^\s*useDynLib\(\s*["\']?([A-Za-z0-9_.]+)', text)
        )
        for name in declared:
            target = root / "libs" / (name + ".so")
            require(
                target.is_file(),
                f"Declared flat R_ARCH NAMESPACE image {name} absent in {root}",
            )
            result.add(target.resolve(strict=True))

    return sorted(result)


def native_closure(files: list[Path]) -> tuple[list[Path], list[dict[str, Any]]]:
    discovered: set[Path] = set(files)
    queue = list(files)
    visited: set[Path] = set()
    records = []
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        with path.open("rb") as stream:
            magic = stream.read(4)
        if magic not in MACHO:
            continue
        text = subprocess.check_output(
            ["/usr/bin/otool", "-arch", "arm64", "-l", str(path)], text=True, timeout=20
        )
        for row in load_commands(text):
            record = {"loader": str(path), **row}
            resolved = dependency(path, row, rpaths=runpaths(text))
            records.append({**record, **resolved})
            if "target" not in resolved:
                continue
            actual = Path(resolved["target"]["path"])
            if actual not in discovered:
                discovered.add(actual)
                queue.append(actual)
    return sorted(discovered), records


def dependency(
    loader: Path, row: dict[str, str], *, rpaths: tuple[str, ...] = ()
) -> dict[str, Any]:
    name = row["path"]
    if name.startswith(("/usr/lib/", "/System/Library/")):
        return {
            "authority": "Apple sealed-system/dyld cache; current OS build pinned separately",
            "physical_file_claim": False,
        }
    if name.startswith("@rpath/"):
        candidates = []
        for value in rpaths:
            if value == "@loader_path":
                root = loader.parent
            elif value.startswith("@loader_path/"):
                root = loader.parent / value.removeprefix("@loader_path/")
            else:
                require(value.startswith("/"), "Unsupported declared LC_RPATH context")
                root = Path(value)
            candidate = root / name.removeprefix("@rpath/")
            if candidate.is_file():
                candidates.append(candidate)
        physical = {candidate.resolve(strict=True) for candidate in candidates}
        require(
            len(physical) == 1, "Missing or ambiguous loader-owned LC_RPATH dependency"
        )
        target = candidates[0]
    elif name.startswith("@loader_path/"):
        target = loader.parent / name.removeprefix("@loader_path/")
    else:
        require(
            name.startswith("/"),
            f"Unsupported loader context {name} from {loader}; do not guess",
        )
        target = Path(name)
    if not target.exists() and row["command"] == "LC_LOAD_WEAK_DYLIB":
        return {
            "authority": "Declared weak unresolved dependency, no target/load claim"
        }
    require(
        target.is_file(), f"Required native dependency absent: {name} from {loader}"
    )
    actual = target.resolve(strict=True)
    return {"target": pin(actual), "lexical_path": str(target)}


def stdlib_alias_contract(
    stdlib: Path,
    environment: Path,
    actual_sys_path: list[str],
    *,
    global_site: Path = Path("/opt/homebrew/lib/python3.11/site-packages"),
) -> tuple[dict[Path, Path], dict[Path, Path], dict[str, Any]]:
    require(stdlib.resolve() == stdlib and stdlib.is_dir(), "Physical stdlib required")
    cfg = environment / "pyvenv.cfg"
    values: dict[str, str] = {}
    for line in cfg.read_text().splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition("=")
        require(
            bool(separator) and key.strip() not in values,
            f"Ambiguous venv config: {cfg}",
        )
        values[key.strip()] = value.strip()
    require(
        values.get("include-system-site-packages") == "false",
        f"Global packages must be disabled: {cfg}",
    )
    alias = stdlib / "site-packages"
    require(
        alias.is_symlink()
        and alias.resolve(strict=True) == global_site
        and global_site.resolve() == global_site
        and global_site.is_dir(),
        f"Unused global-site alias differs: root={stdlib}; alias={alias}; target={global_site}",
    )
    require(
        all(
            not Path(entry).resolve().is_relative_to(global_site)
            for entry in actual_sys_path
        ),
        f"Ambient global packages entered qualified sys.path: {global_site}",
    )
    binary = stdlib.parent.parent / "Python"
    require(
        binary.is_file() and not binary.is_symlink(),
        f"Physical framework binary absent: {binary}",
    )
    external = {
        stdlib / "config-3.11-darwin" / name: binary
        for name in ("libpython3.11.dylib", "libpython3.11.a")
    }
    for entry, target in external.items():
        require(
            entry.is_symlink() and entry.resolve(strict=True) == target,
            f"Framework alias differs: root={stdlib}; alias={entry}; target={target}",
        )
    record = {
        "stdlib": str(stdlib),
        "venv_config": pin(cfg),
        "actual_qualified_sys_path": actual_sys_path,
        "framework_aliases": [
            {"path": str(entry), "readlink": os.readlink(entry), "target": pin(target)}
            for entry, target in sorted(external.items())
        ],
        "unused_global_site_alias": {
            "path": str(alias),
            "readlink": os.readlink(alias),
            "target": str(global_site),
            "contents_traversed_or_admitted": False,
            "authority": "Exact unused alias; system-site-packages disabled and qualified sys.path excludes target",
        },
    }
    return external, {alias: global_site}, record


def aliases_unchanged(
    aliases: dict[str, str], *, link_text: dict[str, str] | None = None
) -> bool:
    if link_text is not None and set(link_text) != set(aliases):
        return False
    try:
        return all(
            Path(a).is_symlink()
            and str(Path(a).resolve(strict=True)) == b
            and (link_text is None or os.readlink(a) == link_text[a])
            for a, b in aliases.items()
        )
    except (OSError, RuntimeError):
        return False


def requested_environment(out: Path, library: Path, r_home: Path) -> dict[str, str]:
    return {
        "PYTHONDONTWRITEBYTECODE": "1",
        "TMPDIR": str(out / "scratch"),
        "PYTHONPYCACHEPREFIX": str(out / "pycache"),
        "R_LIBS_USER": str(library),
        "R_LIBS": "",
        "R_HOME": str(r_home),
        "R_ARCH": "",
        "DYLD_INSERT_LIBRARIES": "",
        "DYLD_LIBRARY_PATH": "",
        "DYLD_FRAMEWORK_PATH": "",
        "DYLD_FALLBACK_LIBRARY_PATH": "",
        "DYLD_FALLBACK_FRAMEWORK_PATH": "",
        "R_LIBS_SITE": "",
        "R_ENVIRON_USER": "/dev/null",
        "R_PROFILE_USER": "/dev/null",
        "R_USER": str(out / "home"),
        "R_HISTFILE": str(out / "history"),
        "TZ": "UTC",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": str(r_home / "bin") + ":/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
        **dict.fromkeys(
            [
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
            ],
            "1",
        ),
    }
