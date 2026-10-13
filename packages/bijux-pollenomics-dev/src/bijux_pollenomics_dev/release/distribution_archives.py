"""Validate embedded distribution identity and confined regular archive contents."""

from __future__ import annotations

import base64
import csv
from email.parser import BytesParser
from email.policy import compat32
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import zipfile

_MAX_MEMBERS = 100_000
_MAX_EXPANDED_BYTES = 2 * 1024**3
_MAX_METADATA_BYTES = 1024**2
_MAX_RECORD_BYTES = 16 * 1024**2
_RECORD_ALGORITHMS = frozenset(
    {
        "sha256",
        "sha384",
        "sha512",
        "sha3_256",
        "sha3_384",
        "sha3_512",
        "blake2b",
        "blake2s",
    }
)


def canonical_project(name: str) -> str:
    """Normalize the ASCII project spelling shared by filenames and metadata."""
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?", name):
        raise ValueError(f"invalid distribution name: {name!r}")
    return re.sub(r"[-_.]+", "-", name).lower()


def _member_name(name: str) -> PurePosixPath:
    if (
        not name
        or "\\" in name
        or name.startswith("/")
        or re.match(r"[A-Za-z]:", name)
        or any(ord(character) < 32 for character in name)
    ):
        raise ValueError("distribution archive member is not confined")
    trimmed = name[:-1] if name.endswith("/") else name
    if any(part in {"", ".", ".."} for part in trimmed.split("/")):
        raise ValueError("distribution archive member is not confined")
    return PurePosixPath(trimmed)


def _metadata_identity(raw: bytes, project: str, version: str) -> None:
    metadata = BytesParser(policy=compat32).parsebytes(raw)
    if metadata.defects:
        raise ValueError("distribution metadata is malformed")
    for header in ("Metadata-Version", "Name", "Version"):
        if len(metadata.get_all(header, [])) != 1:
            raise ValueError("distribution metadata identity headers are ambiguous")
    name = str(metadata["Name"]).strip()
    actual_version = str(metadata["Version"]).strip()
    if canonical_project(name) != project or actual_version != version:
        raise ValueError("embedded distribution project/version does not match request")


def _directory_identity(directory: str, project: str, version: str) -> None:
    if "-" not in directory:
        raise ValueError("distribution metadata directory identity is malformed")
    name, actual_version = directory.rsplit("-", 1)
    if canonical_project(name) != project or actual_version != version:
        raise ValueError(
            "distribution metadata directory identity does not match request"
        )


def _wheel(archive: zipfile.ZipFile, project: str, version: str) -> None:
    members = archive.infolist()
    if len(members) > _MAX_MEMBERS:
        raise ValueError("distribution archive exceeds member bound")
    files: dict[str, zipfile.ZipInfo] = {}
    seen = set()
    expanded = 0
    directories = set()
    for member in members:
        path = _member_name(member.orig_filename)
        name = str(path)
        if name in seen:
            raise ValueError("duplicate distribution archive member")
        seen.add(name)
        mode = stat.S_IFMT(member.external_attr >> 16)
        allowed = {0, stat.S_IFDIR} if member.is_dir() else {0, stat.S_IFREG}
        if mode not in allowed or member.flag_bits & 1:
            raise ValueError("distribution archive member is not regular")
        if member.is_dir() and member.file_size:
            raise ValueError("distribution archive directory contains file data")
        expanded += member.file_size
        if expanded > _MAX_EXPANDED_BYTES:
            raise ValueError("distribution archive exceeds expanded byte bound")
        if path.parts[0].endswith(".dist-info"):
            directories.add(path.parts[0])
        if not member.is_dir():
            files[name] = member
    if len(directories) != 1:
        raise ValueError("wheel requires one metadata directory")
    directory = directories.pop()
    _directory_identity(directory[: -len(".dist-info")], project, version)
    metadata_name = directory + "/METADATA"
    record_name = directory + "/RECORD"
    if not {metadata_name, record_name, directory + "/WHEEL"} <= files.keys():
        raise ValueError("wheel metadata, WHEEL or RECORD is missing")
    if files[metadata_name].file_size > _MAX_METADATA_BYTES:
        raise ValueError("distribution metadata exceeds byte bound")
    _metadata_identity(archive.read(files[metadata_name]), project, version)
    if files[record_name].file_size > _MAX_RECORD_BYTES:
        raise ValueError("wheel RECORD exceeds byte bound")
    raw_record = archive.read(files[record_name]).decode("utf-8")
    rows: dict[str, tuple[str, str]] = {}
    for row in csv.reader(io.StringIO(raw_record, newline=""), strict=True):
        if len(row) != 3:
            raise ValueError("wheel RECORD row is malformed")
        name, checksum, size = row
        if str(_member_name(name)) != name or name in rows:
            raise ValueError("wheel RECORD member is duplicate or not canonical")
        rows[name] = checksum, size
    signatures = {directory + "/RECORD.jws", directory + "/RECORD.p7s"}
    if set(rows) != set(files) - (signatures - set(rows)):
        raise ValueError("wheel RECORD does not account for every file")
    if rows.get(record_name) != ("", ""):
        raise ValueError("wheel RECORD must leave its own hash and size empty")
    for name, (checksum, size) in rows.items():
        if name == record_name:
            continue
        if not re.fullmatch(r"[0-9]+", size) or int(size) != files[name].file_size:
            raise ValueError("wheel RECORD size does not match member")
        algorithm, separator, expected = checksum.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z0-9_-]+", expected):
            raise ValueError("wheel RECORD hash is malformed")
        if algorithm not in _RECORD_ALGORITHMS:
            raise ValueError("wheel RECORD hash algorithm is unsupported or too weak")
        try:
            hasher = hashlib.new(algorithm)
        except ValueError as error:
            raise ValueError("wheel RECORD hash algorithm is unsupported") from error
        if hasher.digest_size < 32:
            raise ValueError("wheel RECORD hash algorithm is too weak")
        with archive.open(files[name]) as member_source:
            while chunk := member_source.read(1024**2):
                hasher.update(chunk)
        actual = base64.urlsafe_b64encode(hasher.digest()).rstrip(b"=").decode("ascii")
        if actual != expected:
            raise ValueError("wheel RECORD hash does not match member")


def _sdist(archive: tarfile.TarFile, project: str, version: str) -> None:
    seen = set()
    roots = set()
    expanded = 0
    metadata: bytes | None = None
    for member in archive:
        path = _member_name(member.name)
        name = str(path)
        if name in seen:
            raise ValueError("duplicate distribution archive member")
        seen.add(name)
        if len(seen) > _MAX_MEMBERS:
            raise ValueError("distribution archive exceeds member bound")
        if not member.isfile() and not member.isdir():
            raise ValueError("distribution archive member is not regular")
        if member.isdir() and member.size:
            raise ValueError("distribution archive directory contains file data")
        if member.size < 0:
            raise ValueError("distribution archive member size is invalid")
        expanded += member.size
        if expanded > _MAX_EXPANDED_BYTES:
            raise ValueError("distribution archive exceeds expanded byte bound")
        roots.add(path.parts[0])
        if len(roots) != 1:
            raise ValueError("source distribution requires one confined root")
        if len(path.parts) == 2 and path.name == "PKG-INFO":
            if not member.isfile() or member.size > _MAX_METADATA_BYTES:
                raise ValueError("distribution metadata is not a bounded regular file")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("source distribution metadata cannot be read")
            with source:
                metadata = source.read(_MAX_METADATA_BYTES + 1)
    if len(roots) != 1 or metadata is None:
        raise ValueError("source distribution PKG-INFO is missing")
    _directory_identity(roots.pop(), project, version)
    _metadata_identity(metadata, project, version)


def assert_distribution_archive(path: Path, project: str, version: str) -> None:
    """Bind actual metadata and file records without extracting or executing code.

    Wheel file hashes cover all members except optional RECORD signatures, whose
    cryptographic authority is not evaluated here. Archive inspection is bounded
    to 100,000 members and 2 GiB expanded bytes, 1 MiB identity metadata and
    16 MiB RECORD. These checks do not install or qualify package behavior.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError("distribution artifact is not a regular staged file")
    try:
        if path.name.endswith(".whl"):
            with zipfile.ZipFile(path) as wheel:
                _wheel(wheel, project, version)
        elif path.name.endswith(".tar.gz"):
            with tarfile.open(path, "r:gz") as sdist:
                _sdist(sdist, project, version)
        else:
            raise ValueError("unsupported distribution archive")
    except (zipfile.BadZipFile, tarfile.TarError, UnicodeError, csv.Error) as error:
        raise ValueError("distribution archive or metadata is malformed") from error
