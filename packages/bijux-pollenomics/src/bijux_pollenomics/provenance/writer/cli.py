"""Callable command-line orchestration for release evidence."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..release_evidence import ReleaseEvidenceError, validate_release_evidence_manifest
from .arguments import _parser
from .codec import (
    _bool_field,
    _canonical_bytes,
    _list_field,
    _mapping_field,
    _string_field,
)
from .repository import _read_repository_json
from .service import write_release_evidence_request
from .translation import _write_request


def main(argv: Sequence[str] | None = None) -> int:
    """Run the callable release-evidence writer or validation gate."""
    args = _parser().parse_args(argv)
    try:
        root = Path(args.repository_root)
        manifest: Mapping[str, object]
        if args.command == "request":
            generated_request = write_release_evidence_request(root, args.output)
            summary = {
                "artifact_count": len(_list_field(generated_request, "artifacts")),
                "gate_count": len(_list_field(generated_request, "gates")),
                "output": args.output,
                "reconciliation_count": len(
                    _list_field(generated_request, "reconciliations")
                ),
                "schema_version": _string_field(generated_request, "schema_version"),
            }
            sys.stdout.buffer.write(_canonical_bytes(summary))
            return 0
        if args.command == "write":
            request = _read_repository_json(root, args.request, require_artifacts=False)
            manifest = _write_request(root, args.output, request)
            output = args.output
        else:
            manifest = _read_repository_json(
                root, args.manifest, require_artifacts=True
            )
            validate_release_evidence_manifest(root, manifest)
            output = args.manifest
        decision = _mapping_field(manifest, "release_decision")
        release_ready = _bool_field(decision, "release_ready")
        summary = {
            "build_id": _string_field(manifest, "build_id"),
            "output": output,
            "release_ready": release_ready,
            "status": _string_field(decision, "status"),
        }
        sys.stdout.buffer.write(_canonical_bytes(summary))
        return 0 if release_ready else 1
    except (OSError, ReleaseEvidenceError, UnicodeError, json.JSONDecodeError) as error:
        print(f"release evidence refused: {error}", file=sys.stderr)
        return 2
