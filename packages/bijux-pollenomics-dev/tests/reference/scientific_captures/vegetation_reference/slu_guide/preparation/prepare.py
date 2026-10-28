"""Freeze one bounded public source acquisition without changing the qualified runtime."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import ssl
import subprocess
import sys
import sysconfig
from typing import Any

sys.path.insert(0, str(Path(__file__).absolute().parent))
# Import the same stdlib HTTP/parser boundary used by the future stage, without a request.
import acquire
from contracts import (
    PAGE,
    PDF,
    PDF_BYTES,
    PDF_SHA,
    RETAINED,
    dump,
    pin,
    read,
    require,
    sha,
)
from runtime_custody import native_closure, stdlib_alias_contract, tree

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    require(git("branch", "--show-current").strip() == b"main", "Local main required")
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def native_aliases(
    authority: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    """Bind only actual loader-declared lexical alias components to exact targets."""
    aliases: dict[str, str] = {}
    links: dict[str, str] = {}
    for row in authority:
        lexical = row.get("lexical_path")
        if lexical is None:
            continue
        require(
            isinstance(lexical, str) and Path(lexical).is_absolute(),
            "Native lexical dependency path differs",
        )
        dependency = Path(lexical)
        require(
            pin(dependency.resolve(strict=True)) == row["target"],
            "Native lexical dependency target changed",
        )
        for component in (dependency, *dependency.parents):
            if component.is_symlink():
                name = str(component)
                target = str(component.resolve(strict=True))
                literal = str(component.readlink())
                require(
                    name not in aliases
                    or (aliases[name] == target and links[name] == literal),
                    "Native alias identity changed during preparation",
                )
                aliases[name] = target
                links[name] = literal
    return aliases, links


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix) == PY.parent.parent
        and sys.version_info[:2] == (3, 11)
        and sys.flags.isolated == 1,
        "Qualified isolated lexical Python3.11 required",
    )
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean current main required",
    )
    out = args.output.absolute()
    require(
        out.resolve() == out
        and out.is_relative_to(R / "artifacts")
        and not out.exists()
        and not any(p.is_symlink() for p in (out, *out.parents)),
        "Fresh physical artifacts output required",
    )
    manifest = A / "prepared-source-manifest.json"
    review = A / "independent-source-review.json"
    for row in read(manifest)["files"]:
        require(
            pin(A / row["path"]) == {**row, "path": str(A / row["path"])},
            "Held source changed",
        )
    require(
        read(review)["approved"] is True
        and read(review)["source_manifest_sha256"] == sha(manifest),
        "Exact independent source review required",
    )
    retained = pin(R / RETAINED)
    require(
        retained["sha256"] == PDF_SHA and retained["bytes"] == PDF_BYTES,
        "Retained guide identity differs",
    )
    ca_entry = Path(ssl.get_default_verify_paths().openssl_cafile)
    require(
        ca_entry.is_absolute() and ca_entry.is_file(), "Qualified TLS CA source absent"
    )
    ca = ca_entry.resolve(strict=True)
    ca_pin = pin(ca)
    stdlib = Path(sysconfig.get_path("stdlib")).resolve(strict=True)
    external, unused, stdlib_authority = stdlib_alias_contract(
        stdlib, PY.parent.parent, sys.path
    )
    stdlib_files, aliases = tree(
        stdlib, external_files=external, unused_directory_aliases=unused
    )
    module_origins = {}
    for name, module in tuple(sys.modules.items()):
        path = getattr(module, "__file__", None)
        if path and Path(path).is_file():
            module_origins[name] = pin(Path(path).resolve(strict=True))
    native_files, native_authority = native_closure(
        [PY.resolve(), *[Path(row["path"]) for row in module_origins.values()]]
    )
    alias_links = {name: str(Path(name).readlink()) for name in aliases}
    native_alias_targets, native_alias_links = native_aliases(native_authority)
    for name, target in native_alias_targets.items():
        require(
            name not in aliases or aliases[name] == target,
            "Native and stdlib alias targets disagree",
        )
        require(
            name not in alias_links or alias_links[name] == native_alias_links[name],
            "Native and stdlib alias text disagrees",
        )
        aliases[name] = target
        alias_links[name] = native_alias_links[name]
    for entry in [PY, ca_entry, *ca_entry.parents]:
        if entry.is_symlink():
            aliases[str(entry)] = str(entry.resolve(strict=True))
            alias_links[str(entry)] = str(entry.readlink())
    files = {
        *stdlib_files,
        *native_files,
        ca,
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        R / RETAINED,
        R / "artifacts/science/runtime/receipt.json",
        manifest,
        review,
        Path("/usr/bin/otool"),
        Path("/usr/bin/sw_vers"),
    }
    files.update(Path(row["path"]) for row in module_origins.values())
    files.update(A / row["path"] for row in read(manifest)["files"])
    common = R / "artifacts/science/current-report-custody/run_account_qualification.py"
    files.add(common)
    require(identity() == before, "Current source changed during preparation")
    out.mkdir()
    (out / "scratch").mkdir()
    (out / "python-cache").mkdir()
    path = out / "plan.json"
    plan = {
        "id": "official-slu-guide-source-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "canonical_identity": before,
        "qualified_python": str(PY),
        "common_runner": str(common),
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "runtime_aliases": aliases,
        "runtime_alias_links": alias_links,
        "stdlib_authority": stdlib_authority,
        "native_runtime_dependencies": native_authority,
        "module_origins": module_origins,
        "OS_build": subprocess.check_output(
            ["/usr/bin/sw_vers", "-buildVersion"], text=True, timeout=10
        ).strip(),
        "OpenSSL": ssl.OPENSSL_VERSION,
        "CA": ca_pin,
        "CA_lexical_entry": str(ca_entry),
        "retained_guide": retained,
        "page_url": PAGE,
        "PDF_url": PDF,
        "input_pins": [pin(p) for p in sorted(files)],
        "absent_input_paths": [],
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TMPDIR": str(out / "scratch"),
            "PYTHONPYCACHEPREFIX": str(out / "python-cache"),
        },
        "stages": [
            {
                "id": "current-official-page-and-literal-guide-acquisition",
                "argv": [
                    str(PY),
                    "-I",
                    "-B",
                    "-X",
                    "pycache_prefix=" + str(out / "python-cache"),
                    str(A / "acquire.py"),
                    "--plan",
                    str(path),
                ],
                "timeout_seconds": 65,
                "must_succeed": True,
            },
            {
                "id": "independent-current-response-link-and-guide-byte-review",
                "argv": [
                    str(PY),
                    "-I",
                    "-B",
                    "-X",
                    "pycache_prefix=" + str(out / "python-cache"),
                    str(A / "observe.py"),
                    "--plan",
                    str(path),
                ],
                "timeout_seconds": 20,
                "must_succeed": True,
            },
        ],
        "resources": {
            "overall_timeout_seconds": 100,
            "declared_memory_bytes": 1073741824,
            "declared_storage_bytes": 67108864,
        },
        "scope": "Only current officialSLU HTTPS page and its literal calibrationPDF; network declared to slu.se/www.slu.se only, max3redirects/2MiBpage/256KiBPDF,45sinnerdeadline+65sstageprocessgroup. VerifiedTLS explicitpinnedCA/noenvproxy. Existing136339Bguide compare, no original2026-09-21/a063 receipt recovery. No workbook/outcome/newdata/model/outreach, guide acquisition epoch remains current. CompletedchildRSS/logicaloutput+16KiBownreceiptpostchecks; no hardOSquota.",
    }
    require(
        Path(acquire.__file__).absolute() == A / "acquire.py",
        "Acquisition source boundary differs",
    )
    require(identity() == before, "Current source changed during preparation")
    dump(path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(path),
                "inputs": len(files),
                "actual_launch_argv": [
                    str(PY),
                    "-I",
                    "-B",
                    str(A / "run.py"),
                    "--plan",
                    str(path),
                    "--registered-plan-sha256",
                    sha(path),
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
