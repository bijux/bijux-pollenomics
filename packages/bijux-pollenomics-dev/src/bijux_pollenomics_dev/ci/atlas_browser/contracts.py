"""Fail-closed contracts for an independently verified atlas candidate."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import cast

JsonObject = dict[str, object]
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_BUILD_ID = re.compile(r"atlas-[0-9a-f]{64}")
_SAFE_NAME = re.compile(r"[a-z][a-z0-9-]*")


class AtlasBrowserContractError(ValueError):
    """Raised when browser evidence is incomplete, ambiguous, or unsafe."""


def _safe_relative_file(value: str, *, label: str, suffix: str) -> str:
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix != suffix
        or any(part in {"", "."} for part in path.parts)
    ):
        raise AtlasBrowserContractError(f"{label} must be a safe {suffix} path")
    return path.as_posix()


def _git_object_id(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _GIT_OBJECT_ID.fullmatch(value) is None:
        raise AtlasBrowserContractError(f"{label} must be a lowercase Git object ID")
    return value


@dataclass(frozen=True)
class AtlasCandidate:
    """Immutable Git and atlas identities expected throughout one verification."""

    repository_head: str
    repository_tree: str
    atlas_output_commit: str
    build_id: str

    def __post_init__(self) -> None:
        _git_object_id(self.repository_head, label="candidate.repository_head")
        _git_object_id(self.repository_tree, label="candidate.repository_tree")
        _git_object_id(self.atlas_output_commit, label="candidate.atlas_output_commit")
        if _BUILD_ID.fullmatch(self.build_id) is None:
            raise AtlasBrowserContractError(
                "candidate.build_id must be atlas- followed by a SHA-256"
            )

    def as_json(self) -> JsonObject:
        """Return the exact candidate identity passed to the browser process."""
        return {
            "repository_head": self.repository_head,
            "repository_tree": self.repository_tree,
            "atlas_output_commit": self.atlas_output_commit,
            "build_id": self.build_id,
        }


@dataclass(frozen=True)
class AtlasScope:
    """One published atlas document and its content manifest."""

    name: str
    document: str
    manifest: str

    def __post_init__(self) -> None:
        if _SAFE_NAME.fullmatch(self.name) is None:
            raise AtlasBrowserContractError("scope.name is not a durable slug")
        _safe_relative_file(self.document, label="scope.document", suffix=".html")
        _safe_relative_file(self.manifest, label="scope.manifest", suffix=".json")
        if Path(self.document).parent != Path(self.manifest).parent:
            raise AtlasBrowserContractError(
                "scope document and manifest must share an output directory"
            )

    def as_json(self) -> JsonObject:
        """Return the browser-process representation."""
        return {
            "name": self.name,
            "document": self.document,
            "manifest": self.manifest,
        }


@dataclass(frozen=True)
class BrowserVerificationPlan:
    """Validated inputs for a non-mutating atlas browser verification run."""

    repository_root: Path
    artifact_root: Path
    browser_binary: Path
    candidate: AtlasCandidate
    scopes: tuple[AtlasScope, ...]
    timeout_seconds: int = 45

    def __post_init__(self) -> None:
        repository_root = self.repository_root.resolve()
        artifact_root = self.artifact_root.resolve()
        if not repository_root.is_dir():
            raise AtlasBrowserContractError("repository_root must be a directory")
        if (
            repository_root == artifact_root
            or repository_root not in artifact_root.parents
        ):
            raise AtlasBrowserContractError(
                "artifact_root must be a dedicated directory inside the repository"
            )
        if "artifacts" not in artifact_root.relative_to(repository_root).parts:
            raise AtlasBrowserContractError("artifact_root must be under artifacts/")
        if not self.browser_binary.is_file():
            raise AtlasBrowserContractError("browser_binary must be an existing file")
        if not self.scopes or len({scope.name for scope in self.scopes}) != len(
            self.scopes
        ):
            raise AtlasBrowserContractError("scopes must be non-empty and unique")
        if self.timeout_seconds < 10 or self.timeout_seconds > 300:
            raise AtlasBrowserContractError("timeout_seconds must be in [10, 300]")
        for scope in self.scopes:
            if not (repository_root / scope.document).is_file():
                raise AtlasBrowserContractError(
                    f"scope document is absent: {scope.document}"
                )
            if not (repository_root / scope.manifest).is_file():
                raise AtlasBrowserContractError(
                    f"scope manifest is absent: {scope.manifest}"
                )

    def as_json(self) -> JsonObject:
        """Return the stable subprocess contract without host-specific inference."""
        return {
            "schema_version": "atlas-browser-verification-plan.v1",
            "repository_root": str(self.repository_root.resolve()),
            "artifact_root": str(self.artifact_root.resolve()),
            "browser_binary": str(self.browser_binary.resolve()),
            "timeout_seconds": self.timeout_seconds,
            "candidate": self.candidate.as_json(),
            "scopes": [scope.as_json() for scope in self.scopes],
        }

    @classmethod
    def from_json(cls, value: object) -> BrowserVerificationPlan:
        """Parse a plan and reject missing or additional contract fields."""
        if not isinstance(value, dict):
            raise AtlasBrowserContractError("plan must be an object")
        raw = cast(JsonObject, value)
        required = {
            "schema_version",
            "repository_root",
            "artifact_root",
            "browser_binary",
            "timeout_seconds",
            "candidate",
            "scopes",
        }
        if set(raw) != required:
            raise AtlasBrowserContractError("plan fields must be exact")
        if raw["schema_version"] != "atlas-browser-verification-plan.v1":
            raise AtlasBrowserContractError("plan schema_version is unsupported")
        candidate = raw["candidate"]
        if not isinstance(candidate, dict) or set(candidate) != {
            "repository_head",
            "repository_tree",
            "atlas_output_commit",
            "build_id",
        }:
            raise AtlasBrowserContractError("candidate fields must be exact")
        raw_scopes = raw["scopes"]
        if not isinstance(raw_scopes, list):
            raise AtlasBrowserContractError("scopes must be an array")
        scopes: list[AtlasScope] = []
        for raw_scope in raw_scopes:
            if not isinstance(raw_scope, dict) or set(raw_scope) != {
                "name",
                "document",
                "manifest",
            }:
                raise AtlasBrowserContractError("scope fields must be exact")
            if not all(
                isinstance(raw_scope[field], str)
                for field in ("name", "document", "manifest")
            ):
                raise AtlasBrowserContractError("scope values must be strings")
            scopes.append(
                AtlasScope(
                    name=raw_scope["name"],
                    document=raw_scope["document"],
                    manifest=raw_scope["manifest"],
                )
            )
        if not isinstance(raw["timeout_seconds"], int):
            raise AtlasBrowserContractError("timeout_seconds must be an integer")
        if not all(
            isinstance(raw[field], str)
            for field in ("repository_root", "artifact_root", "browser_binary")
        ):
            raise AtlasBrowserContractError("plan paths must be strings")
        if not isinstance(candidate["build_id"], str):
            raise AtlasBrowserContractError("candidate.build_id must be a string")
        return cls(
            repository_root=Path(cast(str, raw["repository_root"])),
            artifact_root=Path(cast(str, raw["artifact_root"])),
            browser_binary=Path(cast(str, raw["browser_binary"])),
            candidate=AtlasCandidate(
                repository_head=_git_object_id(
                    candidate["repository_head"], label="candidate.repository_head"
                ),
                repository_tree=_git_object_id(
                    candidate["repository_tree"], label="candidate.repository_tree"
                ),
                atlas_output_commit=_git_object_id(
                    candidate["atlas_output_commit"],
                    label="candidate.atlas_output_commit",
                ),
                build_id=candidate["build_id"],
            ),
            scopes=tuple(scopes),
            timeout_seconds=raw["timeout_seconds"],
        )


def load_plan(path: Path) -> BrowserVerificationPlan:
    """Load a UTF-8 plan without accepting JSON extensions or duplicate ambiguity."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasBrowserContractError(f"cannot load browser plan: {path}") from error
    return BrowserVerificationPlan.from_json(value)
