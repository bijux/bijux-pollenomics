"""Fail-closed contracts for an independently verified atlas candidate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import json
from pathlib import Path
import re
from typing import cast

JsonObject = dict[str, object]
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_BUILD_ID = re.compile(r"atlas-[0-9a-f]{64}")
_SAFE_NAME = re.compile(r"[a-z][a-z0-9-]*")
NORDIC_SOURCE_CHRONOLOGY_PROFILE = "nordic-source-chronology-v1"
GENERIC_TIME_AWARE_PROFILE = "generic-time-aware-atlas-v1"
NATIVE_LRA_PROFILE = "native-lra-exploratory-v1"
SIGNED_NATIVE_LRA_PROFILE = "native-lra-signed-calendar-v1"
SIGNED_CALENDAR_PROFILE = "calendar-bp1950-signed.v1"
VERIFICATION_PROFILES = frozenset(
    {
        NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        GENERIC_TIME_AWARE_PROFILE,
        NATIVE_LRA_PROFILE,
        SIGNED_NATIVE_LRA_PROFILE,
    }
)


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
        """Reject malformed repository and report identities."""
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


def safe_artifact_path(value: object) -> str:
    """Require an unambiguous POSIX spelling before filesystem containment."""
    if (
        not isinstance(value, str)
        or not value
        or "\\" in value
        or "\x00" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise AtlasBrowserContractError(
            "artifact path must be a normalized relative path"
        )
    return value


@dataclass(frozen=True)
class AtlasArtifactCandidate:
    """A generated local presentation with explicitly recorded source provenance."""

    build_id: str
    generator_repository_head: str
    generator_repository_tree: str
    generator_receipt: str
    generator_receipt_sha256: str
    presentation_root: str
    presentation_manifest_sha256: str
    presentation_inventory_sha256: str
    product_manifest_sha256: str
    display_geometry_sha256: str
    kind: str = "local_lra_presentation"

    def __post_init__(self) -> None:
        if self.kind != "local_lra_presentation":
            raise AtlasBrowserContractError("unsupported artifact candidate kind")
        for key in ("generator_repository_head", "generator_repository_tree"):
            _git_object_id(getattr(self, key), label=key)
        if (
            not isinstance(self.build_id, str)
            or _BUILD_ID.fullmatch(self.build_id) is None
        ):
            raise AtlasBrowserContractError("invalid artifact build_id")
        for field in fields(self):
            if field.name.endswith("sha256") and (
                not isinstance(getattr(self, field.name), str)
                or re.fullmatch(r"[0-9a-f]{64}", getattr(self, field.name)) is None
            ):
                raise AtlasBrowserContractError(
                    f"invalid artifact digest: {field.name}"
                )
        for key in ("generator_receipt", "presentation_root"):
            value = safe_artifact_path(getattr(self, key))
            if not value.startswith("artifacts/"):
                raise AtlasBrowserContractError(f"{key} must be under artifacts/")
        if not self.generator_receipt.endswith(".json"):
            raise AtlasBrowserContractError("generator receipt must be JSON")
        if Path(self.generator_receipt).is_relative_to(self.presentation_root):
            raise AtlasBrowserContractError(
                "generator receipt must be outside presentation"
            )

    def as_json(self) -> JsonObject:
        return cast(JsonObject, asdict(self))

    @classmethod
    def from_json(cls, value: object) -> AtlasArtifactCandidate:
        if not isinstance(value, dict) or set(value) != {
            field.name for field in fields(cls)
        }:
            raise AtlasBrowserContractError("artifact candidate fields must be exact")
        if any(not isinstance(item, str) for item in value.values()):
            raise AtlasBrowserContractError("artifact candidate values must be strings")
        return cls(**value)


BrowserCandidate = AtlasCandidate | AtlasArtifactCandidate


@dataclass(frozen=True)
class AtlasScope:
    """One published atlas document and its content manifest."""

    name: str
    document: str
    manifest: str

    def __post_init__(self) -> None:
        """Reject unsafe scope names and mismatched output locations."""
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
    candidate: BrowserCandidate
    scopes: tuple[AtlasScope, ...]
    verification_profile: str = NORDIC_SOURCE_CHRONOLOGY_PROFILE
    timeout_seconds: int = 45

    def __post_init__(self) -> None:
        """Reject mutable, unsafe, or profile-incompatible plans."""
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
        if self.verification_profile not in VERIFICATION_PROFILES:
            raise AtlasBrowserContractError("verification_profile is unsupported")
        if isinstance(self.candidate, AtlasArtifactCandidate):
            if (
                self.verification_profile
                not in {NATIVE_LRA_PROFILE, SIGNED_NATIVE_LRA_PROFILE}
                or len(self.scopes) != 1
            ):
                raise AtlasBrowserContractError(
                    "artifact candidate requires one native LRA scope"
                )
            presentation = repository_root / self.candidate.presentation_root
            receipt = repository_root / self.candidate.generator_receipt
            if presentation.is_relative_to(
                artifact_root
            ) or artifact_root.is_relative_to(presentation):
                raise AtlasBrowserContractError(
                    "presentation and browser evidence must be disjoint"
                )
            if receipt.is_relative_to(artifact_root):
                raise AtlasBrowserContractError(
                    "generator receipt must be outside browser evidence"
                )
            for path in (
                self.repository_root.absolute(),
                self.artifact_root.absolute(),
                presentation,
                receipt,
            ):
                if any(parent.is_symlink() for parent in (path, *path.parents)):
                    raise AtlasBrowserContractError(
                        "artifact paths cannot contain symbolic links"
                    )
            for scope in self.scopes:
                for member in (scope.document, scope.manifest):
                    safe_artifact_path(member)
                    if not (repository_root / member).is_relative_to(presentation):
                        raise AtlasBrowserContractError(
                            "artifact scope must belong to presentation"
                        )
        elif self.verification_profile in {
            NATIVE_LRA_PROFILE,
            SIGNED_NATIVE_LRA_PROFILE,
        }:
            raise AtlasBrowserContractError(
                "native LRA profile requires an artifact candidate"
            )
        scope_names = {scope.name for scope in self.scopes}
        if self.verification_profile == NORDIC_SOURCE_CHRONOLOGY_PROFILE and (
            len(self.scopes) != 1 or scope_names != {"nordic"}
        ):
            raise AtlasBrowserContractError(
                "Nordic source-chronology verification requires only the nordic scope"
            )
        if (
            self.verification_profile == GENERIC_TIME_AWARE_PROFILE
            and "nordic" in scope_names
        ):
            raise AtlasBrowserContractError(
                "generic time-aware verification cannot replace exact nordic verification"
            )
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
            "schema_version": "atlas-browser-verification-plan.v3"
            if isinstance(self.candidate, AtlasArtifactCandidate)
            else "atlas-browser-verification-plan.v2",
            "repository_root": str(self.repository_root.resolve()),
            "artifact_root": str(self.artifact_root.resolve()),
            "browser_binary": str(self.browser_binary.resolve()),
            "timeout_seconds": self.timeout_seconds,
            "verification_profile": self.verification_profile,
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
            "verification_profile",
            "candidate",
            "scopes",
        }
        if set(raw) != required:
            raise AtlasBrowserContractError("plan fields must be exact")
        if not isinstance(raw["schema_version"], str) or raw["schema_version"] not in {
            "atlas-browser-verification-plan.v2",
            "atlas-browser-verification-plan.v3",
        }:
            raise AtlasBrowserContractError("plan schema_version is unsupported")
        candidate = raw["candidate"]
        artifact = raw["schema_version"] == "atlas-browser-verification-plan.v3"
        if artifact:
            parsed_candidate: BrowserCandidate = AtlasArtifactCandidate.from_json(
                candidate
            )
        elif not isinstance(candidate, dict) or set(candidate) != {
            "repository_head",
            "repository_tree",
            "atlas_output_commit",
            "build_id",
        }:
            raise AtlasBrowserContractError("candidate fields must be exact")
        else:
            if not isinstance(candidate["build_id"], str):
                raise AtlasBrowserContractError("candidate.build_id must be a string")
            parsed_candidate = AtlasCandidate(
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
            )
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
        if not isinstance(raw["verification_profile"], str):
            raise AtlasBrowserContractError("verification_profile must be a string")
        if not all(
            isinstance(raw[field], str)
            for field in ("repository_root", "artifact_root", "browser_binary")
        ):
            raise AtlasBrowserContractError("plan paths must be strings")
        return cls(
            repository_root=Path(cast(str, raw["repository_root"])),
            artifact_root=Path(cast(str, raw["artifact_root"])),
            browser_binary=Path(cast(str, raw["browser_binary"])),
            candidate=parsed_candidate,
            scopes=tuple(scopes),
            verification_profile=raw["verification_profile"],
            timeout_seconds=raw["timeout_seconds"],
        )


def load_plan(path: Path) -> BrowserVerificationPlan:
    """Load a UTF-8 plan without accepting JSON extensions or duplicate ambiguity."""
    try:

        def unique(pairs: list[tuple[str, object]]) -> JsonObject:
            result: JsonObject = {}
            for key, item in pairs:
                if key in result:
                    raise AtlasBrowserContractError(f"duplicate plan key: {key}")
                result[key] = item
            return result

        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AtlasBrowserContractError(f"cannot load browser plan: {path}") from error
    return BrowserVerificationPlan.from_json(value)
