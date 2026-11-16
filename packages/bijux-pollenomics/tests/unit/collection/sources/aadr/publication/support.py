"""Generated annotation bytes exercise release publication without transport."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import md5
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.aadr.download import download_aadr_anno_files
from bijux_pollenomics.collection.sources.aadr.models import AadrAnnoDownloadReport

NAMES = ("1240k/v66.1240K.aadr.PUB.anno", "ho/v66.HO.aadr.PUB.anno")


def metadata(values: tuple[bytes, bytes]) -> dict[str, object]:
    """Declare two native source identities for tiny generated payloads."""
    return {
        "data": [
            {
                "files": [
                    {
                        "dataFile": {
                            "filename": Path(name).name,
                            "id": index + 1,
                            "filesize": len(value),
                            "md5": md5(value, usedforsecurity=False).hexdigest(),
                        }
                    }
                    for index, (name, value) in enumerate(
                        zip(NAMES, values, strict=True)
                    )
                ]
            }
        ]
    }


def publish(
    root: Path,
    values: tuple[bytes, bytes],
    *,
    fetch: Callable[..., bytes] | None = None,
    write: Callable[[Path, object], None] | None = None,
) -> AadrAnnoDownloadReport:
    """Call the existing injected public boundary with generated source bytes."""

    def fetched(url: str, **kwargs: Any) -> bytes:
        assert kwargs["insecure"] is False
        return values[int(url.rsplit("/", 1)[1]) - 1]

    def written(path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

    return download_aadr_anno_files(
        root,
        "v66",
        fetch_binary_fn=fetch or fetched,
        fetch_release_history_metadata_fn=lambda: metadata(values),
        write_json_fn=write or written,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    """Retain every generated regular member for exact prior-state assertions."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }
