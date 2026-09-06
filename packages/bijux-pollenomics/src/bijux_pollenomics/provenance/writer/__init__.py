"""Atomic repository-owned writer and CLI for canonical release evidence."""

from __future__ import annotations

import argparse as argparse
import json as json
import os as os
import secrets as secrets
import stat as stat
import sys as sys
from collections.abc import Callable as Callable
from collections.abc import Mapping as Mapping
from collections.abc import Sequence as Sequence
from contextlib import suppress as suppress
from pathlib import Path as Path
from pathlib import PurePosixPath as PurePosixPath
from typing import Literal as Literal
from typing import cast as cast

from ..release_evidence import ArtifactInput as ArtifactInput
from ..release_evidence import ArtifactReference as ArtifactReference
from ..release_evidence import ArtifactRole as ArtifactRole
from ..release_evidence import Blocker as Blocker
from ..release_evidence import CountReconciliation as CountReconciliation
from ..release_evidence import CountStatus as CountStatus
from ..release_evidence import GateResult as GateResult
from ..release_evidence import GateStatus as GateStatus
from ..release_evidence import ReconciliationDimension as ReconciliationDimension
from ..release_evidence import ReleaseEvidenceError as ReleaseEvidenceError
from ..release_evidence import (
    build_release_evidence_manifest as build_release_evidence_manifest,
)
from ..release_evidence import (
    validate_release_evidence_manifest as validate_release_evidence_manifest,
)
from .arguments import _parser as _parser
from .cli import main
from .codec import (
    _bool_field as _bool_field,
)
from .codec import (
    _canonical_bytes as _canonical_bytes,
)
from .codec import (
    _int_field as _int_field,
)
from .codec import (
    _list_field as _list_field,
)
from .codec import (
    _load_json as _load_json,
)
from .codec import (
    _mapping as _mapping,
)
from .codec import (
    _mapping_field as _mapping_field,
)
from .codec import (
    _optional_int_field as _optional_int_field,
)
from .codec import (
    _optional_string_field as _optional_string_field,
)
from .codec import (
    _string_field as _string_field,
)
from .codec import (
    _string_value as _string_value,
)
from .publication import _publish_canonical_document as _publish_canonical_document
from .reconciliation import _blocker as _blocker
from .reconciliation import _reconciliation as _reconciliation
from .repository import (
    _existing_repository_path as _existing_repository_path,
)
from .repository import (
    _fsync_directory as _fsync_directory,
)
from .repository import (
    _open_output_parent as _open_output_parent,
)
from .repository import (
    _read_regular_bytes as _read_regular_bytes,
)
from .repository import (
    _read_regular_bytes_at as _read_regular_bytes_at,
)
from .repository import (
    _read_repository_json as _read_repository_json,
)
from .repository import (
    _relative_parts as _relative_parts,
)
from .repository import (
    _repository_root as _repository_root,
)
from .repository import (
    _verify_output_parent as _verify_output_parent,
)
from .service import _validate_written_manifest as _validate_written_manifest
from .service import write_release_evidence_manifest, write_release_evidence_request
from .translation import (
    _artifact as _artifact,
)
from .translation import (
    _gate as _gate,
)
from .translation import (
    _parent as _parent,
)
from .translation import (
    _write_request as _write_request,
)

__all__ = [
    "main",
    "write_release_evidence_manifest",
    "write_release_evidence_request",
]
