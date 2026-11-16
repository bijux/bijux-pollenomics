"""Attach complete annotation releases while preserving prior and foreign trees."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import ExitStack
import json
import os
from pathlib import Path
import secrets
from typing import Any

from ....core.errors.cleanup import add_cleanup_note
from ....core.filesystem import BoundedInputTree, DirectoryAnchor, OwnedTreeWriter
from ....core.filesystem.namespaces import validate_regular_namespace
from ....core.filesystem.recovery_storage import resolve_publication_workspace_parent
from ....core.filesystem.replacement import publish_owned_replacement

MANIFEST_MAX_BYTES = 16 * 1024 * 1024


class ManifestOutput:
    """Keep a JSON callback on one private file descriptor, not its mutable name.

    The supplied kernel capability supports the existing two-argument writer;
    callbacks must honor that capability rather than resolve a new path. Its
    basename/suffix are not a release filename compatibility contract.
    """

    def __init__(self, control: DirectoryAnchor) -> None:
        """Allocate and verify the capability before any annotation acquisition."""
        self.control = control
        self.fd = os.open(
            "manifest.json",
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=control.fd,
        )
        self.called = False
        self.identity = os.fstat(self.fd)
        self.path = Path("/dev/fd") / str(self.fd)
        try:
            duplicate = os.open(self.path, os.O_RDWR)
            try:
                if (os.fstat(duplicate).st_dev, os.fstat(duplicate).st_ino) != (
                    self.identity.st_dev,
                    self.identity.st_ino,
                ):
                    raise ValueError("AADR manifest descriptor capability differs")
            finally:
                os.close(duplicate)
        except BaseException:
            os.close(self.fd)
            raise

    def capture(self, write: Callable[[Path, object], None], payload: object) -> bytes:
        """Invoke one writer and capture its finite, unchanged ordinary output."""
        if self.called:
            raise ValueError("AADR manifest callback was already invoked")
        self.called = True
        write(self.path, payload)
        node = os.fstat(self.fd)
        if (node.st_dev, node.st_ino, node.st_nlink) != (
            self.identity.st_dev,
            self.identity.st_ino,
            1,
        ) or node.st_size > MANIFEST_MAX_BYTES:
            raise ValueError("AADR manifest callback output exceeds its source seal")
        os.lseek(self.fd, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        count = 0
        while True:
            block = os.read(self.fd, min(1024 * 1024, node.st_size + 1 - count))
            if not block:
                break
            count += len(block)
            if count > node.st_size:
                raise ValueError("AADR manifest callback output grew during capture")
            chunks.append(block)
        after = os.fstat(self.fd)
        attached = os.stat(
            "manifest.json", dir_fd=self.control.fd, follow_symlinks=False
        )

        def stamp(item: os.stat_result) -> tuple[int, ...]:
            return (
                item.st_dev,
                item.st_ino,
                item.st_mode,
                item.st_nlink,
                item.st_size,
                item.st_mtime_ns,
                item.st_ctime_ns,
            )

        if (
            count != node.st_size
            or stamp(after) != stamp(node)
            or stamp(attached) != stamp(node)
        ):
            raise ValueError("AADR manifest callback output identity changed")
        self.control.check()
        return b"".join(chunks)

    def close(self) -> None:
        """Release the capability without deleting any retained control bytes."""
        os.close(self.fd)


def json_document(raw: bytes) -> Any:
    """Decode one finite JSON document without ambiguous duplicate keys."""

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("AADR release manifest contains a duplicate key")
            result[key] = value
        return result

    result = json.loads(raw, object_pairs_hook=pairs)
    json.dumps(result, allow_nan=False)
    return result


def release_namespace(root: Path, names: set[str], max_asset_bytes: int) -> None:
    """Refuse foreign names and aliases before reading any release body."""
    validate_regular_namespace(
        root,
        names | {"release_manifest.json"},
        max_files=len(names) + 1,
        max_bytes=max_asset_bytes * len(names) + MANIFEST_MAX_BYTES,
    )


def _prior_owned(prior: BoundedInputTree, version: str, names: set[str]) -> None:
    manifest = json_document(
        prior.read(prior.root / "release_manifest.json", max_bytes=MANIFEST_MAX_BYTES)
    )
    if not isinstance(manifest, dict):
        raise ValueError("Prior AADR release manifest must be an object")
    recorded = manifest.get("downloaded_files")
    entries = manifest.get("anno_files")
    if (
        manifest.get("source") != "AADR"
        or manifest.get("requested_version") != version
        or not isinstance(recorded, list)
        or any(not isinstance(name, str) for name in recorded)
        or len(recorded) != len(names)
        or set(recorded) != names
        or not isinstance(entries, list)
        or len(entries) != len(names)
    ):
        raise ValueError("Prior destination is not the declared AADR release")
    declared: set[str] = set()
    for entry in entries:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("dataset_name"), str)
            or not isinstance(entry.get("filename"), str)
            or type(entry.get("file_id")) is not int
            or entry["file_id"] <= 0
        ):
            raise ValueError("Prior AADR release source declaration is invalid")
        declared.add(entry["dataset_name"] + "/" + entry["filename"])
    if declared != names:
        raise ValueError("Prior AADR release contains foreign source members")
    prior.validate()


def _retention_note(error: BaseException, run: DirectoryAnchor) -> None:
    try:
        run.check()
    except (OSError, ValueError):
        add_cleanup_note(
            error,
            lambda: (
                f"AADR recovery originally allocated at {run.path}; expected directory "
                f"identity {run.identity}; current location unverified"
            ),
        )
    else:
        add_cleanup_note(error, lambda: f"AADR recovery state retained at {run.path}")


def publish_release(
    output_root: Path,
    version: str,
    *,
    names: set[str],
    max_asset_bytes: int,
    build: Callable[[OwnedTreeWriter, ManifestOutput], None],
    validate: Callable[[Path], None],
) -> None:
    """Stage all members and attach only a closed, validated source release.

    Recovery remains outside the entire declared collection. Publication uses
    same-volume no-replace attachment; native failures retain predecessor and
    candidate bytes without claiming crash durability or inode compare-and-swap.
    """
    output_root = Path(output_root).absolute()
    final = output_root / version
    limit = max_asset_bytes * len(names) + MANIFEST_MAX_BYTES
    with ExitStack() as stack:
        parent = stack.enter_context(DirectoryAnchor(output_root, create=True))
        prior = None
        if os.path.lexists(final):
            release_namespace(final, names, max_asset_bytes)
            prior = stack.enter_context(
                BoundedInputTree(
                    final,
                    max_bytes=limit,
                    max_files=len(names) + 1,
                    member_limits={
                        "release_manifest.json": MANIFEST_MAX_BYTES,
                        **dict.fromkeys(names, max_asset_bytes),
                    },
                )
            )
            _prior_owned(prior, version, names)
        storage_path = resolve_publication_workspace_parent(
            output_root, namespace="aadr-release-publication"
        )
        storage = stack.enter_context(DirectoryAnchor(storage_path, create=True))
        parent.check()
        token = "release-" + secrets.token_hex(16)
        os.mkdir(token, 0o700, dir_fd=storage.fd)
        run = stack.enter_context(DirectoryAnchor(storage.path / token))
        os.mkdir("control", 0o700, dir_fd=run.fd)
        control = stack.enter_context(DirectoryAnchor(run.path / "control"))
        manifest_output = ManifestOutput(control)
        stack.callback(manifest_output.close)
        receipts = stack.enter_context(
            OwnedTreeWriter(run.path / "receipts", max_bytes=64 * 1024, max_files=4)
        )

        def record(status: str, fields: dict[str, Any]) -> None:
            run.check()
            receipts.write_bytes(
                status + ".json",
                json.dumps(
                    {
                        "status": status,
                        "destination": str(final),
                        "publication_root": str(output_root),
                        "recovery_root": str(run.path),
                        **fields,
                    },
                    allow_nan=False,
                    sort_keys=True,
                ).encode(),
            )

        try:
            record("prepared", {"prior_present": prior is not None})
            writer = stack.enter_context(
                OwnedTreeWriter(
                    run.path / "candidate", max_bytes=limit, max_files=len(names) + 1
                )
            )
            build(writer, manifest_output)
            control.check()
            parent.check()

            def verify(root: Path) -> None:
                parent.check()
                run.check()
                validate(root)
                parent.check()
                run.check()

            publish_owned_replacement(
                writer,
                final=final,
                prior=prior,
                recovery=run,
                validate=verify,
                record=record,
            )
            parent.check()
            run.check()
        except BaseException as primary:
            try:
                record("failed-operation", {"error_type": type(primary).__name__})
            except Exception as receipt_error:

                def receipt_note(failure: Exception = receipt_error) -> str:
                    return "AADR refusal receipt failed: " + type(failure).__name__

                add_cleanup_note(primary, receipt_note)
            _retention_note(primary, run)
            raise
