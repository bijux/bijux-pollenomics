"""Reconcile supplied LRA delivery variants without installing received code."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.lra_delivery.archives import (
    ArchiveError,
    archive_inventory,
    compare_adoption_manifest,
    compare_inventory_files,
)

SOURCE_IDENTITIES = {
    "bijux_pollenomics_lra-0.1.0.tar": (
        1566720,
        "a738714b56656554f3f775f6128145fd310b2bc1eaa2dc2ac1300c8efc402275",
    ),
    "bijux_pollenomics_lra-0.1.0.tar.gz": (
        1076647,
        "db18907c473bcbfafe52d796e420c2d6a8f78dbd756683ade3c7f981b4476094",
    ),
    "bijux-pollenomics-lra-0.1.0-complete.zip": (
        1942,
        "90f41e7850a8cd0819e3496b9fd3391e7c190aba3b2ebfafe65fb98f26c1b3dd",
    ),
    "bijux-pollenomics-lra-0.1.0.git.bundle": (
        1832,
        "8d03dbcfd6bf4dfd69881711c7811260b7c141540a7ed61a53e3f28f28009942",
    ),
    "disqover_native_python_port_v0.1.0.zip": (
        1375419,
        "2d34088f55327fc39ec09e48364e0d1d0b511bdd70a476852edeef42e51568d0",
    ),
    "disqover_0.9.14.tar.gz": (
        822732,
        "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c",
    ),
}
ADOPTION = "packages/bijux-pollenomics-lra/docs/adoption-manifest.json"
INVENTORY = "reports/architecture/lra-source-adoption/prototype-files.csv"
FUNCTIONS = "reports/architecture/lra-source-adoption/source-functions.csv"
INTEGRATION = ("CLONE_LOG.txt", "PATCH_STATUS.md", "README.md", "host_adapter.py")


def _identity(path: Path, maximum: int = 4 * 1024 * 1024) -> tuple[int, str]:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ArchiveError("ordinary bounded source file required")
    data = path.read_bytes()
    if len(data) > maximum:
        raise ArchiveError("source file grew beyond byte ceiling")
    return len(data), hashlib.sha256(data).hexdigest()


def inspect_bundle(repository: Path, path: Path) -> dict[str, Any]:
    """Verify advertised history closure without importing any Git objects."""
    before = _identity(path)
    data = path.read_bytes()
    header, delimiter, pack = data.partition(b"\n\n")
    if not delimiter or len(header) > 65536 or not pack.startswith(b"PACK"):
        raise ArchiveError("invalid or oversized Git bundle header")
    try:
        lines = header.decode("ascii").splitlines()
    except UnicodeDecodeError as error:
        raise ArchiveError("non-ASCII Git bundle header") from error
    if not lines or lines[0] != "# v2 git bundle":
        raise ArchiveError("only the received SHA-1 v2 bundle is supported")
    prerequisites: list[str] = []
    refs: dict[str, str] = {}
    for line in lines[1:]:
        match = re.fullmatch(r"(-?)([0-9a-f]{40}) (.+)", line)
        if match is None:
            raise ArchiveError("invalid Git bundle ref or prerequisite")
        prefix, oid, name = match.groups()
        if prefix:
            prerequisites.append(oid)
        elif name in refs:
            raise ArchiveError("duplicate Git bundle ref")
        else:
            refs[name] = oid
    if not refs:
        raise ArchiveError("Git bundle has no advertised refs")
    commands: dict[str, Any] = {}
    for operation in ("verify", "list-heads"):
        result = subprocess.run(
            ["git", "--no-optional-locks", "bundle", operation, str(path)],
            cwd=repository,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if len(result.stdout.encode()) + len(result.stderr.encode()) > 65536:
            raise ArchiveError("Git bundle diagnostic byte ceiling")
        commands[operation] = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        if result.returncode:
            raise ArchiveError(f"Git bundle {operation} failed")
        if operation == "list-heads":
            observed: dict[str, str] = {}
            for row in result.stdout.splitlines():
                oid, sep, name = row.partition(" ")
                if not sep or name in observed:
                    raise ArchiveError("invalid or duplicate listed Git bundle ref")
                observed[name] = oid
            if observed != refs:
                raise ArchiveError("Git bundle header and listed refs differ")
    if _identity(path) != before:
        raise ArchiveError("Git bundle changed during inspection")
    return {
        "source": {"path": str(path), "bytes": before[0], "sha256": before[1]},
        "format": "git_bundle_v2_sha1",
        "refs": refs,
        "prerequisites": prerequisites,
        "commands": commands,
        "scope": "Closure of advertised refs; not complete prior development or archive-tree equivalence.",
    }


def build(repository: Path, deliveries: Path, output: Path) -> dict[str, Any]:
    """Compare all received variants with their existing adoption consumers."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    deliveries = deliveries.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    sources = {name: _identity(deliveries / name) for name in SOURCE_IDENTITIES}
    if sources != SOURCE_IDENTITIES:
        raise ArchiveError("received delivery identity differs from original inventory")
    consumer_paths = [repository / rel for rel in (ADOPTION, INVENTORY, FUNCTIONS)]
    consumer_bytes = [p.read_bytes() for p in consumer_paths]
    manifest = json.loads(consumer_bytes[0])
    inventories = [
        archive_inventory(deliveries / name)
        for name in (
            "bijux_pollenomics_lra-0.1.0.tar",
            "bijux_pollenomics_lra-0.1.0.tar.gz",
            "bijux-pollenomics-lra-0.1.0-complete.zip",
        )
    ]
    tar, compressed, adapter = inventories
    comparisons = {
        "tar_to_compressed_tar": compare_inventory_files(tar, compressed),
        "tar_to_adoption_manifest": compare_adoption_manifest(tar, manifest),
    }
    if tar["root"] != compressed["root"] or any(
        not row["equal"] for row in comparisons.values()
    ):
        raise ArchiveError(
            "source-tree comparison refused: "
            + json.dumps(
                {
                    "tar_root": tar["root"],
                    "compressed_tar_root": compressed["root"],
                    "comparisons": comparisons,
                },
                sort_keys=True,
            )
        )
    adapter_members = {
        row["path"]: row for row in adapter["members"] if row["type"] == "file"
    }
    expected_adapter = {".gitignore"} | {f"integration/{n}" for n in INTEGRATION}
    if set(adapter_members) != expected_adapter:
        raise ArchiveError("adapter delivery member population differs")
    integration: list[dict[str, Any]] = []
    for name in INTEGRATION:
        relative = f"integration/{name}"
        identity = _identity(deliveries / relative)
        archived = adapter_members[relative]
        if identity != (archived["bytes"], archived["sha256"]):
            raise ArchiveError("standalone integration file differs from ZIP member")
        integration.append(
            {"path": relative, "bytes": identity[0], "sha256": identity[1]}
        )
    prototype_rows = list(csv.DictReader(consumer_bytes[1].decode().splitlines()))
    function_rows = list(csv.DictReader(consumer_bytes[2].decode().splitlines()))
    if len(prototype_rows) != 72 or len(function_rows) != 41:
        raise ArchiveError("existing prototype/function inventory population differs")
    embedded_r = [
        row
        for row in tar["members"]
        if row["type"] == "file" and row["path"].endswith("disqover_0.9.14.tar.gz")
    ]
    if (
        len(embedded_r) != 1
        or (embedded_r[0]["bytes"], embedded_r[0]["sha256"])
        != SOURCE_IDENTITIES["disqover_0.9.14.tar.gz"]
    ):
        raise ArchiveError(
            "earlier package does not contain the authenticated original R archive"
        )
    bundle = inspect_bundle(
        repository, deliveries / "bijux-pollenomics-lra-0.1.0.git.bundle"
    )
    if sources != {name: _identity(deliveries / name) for name in SOURCE_IDENTITIES}:
        raise ArchiveError("received delivery changed during audit")
    if any(
        _identity(deliveries / row["path"]) != (row["bytes"], row["sha256"])
        for row in integration
    ):
        raise ArchiveError("standalone integration file changed during audit")
    if consumer_bytes != [p.read_bytes() for p in consumer_paths]:
        raise ArchiveError("adoption consumers changed during audit")
    report = {
        "schema_version": "lra-delivery-comparison.v1",
        "status": "passed",
        "sources": {
            name: {"bytes": n, "sha256": sha} for name, (n, sha) in sources.items()
        },
        "archives": inventories,
        "comparisons": comparisons,
        "integration_files": integration,
        "bundle": bundle,
        "reused_prototype_inventory": {
            "listed_file_dispositions": len(prototype_rows),
            "qualified_regular_zip_members": 73,
            "unlisted_self_manifest": "FILE_MANIFEST.json",
            "functions": len(function_rows),
            "file_inventory": INVENTORY,
            "function_inventory": FUNCTIONS,
            "scope": "Existing qualified ZIP/R inventory reused; no prototype or R execution.",
        },
        "adoption_manifest": ADOPTION,
        "elapsed_seconds": time.monotonic() - started,
        "limits": {
            "wall_seconds": 60,
            "peak_rss_bytes": 512 * 1024 * 1024,
            "output_bytes": 2 * 1024 * 1024,
        },
    }
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if time.monotonic() - started > 60 or len(payload.encode()) > 2 * 1024 * 1024:
        raise ArchiveError(
            "delivery audit exceeded its declared time or output ceiling"
        )
    with output.open("x") as stream:
        stream.write(payload)
    return report


def main() -> None:
    """Require explicit originals and an absent repository artifact destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--deliveries", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build(args.repository, args.deliveries, args.output)
    print(
        json.dumps(
            {"status": report["status"], "elapsed_seconds": report["elapsed_seconds"]}
        )
    )


if __name__ == "__main__":
    main()
