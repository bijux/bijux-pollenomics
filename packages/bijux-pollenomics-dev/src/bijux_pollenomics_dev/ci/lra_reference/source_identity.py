"""Separate committed Git blobs from the single governed generated version file."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
from importlib import metadata
from pathlib import Path, PurePosixPath
import re
import tomllib
from typing import Any

from .contracts import ReferenceRefusal
from .sources import source_inventory

GENERATED_PATH = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
DECLARATION_PATH = "packages/bijux-pollenomics-lra/pyproject.toml"
VERSION_NAMES = {
    "__version__",
    "version",
    "__version_tuple__",
    "version_tuple",
    "__commit_id__",
    "commit_id",
}


@dataclass(frozen=True)
class SourceIdentity:
    tracked_files: dict[str, str]
    tracked_git_blobs: dict[str, str]
    generated_files: dict[str, dict[str, Any]]
    executed_files: dict[str, str]


def generated_literals(data: bytes) -> dict[str, Any]:
    """Parse only the known literal template; never execute generated source."""
    if len(data) > 65536:
        raise ReferenceRefusal(
            "Generated version file exceeds its bounded metadata size"
        )
    try:
        tree = ast.parse(data)
    except (SyntaxError, ValueError, UnicodeError) as error:
        raise ReferenceRefusal("Malformed generated version source") from error
    values: dict[str, Any] = {}
    annotations: set[str] = set()
    future = 0
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and node.level == 0
            and len(node.names) == 1
            and node.names[0].name == "annotations"
            and node.names[0].asname is None
        ):
            future += 1
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in VERSION_NAMES
            and node.value is None
            and ast.unparse(node.annotation)
            in {"str", "str | None", "tuple[int | str, ...]"}
        ):
            if node.target.id in annotations:
                raise ReferenceRefusal("Duplicate generated version annotation")
            annotations.add(node.target.id)
        elif isinstance(node, ast.Assign) and all(
            isinstance(target, ast.Name) for target in node.targets
        ):
            names = tuple(
                target.id for target in node.targets if isinstance(target, ast.Name)
            )
            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError) as error:
                raise ReferenceRefusal(
                    "Generated version contains nonliteral execution"
                ) from error
            if frozenset(names) not in {
                frozenset({"__all__"}),
                frozenset({"__version__", "version"}),
                frozenset({"__version_tuple__", "version_tuple"}),
                frozenset({"__commit_id__", "commit_id"}),
            } or len(names) != len(set(names)):
                raise ReferenceRefusal("Unexpected generated version assignment")
            for name in names:
                if name in values:
                    raise ReferenceRefusal("Duplicate generated version value")
                values[name] = value
        else:
            raise ReferenceRefusal(
                "Generated version contains unsupported executable statements"
            )
    version = values.get("__version__")
    version_tuple = values.get("__version_tuple__")
    commit_id = values.get("__commit_id__")
    if (
        future != 1
        or annotations != VERSION_NAMES
        or set(values) != VERSION_NAMES | {"__all__"}
        or not isinstance(values["__all__"], list)
        or len(values["__all__"]) != 6
        or any(not isinstance(item, str) for item in values["__all__"])
        or set(values["__all__"]) != VERSION_NAMES
        or not isinstance(version, str)
        or re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+_-]*", version) is None
        or not isinstance(version_tuple, tuple)
        or not version_tuple
        or any(type(item) not in {str, int} for item in version_tuple)
        or (
            commit_id is not None
            and (
                not isinstance(commit_id, str)
                or re.fullmatch(r"[0-9a-f]+", commit_id) is None
            )
        )
    ):
        raise ReferenceRefusal(
            "Generated version literal metadata is incomplete or malformed"
        )
    return {
        "version": version,
        "version_tuple": list(version_tuple),
        "commit_id": commit_id,
    }


def inspect_source_identity(repository: Path, git_tree: bytes) -> SourceIdentity:
    """Compare actual blob bytes to the supplied exact HEAD tree, including ignored files."""
    executed = source_inventory(repository)
    blobs: dict[str, str] = {}
    try:
        for entry in git_tree.split(b"\0"):
            if not entry:
                continue
            header, raw_path = entry.split(b"\t", 1)
            mode, kind, blob = header.decode("ascii").split(" ")
            path = raw_path.decode("utf-8")
            if (
                mode not in {"100644", "100755"}
                or kind != "blob"
                or re.fullmatch(r"[0-9a-f]{40}", blob) is None
                or PurePosixPath(path).is_absolute()
                or ".." in PurePosixPath(path).parts
                or path in blobs
            ):
                raise ValueError("invalid tree entry")
            blobs[path] = blob
    except (UnicodeError, ValueError) as error:
        raise ReferenceRefusal(
            "Malformed or unsupported committed source tree"
        ) from error
    if not blobs or set(blobs) - set(executed):
        raise ReferenceRefusal(
            "Tracked executable source is missing from the executed tree"
        )
    extras = set(executed) - set(blobs)
    if extras - {GENERATED_PATH}:
        raise ReferenceRefusal("Untracked or ignored executable source is not governed")
    for path, expected in blobs.items():
        data = (repository / path).read_bytes()
        actual = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()
        if actual != expected:
            raise ReferenceRefusal(
                "Actual tracked source differs from its committed Git blob: " + path
            )
    generated: dict[str, dict[str, Any]] = {}
    if GENERATED_PATH in extras:
        declaration = tomllib.loads((repository / DECLARATION_PATH).read_text())
        if (
            declaration.get("tool", {})
            .get("hatch", {})
            .get("build", {})
            .get("hooks", {})
            .get("vcs", {})
            .get("version-file")
            != "src/bijux_pollenomics_lra/_build_version.py"
        ):
            raise ReferenceRefusal(
                "Generated version file is not declared by package metadata"
            )
        generated[GENERATED_PATH] = {
            "sha256": executed[GENERATED_PATH],
            "declaration_path": DECLARATION_PATH,
            "declaration_sha256": executed[DECLARATION_PATH],
            "profile": "hatch-vcs-literal-version-metadata-v1",
            "literals": generated_literals((repository / GENERATED_PATH).read_bytes()),
            "committed_source": False,
        }
    return SourceIdentity(
        {path: executed[path] for path in sorted(blobs)}, blobs, generated, executed
    )


def selected_engine_version(identity: SourceIdentity) -> dict[str, Any]:
    """Record the branch selected by the committed engine version module policy."""
    try:
        distribution = metadata.distribution("bijux-pollenomics-lra")
    except metadata.PackageNotFoundError:
        generated = identity.generated_files.get(GENERATED_PATH)
        if generated is None:
            return {"origin": "source-only-unknown-fallback", "version": "0+unknown"}
        return {
            "origin": "governed-generated-fallback",
            "version": generated["literals"]["version"],
            "generated_sha256": generated["sha256"],
        }
    return {
        "origin": "installed-distribution-metadata",
        "version": distribution.version,
        "distribution_location": str(distribution.locate_file("")),
        "metadata_sha256": hashlib.sha256(
            (distribution.read_text("METADATA") or "").encode()
        ).hexdigest(),
    }


def validate_generated_evidence(root: Path, certificate: dict[str, Any]) -> None:
    generated = certificate.get("generated_source_files")
    blobs = certificate.get("tracked_git_blobs")
    source_files = certificate.get("source_files")
    if (
        not isinstance(generated, dict)
        or set(generated) - {GENERATED_PATH}
        or not isinstance(blobs, dict)
        or not isinstance(source_files, dict)
        or set(blobs) != set(source_files)
    ):
        raise ReferenceRefusal("Tracked/generated source classification is incomplete")
    if any(
        not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None
        for value in blobs.values()
    ):
        raise ReferenceRefusal("Committed Git blob identity is malformed")
    for path, row in generated.items():
        retained = root / "generated-sources" / path
        data = retained.read_bytes()
        if row != {
            "sha256": hashlib.sha256(data).hexdigest(),
            "declaration_path": DECLARATION_PATH,
            "declaration_sha256": source_files.get(DECLARATION_PATH),
            "profile": "hatch-vcs-literal-version-metadata-v1",
            "literals": generated_literals(data),
            "committed_source": False,
        }:
            raise ReferenceRefusal("Retained generated source metadata differs")
    actual = {
        path.relative_to(root / "generated-sources").as_posix()
        for path in (root / "generated-sources").rglob("*")
        if path.is_file()
    }
    if actual != set(generated):
        raise ReferenceRefusal("Generated source retained member inventory differs")
    runtime = certificate.get("engine_version_identity")
    if (
        not isinstance(runtime, dict)
        or runtime.get("origin")
        not in {
            "installed-distribution-metadata",
            "governed-generated-fallback",
            "source-only-unknown-fallback",
        }
        or not isinstance(runtime.get("version"), str)
    ):
        raise ReferenceRefusal("Selected engine runtime version origin is missing")
    if runtime["origin"] == "governed-generated-fallback" and (
        GENERATED_PATH not in generated
        or runtime.get("generated_sha256") != generated[GENERATED_PATH]["sha256"]
        or runtime["version"] != generated[GENERATED_PATH]["literals"]["version"]
    ):
        raise ReferenceRefusal("Generated fallback version identity differs")
    if runtime["origin"] == "source-only-unknown-fallback" and (
        generated or runtime["version"] != "0+unknown"
    ):
        raise ReferenceRefusal(
            "Unknown version fallback conflicts with generated source"
        )
    if runtime["origin"] == "installed-distribution-metadata" and (
        not isinstance(runtime.get("metadata_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", runtime["metadata_sha256"]) is None
    ):
        raise ReferenceRefusal("Installed distribution version lacks metadata identity")
