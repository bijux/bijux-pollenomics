"""Publication guard helpers."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import tomllib

from .distribution_archives import (
    assert_distribution_archive,
)
from .distribution_archives import (
    canonical_project as _canonical_project,
)
from .version_resolver import resolve_version


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate that a package version is safe to publish."
    )
    parser.add_argument("--pyproject", required=True, help="Path to pyproject.toml")
    parser.add_argument("--package-name", required=True, help="Package slug/tag prefix")
    parser.add_argument(
        "--dist-dir",
        help="Optional dist directory whose artifact versions must match the resolved version",
    )
    parser.add_argument(
        "--allow-prerelease",
        action="store_true",
        help="Allow prerelease versions such as .devN or rcN",
    )
    parser.add_argument(
        "--allow-local-version",
        action="store_true",
        help="Allow local version segments such as +dirty",
    )
    return parser.parse_args()


def _artifact_version(path: Path) -> str:
    """Parse the version embedded in an sdist or wheel filename."""
    if path.name.endswith(".whl"):
        parts = path.name[:-4].split("-")
        if len(parts) < 2:
            raise ValueError(f"unrecognized wheel filename: {path.name}")
        return parts[1]
    if path.name.endswith(".tar.gz"):
        stem = path.name[: -len(".tar.gz")]
        if "-" not in stem:
            raise ValueError(f"unrecognized sdist filename: {path.name}")
        return stem.rsplit("-", 1)[1]
    raise ValueError(f"unsupported artifact extension: {path.name}")


def artifact_versions(dist_dir: Path) -> dict[str, str]:
    """Collect resolved artifact versions from a dist directory."""
    versions: dict[str, str] = {}
    for path in sorted(dist_dir.glob("*.whl")) + sorted(dist_dir.glob("*.tar.gz")):
        versions[path.name] = _artifact_version(path)
    return versions


def _assert_project_metadata(pyproject: Path, package_name: str) -> None:
    document = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    project = document.get("project")
    declared = project.get("name") if isinstance(project, dict) else None
    if not isinstance(declared, str) or _canonical_project(
        declared
    ) != _canonical_project(package_name):
        raise ValueError(
            f"pyproject project name does not match requested project {package_name}"
        )


def _artifact_identity(path: Path) -> tuple[str, str, str]:
    """Return normalized project, version, and distinct wheel/sdist identity.

    Wheel names use escaped project names, optional numeric-leading build tags,
    and three nonempty dot-separated compatibility tags. The resolved version
    is checked separately and comes from the package build metadata.
    """
    if path.name.endswith(".whl"):
        parts = path.name[:-4].split("-")
        if len(parts) not in (5, 6) or any(not part for part in parts):
            raise ValueError(f"unrecognized wheel filename: {path.name}")
        distribution, version = parts[:2]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.]*", distribution):
            raise ValueError(f"unrecognized wheel distribution: {path.name}")
        if len(parts) == 6 and re.fullmatch(r"[0-9][A-Za-z0-9_]*", parts[2]) is None:
            raise ValueError(f"unrecognized wheel build tag: {path.name}")
        if any(
            re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*", tag) is None
            for tag in parts[-3:]
        ):
            raise ValueError(f"unrecognized wheel compatibility tags: {path.name}")
        return _canonical_project(distribution), version, "wheel:" + "-".join(parts[2:])
    if path.name.endswith(".tar.gz"):
        stem = path.name[: -len(".tar.gz")]
        if "-" not in stem:
            raise ValueError(f"unrecognized sdist filename: {path.name}")
        distribution, version = stem.rsplit("-", 1)
        return _canonical_project(distribution), version, "sdist"
    raise ValueError(f"unsupported artifact extension: {path.name}")


def assert_publishable_version(
    version: str,
    *,
    allow_prerelease: bool = False,
    allow_local_version: bool = False,
) -> None:
    """Reject prerelease and local-only versions unless explicitly allowed."""
    lowered = version.lower()
    prerelease_markers = (".dev", "a", "b", "rc")
    if not allow_prerelease and any(marker in lowered for marker in prerelease_markers):
        raise ValueError(
            f"{version} is a prerelease version; create the release tag or set "
            "PUBLISH_ALLOW_PRERELEASE=1 for an intentional prerelease publish"
        )
    if not allow_local_version and ("+" in version or "dirty" in lowered):
        raise ValueError(
            f"{version} includes a local build marker; clean the checkout or set "
            "PUBLISH_ALLOW_LOCAL_VERSION=1 for an intentional local publish"
        )


def assert_artifacts_match_version(
    dist_dir: Path, version: str, package_name: str
) -> None:
    """Bind the complete wheel/sdist set to one requested project and version."""
    versions = artifact_versions(dist_dir)
    if not versions:
        raise ValueError(f"no artifacts found under {dist_dir}")
    mismatched = {
        name: artifact_version
        for name, artifact_version in versions.items()
        if artifact_version != version
    }
    if mismatched:
        details = ", ".join(
            f"{name}={artifact_version}"
            for name, artifact_version in sorted(mismatched.items())
        )
        raise ValueError(
            f"artifact versions do not match resolved version {version}: {details}"
        )
    expected_project = _canonical_project(package_name)
    seen: set[str] = set()
    kinds: set[str] = set()
    for name in versions:
        project, _, archive_identity = _artifact_identity(Path(name))
        if project != expected_project:
            raise ValueError(
                f"artifact project {project} does not match requested project "
                f"{expected_project}: {name}"
            )
        if archive_identity in seen:
            raise ValueError(f"duplicate normalized distribution artifact: {name}")
        seen.add(archive_identity)
        kinds.add("wheel" if archive_identity.startswith("wheel:") else "sdist")
    if kinds != {"wheel", "sdist"}:
        raise ValueError("publish artifacts require at least one wheel and one sdist")
    for name in versions:
        assert_distribution_archive(dist_dir / name, expected_project, version)


def main() -> int:
    """Run the command-line entry point."""
    args = parse_args()
    pyproject = Path(args.pyproject)
    _assert_project_metadata(pyproject, args.package_name)
    version = resolve_version(pyproject, args.package_name)
    if version == "0.0.0":
        raise SystemExit("unable to resolve package version")
    assert_publishable_version(
        version,
        allow_prerelease=args.allow_prerelease,
        allow_local_version=args.allow_local_version,
    )
    if args.dist_dir:
        assert_artifacts_match_version(Path(args.dist_dir), version, args.package_name)
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
