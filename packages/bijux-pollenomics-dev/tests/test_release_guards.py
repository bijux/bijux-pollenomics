"""Release guard coverage."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
from pathlib import Path
import stat
import sys
import tarfile
import zipfile

import pytest

from bijux_pollenomics_dev.release import publication_guard
from bijux_pollenomics_dev.release.publication_guard import (
    artifact_versions,
    assert_artifacts_match_version,
    assert_publishable_version,
)
from bijux_pollenomics_dev.release.version_resolver import resolve_version


def _metadata(project: str, version: str) -> bytes:
    return f"Metadata-Version: 2.4\nName: {project}\nVersion: {version}\n\n".encode()


def _wheel(
    path: Path,
    *,
    metadata: bytes | None = None,
    extra: dict[str, bytes] | None = None,
    record: bytes | None = None,
    special: tuple[str, int] | None = None,
) -> None:
    distribution, version = path.name.split("-")[:2]
    directory = f"{distribution}-{version}.dist-info"
    project = distribution.replace("_", "-").replace(".", "-").lower()
    files = {
        "example_package/__init__.py": b"VALUE = 1\n",
        directory + "/METADATA": _metadata(project, version)
        if metadata is None
        else metadata,
        directory
        + "/WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n\n",
    }
    files.update(extra or {})
    if record is None:
        rows = io.StringIO(newline="")
        writer = csv.writer(rows, lineterminator="\n")
        for name, content in files.items():
            checksum = (
                base64.urlsafe_b64encode(hashlib.sha256(content).digest())
                .rstrip(b"=")
                .decode()
            )
            writer.writerow((name, "sha256=" + checksum, len(content)))
        writer.writerow((directory + "/RECORD", "", ""))
        record = rows.getvalue().encode()
    files[directory + "/RECORD"] = record
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            member = zipfile.ZipInfo(name)
            if special is not None and name == special[0]:
                member.external_attr = special[1] << 16
            archive.writestr(member, content)


def _sdist(
    path: Path,
    *,
    metadata: bytes | None = None,
    extra: list[tuple[tarfile.TarInfo, bytes]] | None = None,
) -> None:
    root = path.name[: -len(".tar.gz")]
    distribution, version = root.rsplit("-", 1)
    project = distribution.replace("_", "-").replace(".", "-").lower()
    body = _metadata(project, version) if metadata is None else metadata
    with tarfile.open(path, "w:gz") as archive:
        member = tarfile.TarInfo(root + "/PKG-INFO")
        member.size = len(body)
        archive.addfile(member, io.BytesIO(body))
        for member, content in extra or []:
            archive.addfile(member, io.BytesIO(content) if member.isfile() else None)


def _artifact(path: Path) -> None:
    if path.name.endswith(".whl"):
        _wheel(path)
    else:
        _sdist(path)


def _pair(root: Path) -> tuple[Path, Path]:
    wheel = root / "example_package-1.2.3-py3-none-any.whl"
    sdist = root / "example-package-1.2.3.tar.gz"
    _wheel(wheel)
    _sdist(sdist)
    return wheel, sdist


def _rewrite_wheel(path: Path, replacements: dict[str, bytes | None]) -> None:
    with zipfile.ZipFile(path) as archive:
        files = {info.filename: archive.read(info) for info in archive.infolist()}
    for name, content in replacements.items():
        if content is None:
            files.pop(name)
        else:
            files[name] = content
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_resolve_version_uses_static_pyproject_version(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "example-package"
version = "1.2.3"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    assert resolve_version(pyproject, "example-package") == "1.2.3"


def test_assert_publishable_version_rejects_prerelease() -> None:
    with pytest.raises(ValueError, match="prerelease"):
        assert_publishable_version("1.2.3rc1")


def test_assert_publishable_version_rejects_local_build_marker() -> None:
    with pytest.raises(ValueError, match="local build marker"):
        assert_publishable_version("1.2.3+dirty")


def test_artifact_versions_read_wheel_and_sdist_names(tmp_path: Path) -> None:
    _artifact(tmp_path / "example_package-1.2.3-py3-none-any.whl")
    _artifact(tmp_path / "example-package-1.2.3.tar.gz")

    assert artifact_versions(tmp_path) == {
        "example-package-1.2.3.tar.gz": "1.2.3",
        "example_package-1.2.3-py3-none-any.whl": "1.2.3",
    }


def test_assert_artifacts_match_version_rejects_mismatch(tmp_path: Path) -> None:
    _artifact(tmp_path / "example_package-1.2.4-py3-none-any.whl")

    with pytest.raises(ValueError, match="artifact versions do not match"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_release_artifacts_require_one_project_and_both_archive_kinds(
    tmp_path: Path,
) -> None:
    _artifact(tmp_path / "example_package-1.2.3-py3-none-any.whl")
    with pytest.raises(ValueError, match="one wheel and one sdist"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")

    _artifact(tmp_path / "example-package-1.2.3.tar.gz")
    assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")
    _artifact(tmp_path / "other_package-1.2.3-py3-none-any.whl")
    with pytest.raises(ValueError, match="does not match requested project"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_distinct_platform_wheels_are_permitted(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "example_package-1.2.3-cp311-cp311-manylinux_x86_64.whl",
        "example-package-1.2.3.tar.gz",
    ):
        _artifact(tmp_path / name)
    assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_duplicate_normalized_sdist_is_refused(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "example-package-1.2.3.tar.gz",
        "example_package-1.2.3.tar.gz",
    ):
        _artifact(tmp_path / name)
    with pytest.raises(ValueError, match="duplicate normalized"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_malformed_wheel_name_is_refused(tmp_path: Path) -> None:
    _artifact(tmp_path / "example_package-1.2.3-improper.whl")
    _artifact(tmp_path / "example-package-1.2.3.tar.gz")
    with pytest.raises(ValueError, match="unrecognized wheel filename"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize(
    ("wheel", "reason"),
    [
        ("example_package-1.2.3-py3..py2-none-any.whl", "compatibility tags"),
        ("example_package-1.2.3-py3-none-any..whl", "compatibility tags"),
        ("example_package-1.2.3-abc-py3-none-any.whl", "build tag"),
        ("example_package_-1.2.3-py3-none-any.whl", "invalid distribution name"),
    ],
)
def test_malformed_wheel_components_are_refused(
    tmp_path: Path, wheel: str, reason: str
) -> None:
    _artifact(tmp_path / wheel)
    _artifact(tmp_path / "example-package-1.2.3.tar.gz")
    with pytest.raises(ValueError, match=reason):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_normalized_wheel_alias_does_not_duplicate_same_tag(tmp_path: Path) -> None:
    for name in (
        "example_package-1.2.3-py3-none-any.whl",
        "Example.Package-1.2.3-py3-none-any.whl",
        "example-package-1.2.3.tar.gz",
    ):
        _artifact(tmp_path / name)
    with pytest.raises(ValueError, match="duplicate normalized"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_cli_binds_requested_project_to_staged_archives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "example-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    _artifact(dist / "example_package-1.2.3-py3-none-any.whl")
    _artifact(dist / "example-package-1.2.3.tar.gz")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publication_guard",
            "--pyproject",
            str(pyproject),
            "--package-name",
            "example-package",
            "--dist-dir",
            str(dist),
        ],
    )
    assert publication_guard.main() == 0
    assert capsys.readouterr().out == "1.2.3\n"
    pyproject.write_text(
        '[project]\nname = "different-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="pyproject project name"):
        publication_guard.main()
    pyproject.write_text(
        '[project]\nname = "example-package"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    _artifact(dist / "other_package-1.2.3-py3-none-any.whl")
    with pytest.raises(ValueError, match="does not match requested project"):
        publication_guard.main()


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize(
    "identity", [("other-package", "1.2.3"), ("example-package", "9.0.0")]
)
def test_embedded_metadata_must_match_request(
    tmp_path: Path, kind: str, identity: tuple[str, str]
) -> None:
    wheel, sdist = _pair(tmp_path)
    if kind == "wheel":
        _wheel(wheel, metadata=_metadata(*identity))
    else:
        _sdist(sdist, metadata=_metadata(*identity))
    with pytest.raises(ValueError, match="embedded distribution project/version"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_renamed_distribution_cannot_relabel_embedded_identity(
    tmp_path: Path, kind: str
) -> None:
    wheel, sdist = _pair(tmp_path)
    if kind == "wheel":
        old = tmp_path / "old_package-1.2.3-py3-none-any.whl"
        _wheel(old)
        old.replace(wheel)
    else:
        old = tmp_path / "old-package-1.2.3.tar.gz"
        _sdist(old)
        old.replace(sdist)
    with pytest.raises(ValueError, match="directory identity does not match"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_empty_distribution_is_not_publication_evidence(
    tmp_path: Path, kind: str
) -> None:
    wheel, sdist = _pair(tmp_path)
    (wheel if kind == "wheel" else sdist).write_bytes(b"")
    with pytest.raises(ValueError, match="malformed"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("payload", [b"VALUE = 2\n", b"VALUE = 200\n"])
def test_wheel_record_detects_changed_payload_hash_and_size(
    tmp_path: Path, payload: bytes
) -> None:
    wheel, _ = _pair(tmp_path)
    _rewrite_wheel(wheel, {"example_package/__init__.py": payload})
    with pytest.raises(ValueError, match="wheel RECORD (hash|size)"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("extra", [True, False])
def test_wheel_record_requires_complete_file_membership(
    tmp_path: Path, extra: bool
) -> None:
    wheel, _ = _pair(tmp_path)
    changes: dict[str, bytes | None] = (
        {"unrecorded.py": b"extra"} if extra else {"example_package/__init__.py": None}
    )
    _rewrite_wheel(wheel, changes)
    with pytest.raises(ValueError, match="account for every file"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "self-hash", "weak-hash"])
def test_wheel_record_missing_ambiguous_or_weak_integrity_is_refused(
    tmp_path: Path, mutation: str
) -> None:
    wheel, _ = _pair(tmp_path)
    name = "example_package-1.2.3.dist-info/RECORD"
    with zipfile.ZipFile(wheel) as archive:
        record = archive.read(name)
    if mutation == "missing":
        replacement = None
    elif mutation == "duplicate":
        replacement = record + record.splitlines(keepends=True)[0]
    elif mutation == "self-hash":
        replacement = record.replace(
            (name + ",,\n").encode(), (name + ",sha256=abcd,0\n").encode()
        )
    else:
        replacement = record.replace(b"sha256=", b"sha1=", 1)
    _rewrite_wheel(wheel, {name: replacement})
    with pytest.raises(ValueError, match="RECORD"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize(
    "member",
    ["../escape.py", "/absolute.py", "C:/drive.py", r"..\escape.py", "pkg/./alias.py"],
)
@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_archive_member_paths_are_confined(
    tmp_path: Path, member: str, kind: str
) -> None:
    wheel, sdist = _pair(tmp_path)
    if kind == "wheel":
        _wheel(wheel, extra={member: b"escape"})
    else:
        info = tarfile.TarInfo(member)
        info.size = 6
        _sdist(sdist, extra=[(info, b"escape")])
    with pytest.raises(ValueError, match="not confined"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("member_type", ["symlink", "fifo"])
def test_distribution_members_are_regular(
    tmp_path: Path, kind: str, member_type: str
) -> None:
    wheel, sdist = _pair(tmp_path)
    if kind == "wheel":
        mode = stat.S_IFLNK if member_type == "symlink" else stat.S_IFIFO
        _wheel(wheel, extra={"extra": b"target"}, special=("extra", mode | 0o644))
    else:
        info = tarfile.TarInfo("example-package-1.2.3/extra")
        info.type = tarfile.SYMTYPE if member_type == "symlink" else tarfile.FIFOTYPE
        info.linkname = "target"
        _sdist(sdist, extra=[(info, b"")])
    with pytest.raises(ValueError, match="not regular"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_sdist_hardlink_and_duplicate_metadata_are_refused(tmp_path: Path) -> None:
    _, sdist = _pair(tmp_path)
    info = tarfile.TarInfo("example-package-1.2.3/extra")
    info.type = tarfile.LNKTYPE
    info.linkname = "example-package-1.2.3/PKG-INFO"
    _sdist(sdist, extra=[(info, b"")])
    with pytest.raises(ValueError, match="not regular"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")
    duplicate = tarfile.TarInfo("example-package-1.2.3/PKG-INFO")
    duplicate.size = 1
    _sdist(sdist, extra=[(duplicate, b"x")])
    with pytest.raises(ValueError, match="duplicate"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_duplicate_identity_headers_are_ambiguous(tmp_path: Path, kind: str) -> None:
    wheel, sdist = _pair(tmp_path)
    raw = (
        b"Metadata-Version: 2.4\nName: example-package\nName: other\nVersion: 1.2.3\n\n"
    )
    if kind == "wheel":
        _wheel(wheel, metadata=raw)
    else:
        _sdist(sdist, metadata=raw)
    with pytest.raises(ValueError, match="identity headers are ambiguous"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_symlinked_staged_distribution_is_refused(tmp_path: Path) -> None:
    wheel, _ = _pair(tmp_path)
    target = tmp_path / "retained-wheel"
    wheel.replace(target)
    wheel.symlink_to(target)
    with pytest.raises(ValueError, match="not a regular staged file"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_duplicate_zip_member_is_refused(tmp_path: Path) -> None:
    wheel, _ = _pair(tmp_path)
    with zipfile.ZipFile(wheel, "a") as archive, pytest.warns(UserWarning):
        archive.writestr("example_package/__init__.py", b"VALUE = 2\n")
    with pytest.raises(ValueError, match="duplicate distribution archive member"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("metadata_file", ["METADATA", "WHEEL"])
def test_wheel_required_metadata_files_are_present(
    tmp_path: Path, metadata_file: str
) -> None:
    wheel, _ = _pair(tmp_path)
    _rewrite_wheel(wheel, {"example_package-1.2.3.dist-info/" + metadata_file: None})
    with pytest.raises(ValueError, match="missing"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


def test_sdist_requires_top_level_identity_metadata(tmp_path: Path) -> None:
    _, sdist = _pair(tmp_path)
    with tarfile.open(sdist, "w:gz") as archive:
        member = tarfile.TarInfo("example-package-1.2.3/src/example.py")
        member.size = 1
        archive.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="PKG-INFO is missing"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_identity_metadata_has_a_bounded_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from bijux_pollenomics_dev.release import distribution_archives

    _pair(tmp_path)
    if kind == "wheel":
        monkeypatch.setattr(distribution_archives, "_MAX_METADATA_BYTES", 10)
    else:
        # Leave the wheel within the bound while making the sdist identity larger.
        _sdist(
            tmp_path / "example-package-1.2.3.tar.gz",
            metadata=_metadata("example-package", "1.2.3") + b"x" * 200,
        )
        monkeypatch.setattr(distribution_archives, "_MAX_METADATA_BYTES", 100)
    with pytest.raises(ValueError, match="bound"):
        assert_artifacts_match_version(tmp_path, "1.2.3", "example-package")
