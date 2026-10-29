"""Freeze complete cached payload and original CPython custody before offline bootstrapping."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import sysconfig
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    BASE,
    BASE_SHA,
    ROOT,
    SELECTION_SHA,
    SOURCE,
    aliases,
    confined_output,
    create_root,
    digest,
    json_value,
    namespace_snapshot,
    normalize,
    pin,
    require,
    require_runtime_environment,
    validate_payload,
    validate_probe_dependencies,
    validate_selection,
    verify_absences,
    verify_aliases,
    verify_base_namespaces,
    verify_cache_membership,
    verify_pin,
    verify_unused_namespaces,
    write_json,
)

SELECTION = (
    ROOT
    / "artifacts/science/runtime-availability-custody/offline-runtime-selection.json"
)
OTool = Path("/Library/Developer/CommandLineTools/usr/bin/otool-classic")
OTool_SHA = "ef0b500f6cb89910209839f66cab6100bb86defd7ebbfa2188a44ff5784a58b9"


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": __import__("hashlib")
        .sha256(git("ls-files", "-s", "-z"))
        .hexdigest(),
    }


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


def validate_inspector(path: Path, wanted_sha: str) -> None:
    require(
        path.is_file() and not path.is_symlink() and digest(path) == wanted_sha,
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


def is_macho(path: Path) -> bool:
    with path.open("rb") as stream:
        return stream.read(4) in {
            b"\xfe\xed\xfa\xce",
            b"\xce\xfa\xed\xfe",
            b"\xfe\xed\xfa\xcf",
            b"\xcf\xfa\xed\xfe",
            b"\xca\xfe\xba\xbe",
            b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf",
            b"\xbf\xba\xfe\xca",
        }


def resolve_dependency(
    raw: str, owner: Path, rpaths: list[str], executable: Path
) -> tuple[Path, Path]:
    def expand(value: str) -> Path:
        if value.startswith("@loader_path/"):
            return owner.parent / value.removeprefix("@loader_path/")
        if value.startswith("@executable_path/"):
            return executable.parent / value.removeprefix("@executable_path/")
        require(not value.startswith("@"), "Unknown native loader token")
        path = Path(value)
        require(path.is_absolute(), "Relative native dependency is undeclared")
        return path

    candidates = (
        [expand(raw)]
        if not raw.startswith("@rpath/")
        else [expand(value) / raw.removeprefix("@rpath/") for value in rpaths]
    )
    matches = {
        str(candidate.resolve(strict=True)): candidate
        for candidate in candidates
        if candidate.is_file()
    }
    require(
        len(matches) == 1, f"Native dependency unresolved or ambiguous: {owner}: {raw}"
    )
    resolved, lexical = next(iter(matches.items()))
    return Path(resolved), lexical


def base_runtime(
    payloads: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    str,
    list[dict[str, Any]],
    list[str],
    list[dict[str, Any]],
]:
    require(
        sys.version_info[:3] == (3, 11, 13)
        and Path(sys.executable).resolve(strict=True) == BASE
        and digest(BASE) == BASE_SHA
        and sys.flags.isolated == 1
        and sys.flags.no_site == 1
        and sys.dont_write_bytecode,
        "Preparation must use the exact original base CPython",
    )
    prefix = Path(sys.base_prefix)
    roots = [BASE.parents[1], Path(sysconfig.get_path("stdlib"))]
    # Base-only stages use no-site; global Homebrew site-packages are not source inputs.
    excluded: list[dict[str, Any]] = []
    absent_zip = [name for name in sys.path if Path(name).name == "python311.zip"]
    require(
        absent_zip
        and all(
            not Path(name).exists() and not Path(name).is_symlink()
            for name in absent_zip
        ),
        "Unexpected python311.zip namespace",
    )
    for name in sys.path:
        search_path = Path(name) if name else None
        if (
            search_path
            and search_path.exists()
            and str(search_path).startswith("/opt/homebrew/")
        ):
            roots.append(search_path)
    pending = roots[:]
    visited = set()
    physical: dict[str, dict[str, Any]] = {}
    lexical = roots[:] + [BASE]
    while pending:
        path = pending.pop()
        if path.name == "site-packages":
            excluded.append(
                {
                    "path": str(path),
                    "is_symlink": path.is_symlink(),
                    "raw_link": os.readlink(path) if path.is_symlink() else None,
                    "resolved_target": str(path.resolve(strict=False)),
                    "loaded_by_base_stages": False,
                }
            )
            continue
        lexical.append(path)
        resolved = path.resolve(strict=True)
        require(
            str(resolved).startswith("/opt/homebrew/"),
            "Unexpected external base namespace root",
        )
        if str(resolved) in visited:
            continue
        visited.add(str(resolved))
        if resolved.is_file():
            physical[str(resolved)] = pin(resolved)
        elif resolved.is_dir():
            for child in resolved.iterdir():
                require(
                    child.is_file() or child.is_dir() or child.is_symlink(),
                    "Special base runtime file",
                )
                pending.append(child)
        else:
            raise ValueError("Special base runtime target")
    namespace_roots = sorted(
        (Path(name) for name in visited if Path(name).is_dir()),
        key=lambda value: len(value.parts),
    )
    complete_roots: list[Path] = []
    for namespace_root in namespace_roots:
        if not any(namespace_root.is_relative_to(owner) for owner in complete_roots):
            complete_roots.append(namespace_root)
    namespaces = [
        namespace_snapshot(owner, [row["path"] for row in excluded])
        for owner in complete_roots
    ]
    validate_inspector(OTool, OTool_SHA)
    physical[str(OTool)] = pin(OTool)
    lexical.append(OTool)
    native = [
        Path(name) for name in physical if name != str(OTool) and is_macho(Path(name))
    ]
    native.append(OTool)
    cache_members = {row["path"] for payload in payloads for row in payload["members"]}
    for name in cache_members:
        binary = Path(name)
        if is_macho(binary):
            physical[name] = pin(binary)
            native.append(binary)
    seen = set()
    os_dependencies = set()
    native_records = []
    while native:
        path = native.pop()
        if str(path) in seen:
            continue
        seen.add(str(path))
        output = subprocess.check_output(
            [str(OTool), "-arch", "arm64", "-L", str(path)], text=True
        )
        listing = subprocess.check_output(
            [str(OTool), "-arch", "arm64", "-l", str(path)], text=True
        )
        rpaths, install_ids = loader_commands(listing)
        dependencies: list[dict[str, Any]] = []
        for raw in dependency_load_names(output, path):
            if raw in install_ids:
                dependencies.append(
                    {
                        "load_name": raw,
                        "scope": "LC_ID_DYLIB self identity, not an external dependency",
                    }
                )
                continue
            if raw.startswith(("/usr/lib/", "/System/Library/")):
                os_dependencies.add(raw)
                dependencies.append(
                    {
                        "load_name": raw,
                        "scope": "Darwin loader/shared-cache identity; raw system library bytes not claimed",
                    }
                )
                continue

            resolved, original = resolve_dependency(raw, path, rpaths, BASE)
            resolved_name = str(resolved)
            require(
                resolved_name.startswith("/opt/homebrew/")
                or resolved_name in cache_members,
                "Undeclared external native runtime",
            )
            lexical.append(original)
            if resolved_name not in physical:
                physical[resolved_name] = pin(resolved)
                native.append(resolved)
            dependencies.append(
                {
                    "load_name": raw,
                    "lexical_path": str(original),
                    "physical": physical[resolved_name],
                }
            )
        native_records.append(
            {
                "binary": str(path),
                "sha256": digest(path),
                "dependencies": dependencies,
                "role": "dependency-inspector"
                if path == OTool
                else (
                    "selected-wheel-native"
                    if str(path) in cache_members
                    else "base-or-external-runtime-native"
                ),
            }
        )
    require(
        str(BASE) in physical, "Base interpreter missing from complete physical runtime"
    )
    return (
        list(physical.values()),
        aliases(lexical),
        native_records,
        str(prefix),
        excluded,
        absent_zip,
        namespaces,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    args = parser.parse_args()
    environment_admission = require_runtime_environment(dict(os.environ))
    confined_output(args.output, absent=True)
    canonical = identity()
    require(
        canonical["candidate"] == args.candidate and canonical["status"] == "",
        "Clean candidate differs",
    )
    require(
        digest(SELECTION) == SELECTION_SHA, "Root-reviewed offline selection differs"
    )
    require(
        digest(args.review) == args.review_sha256, "Independent source review differs"
    )
    review = json_value(args.review)
    manifest = SOURCE / "prepared-source-manifest.json"
    require(
        review.get("approved") is True
        and review.get("source_manifest_sha256") == digest(manifest),
        "Source preparation lacks exact independent approval",
    )
    for row in json_value(manifest)["files"]:
        path = SOURCE / row["path"]
        require(
            path.is_file()
            and not path.is_symlink()
            and digest(path) == row["sha256"]
            and path.stat().st_size == row["bytes"],
            "Held controller member differs",
        )
    selection = json_value(SELECTION)
    validate_selection(selection)
    payloads = [validate_payload(row) for row in selection["selected"]]
    validate_probe_dependencies(payloads)
    require(
        len({normalize(row["name"]) for row in payloads}) == 147,
        "Selected installed namespace duplicates",
    )
    physical, links, native, prefix, excluded, absent_zip, namespaces = base_runtime(
        payloads
    )
    inputs = {row["path"]: row for row in physical}
    for payload in payloads:
        for row in payload["members"]:
            item = {key: row[key] for key in ("path", "sha256", "bytes")}
            require(
                item["path"] not in inputs or inputs[item["path"]] == item,
                "Input custody conflict",
            )
            inputs[item["path"]] = item
    for path in [
        SELECTION,
        args.review,
        manifest,
        *[SOURCE / row["path"] for row in json_value(manifest)["files"]],
    ]:
        inputs[str(path)] = pin(path)
    # All checks and full input census occur before any owned products are created.
    verify_aliases(links)
    verify_base_namespaces(namespaces)
    verify_cache_membership(payloads)
    verify_unused_namespaces(excluded)
    verify_absences(absent_zip)
    for row in inputs.values():
        verify_pin(row)
    output = args.output
    create_root(output)
    for name in ("temporary", "cache", "matplotlib"):
        (output / name).mkdir()
    plan_path = output / "plan.json"
    resources = {
        "overall_timeout_seconds": 600,
        "resident_memory_limit_bytes": 3 * 1024**3,
        "output_byte_limit": 8 * 1024**3,
    }
    stages: list[dict[str, Any]] = [
        {
            "id": "offline-wheel-transport",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(SOURCE / "transport.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 150,
            "must_succeed": True,
        },
        {
            "id": "owned-source-environment",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                "-m",
                "venv",
                "--copies",
                "--without-pip",
                str(output / "environment"),
            ],
            "timeout_seconds": 60,
            "must_succeed": True,
        },
        {
            "id": "hash-required-offline-install",
            "argv": [
                str(BASE),
                "-I",
                "-S",
                "-B",
                str(SOURCE / "install.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 240,
            "must_succeed": True,
        },
        {
            "id": "independent-source-runtime",
            "argv": [
                str(output / "environment/bin/python"),
                "-I",
                "-B",
                str(SOURCE / "observe.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 90,
            "must_succeed": True,
        },
    ]
    plan = {
        "schema_version": "offline-source-runtime-bootstrap-plan.v1",
        "candidate": args.candidate,
        "repository": str(ROOT),
        "canonical_identity": canonical,
        "output": str(output),
        "base_prefix": prefix,
        "base_interpreter": pin(BASE),
        "runtime_aliases": links,
        "environment_override_admission": environment_admission,
        "native_runtime_dependencies": native,
        "input_pins": [inputs[k] for k in sorted(inputs)],
        "absent_input_paths": absent_zip,
        "unused_no_site_namespaces": excluded,
        "base_namespaces": namespaces,
        "selected_payloads": payloads,
        "selection_sha256": SELECTION_SHA,
        "optional_release_distributions_missing": selection[
            "missing_optional_release_distributions"
        ],
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "",
            "PYTHONNOUSERSITE": "1",
            "PIP_CONFIG_FILE": os.devnull,
            "PIP_NO_INDEX": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "TMPDIR": str(output / "temporary"),
            "XDG_CACHE_HOME": str(output / "cache"),
            "MPLCONFIGDIR": str(output / "matplotlib"),
            "PROJ_NETWORK": "OFF",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        },
        "resources": resources,
        "stages": stages,
        "scope": "Fresh offline source-check dependencies from exact cached original wheel payloads. No old environment/process recovery, first-party editable installation, public installed API admission, network/source-build fallback, model/scientific execution or optional release-dependency completeness is claimed. Completed-child RSS and logical output bounds are postchecks; OS quotas and full descendant RSS are not claimed.",
    }
    require(
        sum(s["timeout_seconds"] for s in stages) <= 600 and identity() == canonical,
        "Stage budget/candidate changed",
    )
    write_json(plan_path, plan)
    write_json(
        output / "preparation.json",
        {
            "actual_exit": 0,
            "candidate": args.candidate,
            "plan": pin(plan_path),
            "cache_distributions": 147,
            "complete_cache_files": sum(len(r["members"]) for r in payloads),
            "runtime_pins": len(physical),
            "input_pins": len(inputs),
            "native_executions_started": 0,
        },
    )
    print(str(plan_path))


if __name__ == "__main__":
    main()
