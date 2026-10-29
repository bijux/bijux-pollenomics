"""Independently qualify new offline dependency versions, payloads and native origins."""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib
import importlib.metadata as metadata
import io
from pathlib import Path
import platform
import subprocess
import sys
import sysconfig
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    BASE_SHA,
    CORE,
    FIRST_PARTY,
    NATIVE_PROBES,
    OBSERVER_PROBES,
    OPTIONAL_MISSING,
    confined_output,
    digest,
    json_value,
    native_origin,
    normalize,
    require,
    validate_probe_dependencies,
    write_json,
)


def installed_member(
    environment: Path, site: Path, name: str, distribution: str
) -> Path:
    parts = name.split("/")
    if parts[0].endswith(".data"):
        require(len(parts) >= 3, "Malformed installed data mapping")
        kind = parts[1]
        tail = Path(*parts[2:])
        roots = {
            "purelib": site,
            "platlib": site,
            "scripts": environment / "bin",
            "data": environment,
            "headers": environment
            / "include/site/python3.11"
            / distribution.split("-", 1)[0],
        }
        require(kind in roots, "Undeclared wheel installation scheme")
        return roots[kind] / tail
    return site / name


def installed_record(distribution: metadata.Distribution, environment: Path) -> int:
    raw = distribution.read_text("RECORD")
    require(isinstance(raw, str), "Installed RECORD absent")
    seen = set()
    for row in csv.reader(io.StringIO(raw, newline="")):
        require(
            len(row) == 3 and row[0] not in seen, "Installed RECORD duplicate or shape"
        )
        seen.add(row[0])
        path = Path(str(distribution.locate_file(row[0])))
        require(
            path.is_file()
            and not path.is_symlink()
            and path.resolve().is_relative_to(environment),
            "Installed RECORD file escaped environment",
        )
        if row[1]:
            require(
                row[1].startswith("sha256=")
                and row[2].isascii()
                and row[2].isdecimal(),
                "Installed RECORD hash/size shape differs",
            )
            encoded = (
                base64.urlsafe_b64encode(bytes.fromhex(digest(path)))
                .decode()
                .rstrip("=")
            )
            require(
                row[1] == "sha256=" + encoded and path.stat().st_size == int(row[2]),
                "Installed RECORD hash/size differs",
            )
        else:
            require(
                row[0].endswith(".dist-info/RECORD") and row[2] == "",
                "Unexpected unhashed installed payload",
            )
    return len(seen)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json_value(args.plan)
    output = confined_output(Path(plan["output"]))
    environment = Path(plan["retained_environment"])
    require(
        Path(sys.prefix) == environment
        and Path(sys.executable) == environment / "bin/python",
        "Observer is not the newly owned interpreter",
    )
    require(
        sys.version_info[:3] == (3, 11, 13)
        and platform.python_implementation() == "CPython"
        and platform.machine() == "arm64"
        and sys.platform == "darwin",
        "Original CPython ABI/platform differs",
    )
    require(
        digest(Path(sys.executable)) == BASE_SHA
        and Path(sys.base_prefix).resolve(strict=True)
        == Path(plan["base_prefix"]).resolve(strict=True),
        "New interpreter/base authority differs",
    )
    site = Path(sysconfig.get_path("purelib"))
    require(
        site == environment / "lib/python3.11/site-packages",
        "Owned site-packages differs",
    )
    transport = json_value(Path(plan["retained_wheels"]) / "transport-manifest.json")
    wheels = {normalize(row["name"]): row for row in transport["distributions"]}
    expected = {normalize(row["name"]): row for row in plan["selected_payloads"]}
    validate_probe_dependencies(plan["selected_payloads"])
    installed = {}
    for distribution in metadata.distributions(path=[str(site)]):
        name = normalize(distribution.metadata["Name"])
        require(name not in installed, "Duplicate installed distribution")
        installed[name] = distribution
    require(
        set(installed) == set(expected) == set(wheels) and len(installed) == 147,
        "Installed distribution membership differs",
    )
    require(
        not (set(installed) & (FIRST_PARTY | OPTIONAL_MISSING)),
        "First-party editable or missing optional release metadata appeared",
    )
    proofs = []
    for name, source in expected.items():
        distribution = installed[name]
        require(distribution.version == source["version"], "Installed version differs")
        dist_info = site / source["distribution"]
        require(
            digest(dist_info / "METADATA") == source["metadata_sha256"]
            and digest(dist_info / "WHEEL") == source["wheel_sha256"],
            "Installed original metadata/WHEEL differs",
        )
        count = installed_record(distribution, environment)
        wheel = wheels[name]
        path = Path(wheel["path"])
        require(
            digest(path) == wheel["sha256"] and path.stat().st_size == wheel["bytes"],
            "Transport wheel changed before observation",
        )
        original_payloads = 0
        with zipfile.ZipFile(path) as archive:
            require(
                archive.namelist() == [row["name"] for row in source["members"]],
                "Independent complete wheel membership differs",
            )
            for row in source["members"]:
                raw = archive.read(row["name"])
                require(
                    hashlib.sha256(raw).hexdigest() == row["sha256"]
                    and len(raw) == row["bytes"],
                    "Independent cached-payload transport bytes differ",
                )
                if row["name"] == source["distribution"] + "/RECORD":
                    continue
                destination = installed_member(
                    environment, site, row["name"], source["distribution"]
                )
                require(
                    destination.is_file()
                    and not destination.is_symlink()
                    and destination.resolve().is_relative_to(environment),
                    "Original installed wheel member absent/unconfined",
                )
                observed = destination.read_bytes()
                if ".data/scripts/" in row["name"] and raw.startswith(
                    (b"#!python\n", b"#!pythonw\n")
                ):
                    tail = raw.split(b"\n", 1)[1]
                    python = str(environment / "bin/python").encode()
                    allowed = [
                        b"#!" + python + b"\n" + tail,
                        b"#!/bin/sh\n'''exec' "
                        + python
                        + b" \"$0\" \"$@\"\n' '''\n"
                        + tail,
                    ]
                    require(
                        observed in allowed,
                        "Pip script relocation differs from explicit interpreter rewrite",
                    )
                else:
                    require(observed == raw, "Original installed payload changed")
                original_payloads += 1
        proofs.append(
            {
                "name": source["name"],
                "version": distribution.version,
                "original_metadata_sha256": source["metadata_sha256"],
                "original_WHEEL_sha256": source["wheel_sha256"],
                "original_RECORD_sha256": source["record_sha256"],
                "new_installed_RECORD_sha256": digest(dist_info / "RECORD"),
                "installed_RECORD_files_authenticated": count,
                "original_payload_files_authenticated": original_payloads,
                "new_transport_wheel_sha256": wheel["sha256"],
                "complete_original_native_tags": source["complete_wheel_tags"],
            }
        )
    imports = {}
    for name, distribution_name in OBSERVER_PROBES.items():
        module = importlib.import_module(name)
        module_file = module.__file__
        require(isinstance(module_file, str), "Core import has no physical origin")
        assert isinstance(module_file, str)
        origin = Path(module_file)
        require(
            origin.resolve().is_relative_to(site),
            "Core import resolved outside newly installed payload",
        )
        imports[name] = {
            "origin": str(origin),
            "sha256": digest(origin),
            "version": str(
                getattr(
                    module,
                    "__version__",
                    metadata.version(distribution_name),
                )
            ),
        }
    for name, wanted in CORE.items():
        require(metadata.version(name) == wanted, "Exact core version differs")
    pyproj = importlib.import_module("pyproj")
    require(
        pyproj.proj_version_str == "9.5.1"
        and pyproj.network.is_network_enabled() is False,
        "PROJ version/network scope differs",
    )
    native = {}
    for name in NATIVE_PROBES:
        module = importlib.import_module(name)
        module_file = module.__file__
        require(isinstance(module_file, str), "Native import has no physical origin")
        assert isinstance(module_file, str)
        native[name] = native_origin(Path(module_file), site)
    ruff_binary = environment / "bin/ruff"
    require(
        ruff_binary.is_file() and not ruff_binary.is_symlink(),
        "Owned Ruff native binary is absent",
    )
    ruff = subprocess.run(
        [str(ruff_binary), "--version"], capture_output=True, text=True, check=False
    )
    require(
        ruff.returncode == 0 and ruff.stdout.strip() == "ruff 0.15.8",
        "Offline Ruff executable failed",
    )
    write_json(
        output / "independent-runtime-review.json",
        {
            "schema_version": "offline-source-runtime-independent-review.v1",
            "actual_exit": 0,
            "candidate": plan["candidate"],
            "retained_bootstrap": plan["retained_bootstrap"],
            "original_bootstrap_whole_actual_exit": 1,
            "production_stage_actual_exits": [0, 0, 0],
            "new_observation_only": True,
            "new_environment": str(environment),
            "python": sys.version,
            "base_prefix": sys.base_prefix,
            "selected_distribution_count": 147,
            "distributions": proofs,
            "core_imports": imports,
            "native_CP311_imports": native,
            "PROJ_version": "9.5.1",
            "ruff_stdout": ruff.stdout,
            "optional_release_distributions_still_missing": sorted(OPTIONAL_MISSING),
            "first_party_editable_metadata_copied": False,
            "old_runtime_recovered_or_same_process_claimed": False,
            "original_download_archive_SHA_claimed": False,
            "installed_first_party_interface_claimed": False,
            "scope": "New offline source-check dependency environment, exact original cached wheel payload and metadata, independently observed imports/native ABI. Later canonical first-party roots require explicit PYTHONPATH; no installed package interface, scientific/model execution or historical runtime identity is inferred.",
        },
    )


if __name__ == "__main__":
    main()
