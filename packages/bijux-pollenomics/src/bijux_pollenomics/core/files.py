from __future__ import annotations

import json
from pathlib import Path

from .filesystem import OwnedTreeWriter


def write_json(
    path: Path, payload: object, *, writer: OwnedTreeWriter | None = None
) -> None:
    """Write JSON with stable formatting."""
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False), writer=writer)


def write_text(
    path: Path, content: str, *, writer: OwnedTreeWriter | None = None
) -> None:
    """Write UTF-8 text content."""
    if writer is None:
        path.write_text(content, encoding="utf-8")
    else:
        writer.write_bytes(
            path.relative_to(writer.root).as_posix(), content.encode("utf-8")
        )
