"""Independent source and byte closure for local presentation browser candidates."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any
import zipfile

from ..atlas_media.process_execution import BoundedProcessError, run_bounded_argv
from .contracts import (
    AtlasArtifactCandidate,
    AtlasBrowserContractError,
    BrowserVerificationPlan,
    JsonObject,
    safe_artifact_path,
)

SOURCE_ROOTS = (
    "packages/bijux-pollenomics/src",
    "packages/bijux-pollenomics/pyproject.toml",
    "pyproject.toml",
    "uv.lock",
    "configs/scientific-contracts",
)
ENTRY_POINT = "bijux_pollenomics.reporting.lra_products.api:render_lra_report"


GENERATOR_SCRIPT = """import hashlib,json,platform,sys
from importlib import metadata
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from bijux_pollenomics.reporting.lra_products.api import render_lra_report
render_lra_report(Path(sys.argv[2]),expected_manifest_sha256=sys.argv[3],geometry_path=Path(sys.argv[4]),expected_geometry_sha256=sys.argv[5],destination=Path(sys.argv[6]))
print(json.dumps({'python':platform.python_version(),'implementation':platform.python_implementation(),'executable':str(Path(sys.executable).resolve()),'executable_sha256':hashlib.sha256(Path(sys.executable).resolve().read_bytes()).hexdigest(),'distributions':sorted([{'name':d.metadata['Name'],'version':d.version} for d in metadata.distributions()],key=lambda d:(d['name'],d['version']))}))
"""


def canonical_digest(value: object) -> str:
    """SHA256 of ASCII-escaped, sorted, compact JSON without a terminal newline."""
    return sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def regular_bytes(path: Path) -> bytes:
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise AtlasBrowserContractError(f"symbolic link in candidate: {path}")
    try:
        descriptor = os.open(
            path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise AtlasBrowserContractError(f"nonregular candidate member: {path}")
            return stream.read()
    except OSError as error:
        raise AtlasBrowserContractError(
            f"cannot read candidate member: {path}"
        ) from error


def json_bytes(value: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise AtlasBrowserContractError(f"duplicate candidate JSON key: {key}")
            result[key] = item
        return result

    try:
        result = json.loads(value, object_pairs_hook=unique)
        if not isinstance(result, dict):
            raise ValueError("expected an object")
        canonical_digest(result)
    except (ValueError, UnicodeError) as error:
        raise AtlasBrowserContractError("invalid candidate JSON") from error
    return result


def inventory(root: Path) -> list[dict[str, Any]]:
    """Inventory every regular member, refusing links and nonregular entries."""
    if root.is_symlink() or not root.is_dir():
        raise AtlasBrowserContractError(
            f"candidate root is not a real directory: {root}"
        )
    result = []
    for path in sorted(
        root.rglob("*"), key=lambda member: member.relative_to(root).as_posix()
    ):
        if path.is_symlink():
            raise AtlasBrowserContractError(f"symbolic link in candidate: {path}")
        if path.is_dir():
            continue
        member = safe_artifact_path(path.relative_to(root).as_posix())
        value = regular_bytes(path)
        result.append(
            {"path": member, "sha256": sha256(value), "byte_count": len(value)}
        )
    return result


def git_bytes(root: Path, *args: str) -> bytes:
    try:
        result = run_bounded_argv(("git", *args), cwd=root, timeout_seconds=30)
    except BoundedProcessError as error:
        raise AtlasBrowserContractError(
            "cannot inspect generator Git objects"
        ) from error
    if result.timed_out or result.returncode:
        raise AtlasBrowserContractError("generator Git object inspection failed")
    return result.stdout


def committed_source(root: Path, head: str, tree: str) -> dict[str, str]:
    """Resolve all required generator paths from an immutable committed tree."""
    if git_bytes(root, "rev-parse", f"{head}^{{tree}}").decode().strip() != tree:
        raise AtlasBrowserContractError("generator HEAD/tree relationship differs")
    entries = git_bytes(
        root, "ls-tree", "-r", "-z", "--full-tree", head, "--", *SOURCE_ROOTS
    )
    result = {}
    for row in entries.split(b"\x00"):
        if not row:
            continue
        metadata, member = row.decode().split("\t", 1)
        mode, kind, object_id = metadata.split()
        member = safe_artifact_path(member)
        if mode not in {"100644", "100755"} or kind != "blob" or member in result:
            raise AtlasBrowserContractError(
                "generator tree contains unsupported entries"
            )
        result[member] = object_id
    for required in SOURCE_ROOTS:
        if not any(
            member == required or member.startswith(required + "/") for member in result
        ):
            raise AtlasBrowserContractError(
                f"generator tree lacks required source: {required}"
            )
    return result


def source_inventory(root: Path, objects: dict[str, str]) -> dict[str, str]:
    """Require actual source bytes to equal their declared committed Git blobs."""
    actual_paths: set[str] = set()
    for name in SOURCE_ROOTS:
        selected = root / name
        if selected.is_symlink():
            raise AtlasBrowserContractError("symbolic generator source root")
        if selected.is_dir():
            actual_paths.update(name + "/" + row["path"] for row in inventory(selected))
        elif selected.is_file():
            actual_paths.add(name)
    # Interpreter caches are not generator inputs; all other extras refuse.
    actual_paths = {
        name for name in actual_paths if "__pycache__" not in Path(name).parts
    }
    if actual_paths != set(objects):
        raise AtlasBrowserContractError(
            "generator source inventory differs from committed tree"
        )
    result = {}
    for member, object_id in sorted(objects.items()):
        value = regular_bytes(root / member)
        encoded = b"blob " + str(len(value)).encode() + b"\x00" + value
        observed = hashlib.new(
            "sha1" if len(object_id) == 40 else "sha256", encoded
        ).hexdigest()
        if observed != object_id:
            raise AtlasBrowserContractError(
                f"generator source differs from committed tree: {member}"
            )
        result[member] = sha256(value)
    return result


def _bound(root: Path, member: str, expected: str) -> bytes:
    value = regular_bytes(root / safe_artifact_path(member))
    if sha256(value) != expected:
        raise AtlasBrowserContractError(f"candidate input digest differs: {member}")
    return value


def _source_receipt(root: Path, candidate: AtlasArtifactCandidate) -> dict[str, Any]:
    encoded = _bound(
        root, candidate.generator_receipt, candidate.generator_receipt_sha256
    )
    receipt = json_bytes(encoded)
    required = {
        "schema_version",
        "source_relation",
        "generator_repository_head",
        "generator_repository_tree",
        "source_root",
        "source_files",
        "entry_point",
        "runtime",
        "invocation",
        "inputs",
        "output",
    }
    if (
        set(receipt) != required
        or receipt["schema_version"] != "atlas-artifact-generation.v1"
        or receipt["source_relation"] != "committed_tree"
    ):
        raise AtlasBrowserContractError(
            "unsupported generator receipt or source relation"
        )
    if (
        receipt["entry_point"] != ENTRY_POINT
        or receipt["generator_repository_head"] != candidate.generator_repository_head
        or receipt["generator_repository_tree"] != candidate.generator_repository_tree
    ):
        raise AtlasBrowserContractError("generator receipt identity differs")
    source_relative = safe_artifact_path(receipt["source_root"])
    if not source_relative.startswith("artifacts/"):
        raise AtlasBrowserContractError(
            "generator source snapshot must be under artifacts"
        )
    source = root / source_relative
    presentation = root / candidate.presentation_root
    if source.is_relative_to(presentation) or presentation.is_relative_to(source):
        raise AtlasBrowserContractError(
            "generator source and presentation must be disjoint"
        )
    objects = committed_source(
        root, candidate.generator_repository_head, candidate.generator_repository_tree
    )
    if source_inventory(source, objects) != receipt["source_files"]:
        raise AtlasBrowserContractError(
            "generator source receipt differs from actual bytes"
        )
    inputs = receipt["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != {
        "product_directory",
        "geometry_path",
    }:
        raise AtlasBrowserContractError("generator inputs are incomplete")
    product_input = root / safe_artifact_path(inputs["product_directory"])
    geometry_input = root / safe_artifact_path(inputs["geometry_path"])
    receipt_path = root / candidate.generator_receipt
    trees = (source, presentation, product_input)
    if (
        any(
            a.is_relative_to(b) or b.is_relative_to(a)
            for i, a in enumerate(trees)
            for b in trees[i + 1 :]
        )
        or any(receipt_path.is_relative_to(p) for p in trees)
        or any(geometry_input.is_relative_to(p) for p in (source, presentation))
    ):
        raise AtlasBrowserContractError("generator input/output paths overlap")
    runtime = receipt["runtime"]
    if not isinstance(runtime, dict) or set(runtime) != {
        "python",
        "implementation",
        "executable",
        "executable_sha256",
        "distributions",
    }:
        raise AtlasBrowserContractError("generator runtime identity is incomplete")
    if (
        any(
            not isinstance(runtime[key], str) or not runtime[key]
            for key in ("python", "implementation", "executable")
        )
        or not Path(runtime["executable"]).is_absolute()
    ):
        raise AtlasBrowserContractError("generator interpreter identity is incomplete")
    digest = runtime["executable_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ):
        raise AtlasBrowserContractError("generator interpreter digest is invalid")
    distributions = runtime["distributions"]
    if (
        not isinstance(distributions, list)
        or not distributions
        or any(
            not isinstance(row, dict)
            or set(row) != {"name", "version"}
            or any(not isinstance(v, str) or not v for v in row.values())
            for row in distributions
        )
    ):
        raise AtlasBrowserContractError(
            "generator distribution inventory is incomplete"
        )
    if distributions != sorted(
        distributions, key=lambda row: (row["name"], row["version"])
    ):
        raise AtlasBrowserContractError("generator distribution inventory is unordered")
    invocation = receipt["invocation"]
    if not isinstance(invocation, dict) or set(invocation) != {
        "argv",
        "cwd",
        "python_binary",
    }:
        raise AtlasBrowserContractError("generator invocation is incomplete")
    argv = invocation["argv"]
    if (
        not isinstance(argv, list)
        or len(argv) != 10
        or any(not isinstance(v, str) for v in argv)
        or not isinstance(invocation["python_binary"], str)
        or not Path(invocation["python_binary"]).is_absolute()
        or argv[0] != invocation["python_binary"]
        or invocation["cwd"] != str(source)
    ):
        raise AtlasBrowserContractError("generator invocation identity differs")
    expected_arguments = [
        argv[0],
        "-I",
        "-c",
        GENERATOR_SCRIPT,
        str(source / "packages/bijux-pollenomics/src"),
        str(root / safe_artifact_path(receipt["inputs"]["product_directory"])),
        candidate.product_manifest_sha256,
        str(root / safe_artifact_path(receipt["inputs"]["geometry_path"])),
        candidate.display_geometry_sha256,
        str(presentation),
    ]
    if argv != expected_arguments:
        raise AtlasBrowserContractError("generator invocation arguments differ")
    expected_output = {
        key: value
        for key, value in candidate.as_json().items()
        if key
        in {
            "presentation_root",
            "presentation_manifest_sha256",
            "presentation_inventory_sha256",
            "product_manifest_sha256",
            "display_geometry_sha256",
            "build_id",
        }
    }
    if receipt["output"] != expected_output:
        raise AtlasBrowserContractError("generator output identity differs")
    _bound(
        root,
        safe_artifact_path(inputs["geometry_path"]),
        candidate.display_geometry_sha256,
    )
    product = root / safe_artifact_path(inputs["product_directory"])
    _verify_product(product, candidate.product_manifest_sha256)
    return receipt


def _verify_product(root: Path, expected: str) -> None:
    # The public saved-product reader does not import the optional numerical engine.
    from bijux_pollenomics.analysis.lra.api import read_lra_product

    try:
        read_lra_product(root, expected_manifest_sha256=expected)
    except ValueError as error:
        raise AtlasBrowserContractError("candidate product is invalid") from error


def audit_artifact_candidate(plan: BrowserVerificationPlan) -> JsonObject:
    candidate = plan.candidate
    if not isinstance(candidate, AtlasArtifactCandidate):
        raise AtlasBrowserContractError("artifact audit requires an artifact candidate")
    root = plan.repository_root.resolve()
    receipt = _source_receipt(root, candidate)
    presentation = root / candidate.presentation_root
    evidence = plan.artifact_root.resolve()
    source = root / receipt["source_root"]
    product_input = root / receipt["inputs"]["product_directory"]
    geometry_input = root / receipt["inputs"]["geometry_path"]
    if any(
        evidence.is_relative_to(path) or path.is_relative_to(evidence)
        for path in (source, product_input)
    ) or geometry_input.is_relative_to(evidence):
        raise AtlasBrowserContractError("browser evidence overlaps generation inputs")
    manifest = json_bytes(
        _bound(presentation, "manifest.json", candidate.presentation_manifest_sha256)
    )
    observed = inventory(presentation)
    if canonical_digest(observed) != candidate.presentation_inventory_sha256:
        raise AtlasBrowserContractError("presentation inventory identity differs")
    hashes = {
        row["path"]: row["sha256"] for row in observed if row["path"] != "manifest.json"
    }
    if manifest.get("files") != hashes:
        raise AtlasBrowserContractError(
            "presentation physical inventory differs from manifest"
        )
    expected = {
        "schema_version": "lra-presentation.v1",
        "status": "generated_exploratory",
        "scientific_acceptance": "not_evaluated",
        "publication_authorized": False,
        "map_build_id": candidate.build_id,
        "product_manifest_sha256": candidate.product_manifest_sha256,
        "display_geometry_sha256": candidate.display_geometry_sha256,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise AtlasBrowserContractError(
            "presentation identity or acceptance posture differs"
        )
    if (
        manifest.get("publication_authorized") is not False
        or manifest.get("data_kind") != "synthetic"
        or manifest.get("operation") != "lra"
    ):
        raise AtlasBrowserContractError(
            "native browser candidate must be an unapproved synthetic paired presentation"
        )
    geometry = json_bytes(
        _bound(presentation, "display-geometry.json", candidate.display_geometry_sha256)
    )
    _verify_product(presentation / "product", candidate.product_manifest_sha256)
    product_manifest = json_bytes(
        _bound(presentation, "product/manifest.json", candidate.product_manifest_sha256)
    )
    if (
        any(
            manifest.get(key) != product_manifest.get(key)
            or geometry.get(key) != product_manifest.get(key)
            for key in ("request_sha256", "scientific_content_sha256")
        )
        or geometry.get("product_manifest_sha256") != candidate.product_manifest_sha256
    ):
        raise AtlasBrowserContractError(
            "presentation product/geometry identity graph differs"
        )
    copied = {row["path"]: row for row in inventory(presentation / "product")}
    try:
        with zipfile.ZipFile(presentation / "product.zip") as archive:
            if sorted(archive.namelist()) != sorted(copied) or len(
                archive.namelist()
            ) != len(copied):
                raise AtlasBrowserContractError(
                    "original product ZIP inventory differs"
                )
            for name, row in copied.items():
                info = archive.getinfo(name)
                if (
                    info.file_size != row["byte_count"]
                    or info.compress_type != zipfile.ZIP_STORED
                    or info.flag_bits & 1
                ):
                    raise AtlasBrowserContractError(
                        "original product ZIP member contract differs"
                    )
                value = archive.read(name)
                if sha256(value) != row["sha256"] or len(value) != row["byte_count"]:
                    raise AtlasBrowserContractError("original product ZIP bytes differ")
    except (OSError, zipfile.BadZipFile) as error:
        raise AtlasBrowserContractError("original product ZIP is invalid") from error
    if inventory(presentation) != observed:
        raise AtlasBrowserContractError(
            "presentation changed during candidate verification"
        )
    # Recheck all generation sources and original inputs after output inspection.
    if _source_receipt(root, candidate) != receipt:
        raise AtlasBrowserContractError("generator receipt changed during verification")
    return {
        "schema_version": "atlas-artifact-integrity.v1",
        "candidate": candidate.as_json(),
        "files": [
            {**row, "path": candidate.presentation_root + "/" + row["path"]}
            for row in observed
        ],
        "generator_receipt_sha256": candidate.generator_receipt_sha256,
    }


def verify_served_bytes(
    plan: BrowserVerificationPlan, audit: JsonObject, report: object
) -> None:
    """Bind actual successful local responses, including changed-then-restored bytes."""
    if not isinstance(report, dict) or not isinstance(
        report.get("served_artifact_bytes"), list
    ):
        raise AtlasBrowserContractError(
            "artifact browser report lacks served-byte receipts"
        )
    if report.get("refused_artifact_reads") != []:
        raise AtlasBrowserContractError("browser refused altered artifact reads")
    files = audit["files"]
    assert isinstance(files, list)
    expected = {row["path"]: row for row in files}
    seen = set()
    for row in report["served_artifact_bytes"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "byte_count"}
            or not isinstance(row.get("path"), str)
            or not isinstance(row.get("byte_count"), int)
            or isinstance(row.get("byte_count"), bool)
            or expected.get(row.get("path")) != row
        ):
            raise AtlasBrowserContractError(
                "served artifact bytes differ from candidate"
            )
        seen.add(row["path"])
    candidate = plan.candidate
    assert isinstance(candidate, AtlasArtifactCandidate)
    required = {candidate.presentation_root + "/manifest.json"}
    required.update(
        member for scope in plan.scopes for member in (scope.document, scope.manifest)
    )
    if not required <= seen:
        raise AtlasBrowserContractError(
            "browser did not observe required artifact identities"
        )
