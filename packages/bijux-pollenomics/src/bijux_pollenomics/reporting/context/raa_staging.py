"""Own and verify the complete RAÄ publication subtree before exposing links."""

from __future__ import annotations

import json
import os
import secrets
from collections.abc import Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

from ...collection.contracts.artifacts import RAA_DENSITY_GEOJSON, RAA_LAYER_METADATA
from ...collection.sources.raa.density_membership import semantic_payload_sha256
from ...collection.sources.raa.inventory import decode_source_object
from ...core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    publish_owned_replacement,
)
from ...core.filesystem.recovery_storage import resolve_publication_workspace_parent
from .raa import (
    RAA_ATLAS_INPUT_STATUS_FILENAME,
    RAA_ATLAS_INPUT_STATUS_LABEL,
    RAA_CONTEXT_RELATIVE_DIRECTORY,
    RaaAtlasInputSnapshot,
)

_MANIFEST = "publication_manifest.json"
_LIMITS = {
    RAA_LAYER_METADATA.filename: 1024 * 1024,
    RAA_DENSITY_GEOJSON.filename: 1024 * 1024,
    RAA_ATLAS_INPUT_STATUS_FILENAME: 1024 * 1024,
    _MANIFEST: 64 * 1024,
}
_TREE_MAX_BYTES = sum(_LIMITS.values())
_SCHEMA = "raa-context-publication-v1"
_LABELS = {
    RAA_LAYER_METADATA.filename: RAA_LAYER_METADATA.label,
    RAA_DENSITY_GEOJSON.filename: RAA_DENSITY_GEOJSON.label,
    RAA_ATLAS_INPUT_STATUS_FILENAME: RAA_ATLAS_INPUT_STATUS_LABEL,
    _MANIFEST: "RAÄ context publication receipt",
}


def _buffers(snapshot: RaaAtlasInputSnapshot) -> dict[str, bytes]:
    status = snapshot.status()
    geometry = status.get("geometry_publication")
    publish = isinstance(geometry, dict) and geometry.get("default_enabled") is True
    result = {RAA_ATLAS_INPUT_STATUS_FILENAME: snapshot.status_bytes}
    if publish:
        if snapshot.metadata_bytes is None or snapshot.density_bytes is None:
            raise ValueError("RAÄ publication requires captured normalized buffers")
        result[RAA_LAYER_METADATA.filename] = snapshot.metadata_bytes
        result[RAA_DENSITY_GEOJSON.filename] = snapshot.density_bytes
    manifest = {
        "schema_version": _SCHEMA,
        "input_epoch": "captured_buffers",
        "inputs": status["inputs"],
        "files": {
            name: {"sha256": sha256(raw).hexdigest(), "byte_count": len(raw)}
            for name, raw in result.items()
        },
    }
    result[_MANIFEST] = json.dumps(manifest, indent=2, ensure_ascii=False).encode(
        "utf-8"
    )
    if any(
        type(raw) is not bytes or len(raw) > _LIMITS[name]
        for name, raw in result.items()
    ):
        raise ValueError("RAÄ publication exceeds its immutable-buffer byte budget")
    return result


def _validate_output(root: Path, expected: Mapping[str, bytes] | None = None) -> None:
    with BoundedInputTree(
        root, max_bytes=_TREE_MAX_BYTES, max_files=4, member_limits=_LIMITS
    ) as tree:
        if set(tree.directories) != {""} or _MANIFEST not in tree.files:
            raise ValueError("RAÄ publication is not a recognized closed subtree")
        manifest_raw = tree.read(root / _MANIFEST, max_bytes=_LIMITS[_MANIFEST])
        manifest = decode_source_object(manifest_raw.decode("utf-8"))
        records = manifest.get("files")
        if (
            set(manifest) != {"schema_version", "input_epoch", "inputs", "files"}
            or manifest.get("schema_version") != _SCHEMA
            or manifest.get("input_epoch") != "captured_buffers"
            or not isinstance(manifest.get("inputs"), dict)
            or not isinstance(records, dict)
        ):
            raise ValueError("RAÄ publication manifest profile is unsupported")
        if (
            RAA_ATLAS_INPUT_STATUS_FILENAME not in records
            or not set(records) <= set(_LIMITS) - {_MANIFEST}
            or set(tree.files) != {*records, _MANIFEST}
        ):
            raise ValueError(
                "RAÄ publication member set differs from its literal profile"
            )
        normalized = {RAA_LAYER_METADATA.filename, RAA_DENSITY_GEOJSON.filename}
        if set(records).intersection(normalized) not in (set(), normalized):
            raise ValueError("RAÄ publication requires a complete normalized pair")
        buffers = {_MANIFEST: manifest_raw}
        for name in records:
            if name not in _LIMITS:
                raise ValueError("RAÄ publication contains a foreign member")
            raw = tree.read(root / name, max_bytes=_LIMITS[name])
            buffers[name] = raw
            record = records[name]
            actual = {"sha256": sha256(raw).hexdigest(), "byte_count": len(raw)}
            if not isinstance(record, dict) or semantic_payload_sha256(
                record
            ) != semantic_payload_sha256(actual):
                raise ValueError("RAÄ publication bytes differ from their receipt")
        status = decode_source_object(
            buffers[RAA_ATLAS_INPUT_STATUS_FILENAME].decode("utf-8")
        )
        if (
            status.get("schema_version") != "raa-atlas-input-status.v1"
            or status.get("source_family") != "raa"
            or status.get("inputs") != manifest["inputs"]
        ):
            raise ValueError("RAÄ prior publication status is unrecognized")
        if expected is not None and (
            set(buffers) != set(expected)
            or any(raw != expected[name] for name, raw in buffers.items())
        ):
            raise ValueError("RAÄ staged bytes differ from the captured snapshot")
        tree.validate()


@dataclass(frozen=True)
class RaaOwnedPublication:
    """A live output capability, retained until the caller finishes its layer."""

    writer: OwnedTreeWriter
    directory: Path
    expected: Mapping[str, bytes]
    receipt_path: Path

    def validate(self) -> None:
        """Verify original output identities and the exact expected byte buffers."""
        self.writer.validate_closed_attachment(self.directory)
        _validate_output(self.directory, self.expected)
        self.writer.validate_closed_attachment(self.directory)

    def artifacts(self) -> list[tuple[str, str]]:
        """Link only the closed verified publication members."""
        return [
            (_LABELS[name], (RAA_CONTEXT_RELATIVE_DIRECTORY / name).as_posix())
            for name in self.expected
        ]


def _receipt_bytes(payload: dict[str, object]) -> bytes:
    raw = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    if len(raw) > 64 * 1024:
        raise ValueError("RAÄ private publication receipt exceeds its byte budget")
    return raw


@contextmanager
def stage_raa_publication(
    *, snapshot: RaaAtlasInputSnapshot, output_dir: Path
) -> Iterator[RaaOwnedPublication]:
    """Keep candidates and predecessors outside the entire public report root."""
    expected = _buffers(snapshot)
    output_root = Path(output_dir).absolute()
    workspace_parent = resolve_publication_workspace_parent(
        output_root, namespace="raa-publication"
    )
    with (
        DirectoryAnchor(output_root) as output,
        DirectoryAnchor(workspace_parent, create=True) as private,
        ExitStack() as stack,
    ):
        if (
            workspace_parent.is_relative_to(output_root)
            or private.identity == output.identity
            or os.fstat(private.fd).st_dev != os.fstat(output.fd).st_dev
        ):
            raise ValueError("RAÄ recovery requires external same-volume storage")
        operation = stack.enter_context(
            OwnedTreeWriter(
                workspace_parent / secrets.token_hex(16),
                max_bytes=128 * 1024,
                max_files=2,
            )
        )
        receipt_path = operation.root / "operation.json"
        candidate_path, recovery_path = (
            operation.root / "candidate",
            operation.root / "recovery",
        )
        events: list[dict[str, object]] = []
        try:
            operation.write_bytes(
                "operation.json",
                _receipt_bytes(
                    {
                        "schema_version": "raa-publication-operation-v1",
                        "publication_root": str(output_root),
                        "candidate": str(candidate_path),
                        "recovery": str(recovery_path),
                        "expected_files": {
                            name: {
                                "sha256": sha256(raw).hexdigest(),
                                "byte_count": len(raw),
                            }
                            for name, raw in expected.items()
                        },
                    }
                ),
            )
            writer = stack.enter_context(
                OwnedTreeWriter(candidate_path, max_bytes=_TREE_MAX_BYTES, max_files=4)
            )
            recovery_owner = stack.enter_context(
                OwnedTreeWriter(recovery_path, max_bytes=1, max_files=1)
            )
            recovery = stack.enter_context(DirectoryAnchor(recovery_path))
            for name, raw in expected.items():
                writer.write_bytes(name, raw)
            publication = RaaOwnedPublication(
                writer, candidate_path, MappingProxyType(expected), receipt_path
            )
            publication.validate()
            parent = stack.enter_context(
                DirectoryAnchor(output_root / "context", create=True)
            )
            final = output_root / "context/raa"
            prior = None
            if final.exists() or final.is_symlink():
                prior = stack.enter_context(
                    BoundedInputTree(
                        final,
                        max_bytes=_TREE_MAX_BYTES,
                        max_files=4,
                        member_limits=_LIMITS,
                    )
                )
                _validate_output(final)
                prior.validate()
            # Caller builds its layer from captured bytes while this candidate is private.
            yield publication
            publication.validate()
            output.check()
            private.check()
            operation.validate_attachment()
            recovery_owner.validate_attachment()
            parent.check()

            def record(event: str, payload: dict[str, object]) -> None:
                events.append({"event": event, **payload})
                if event == "published":
                    operation.write_bytes(
                        "terminal.json",
                        _receipt_bytes(
                            {
                                "status": "published",
                                "events": events,
                                "operation_receipt": str(receipt_path),
                            }
                        ),
                    )

            publish_owned_replacement(
                writer,
                final=final,
                prior=prior,
                recovery=recovery,
                validate=lambda path: _validate_output(path, expected),
                record=record,
            )
            writer.validate_closed_attachment(final)
            _validate_output(final, expected)
            writer.validate_closed_attachment(final)
            output.check()
            private.check()
            parent.check()
            operation.validate_attachment()
            recovery_owner.validate_attachment()
        except BaseException as error:
            try:
                operation.write_bytes(
                    "terminal.json",
                    _receipt_bytes(
                        {
                            "status": "refused",
                            "events": events,
                            "operation_receipt": str(receipt_path),
                            "error_type": type(error).__name__,
                        }
                    ),
                )
            except Exception as receipt_error:  # noqa: BLE001 - Preserve the primary failure.
                error.add_note(
                    f"RAÄ terminal receipt failed: {type(receipt_error).__name__}"
                )
            error.add_note(f"RAÄ retained operation receipt: {receipt_path}")
            raise
