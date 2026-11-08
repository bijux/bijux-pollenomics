"""Exact reader routes and identities delegated to existing publication owners."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
from typing import Any, cast
from urllib.parse import urlsplit

PREFIX = "/bijux-pollenomics/"
SITE_URL = "https://bijux.io" + PREFIX
SITE = "artifacts/docs/site"
ENTRY = "public/pollenomics/science/"
ROUTES = tuple(
    "public/pollenomics/science/" + name + "/"
    for name in ("glossary", "papers", "sources", "results", "downloads")
) + (
    "public/pollenomics/interfaces/atlas-walkthrough/",
    "public/pollenomics/operations/installation-and-setup/",
)
DATA = tuple(
    "report/regions/nordic/author-target-pollen/" + name
    for name in ("input-manifest.json", "coverage.csv", "scores.csv")
)
LIMIT = 16 * 1024 * 1024


def require(condition: object, message: str) -> None:
    """Refuse incomplete observations rather than certify a partial journey."""
    if not condition:
        raise ValueError(message)


def read_regular(root: Path, relative: str) -> bytes:
    """Read a bounded regular file without traversing symbolic source paths."""
    require(
        root.is_dir() and not root.is_symlink(), "reader root is missing or symbolic"
    )
    path = PurePosixPath(relative)
    require(
        bool(path.parts)
        and not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == relative
        and not any(c in relative for c in "\\\0?#"),
        "reader path must be canonical and confined",
    )
    current = root
    for part in path.parts:
        current /= part
        require(not current.is_symlink(), "reader path is symbolic")
    require(
        current.is_file() and current.stat().st_size <= LIMIT,
        "reader file missing or oversized",
    )
    return current.read_bytes()


def identity(content: bytes) -> dict[str, object]:
    """Keep numerical download contents opaque; only authenticate their bytes."""
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def download_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Consume the existing twelve-PDF owner without a second registry."""
    rows = manifest.get("files", [])
    require(
        manifest.get("schema_version") == "scientific-reader-downloads.v1",
        "PDF owner schema differs",
    )
    require(isinstance(rows, list) and len(rows) == 12, "PDF owner population differs")
    paths = [row["site_uri"] for row in rows]
    require(len(set(paths)) == 12, "PDF routes are duplicated")
    require(
        sum(path.startswith("assets/science/papers/") for path in paths) == 9
        and sum(path.startswith("assets/science/presentations/") for path in paths)
        == 3,
        "PDF roles differ",
    )
    for row in rows:
        require(
            row["site_uri"].endswith(".pdf")
            and isinstance(row["bytes"], int)
            and row["bytes"] > 0
            and isinstance(row["sha256"], str)
            and len(row["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in row["sha256"]),
            "PDF identity is malformed",
        )
    return cast(list[dict[str, Any]], rows)


def verify_receipt(plan: dict[str, Any], receipt: dict[str, Any]) -> None:
    """Require every viewport, clicked route, response identity and error channel."""
    require(
        receipt.get("status") == "PASS"
        and receipt.get("candidate") == plan["candidate"],
        "browser candidate or status differs",
    )
    require(
        receipt.get("errors") == [],
        "browser reported page, console or resource failures",
    )
    require(
        isinstance(receipt.get("browser"), dict) and receipt["browser"].get("product"),
        "browser version absent",
    )
    origin = receipt.get("local_origin", "")
    parsed = urlsplit(origin)
    require(
        parsed.scheme == "http"
        and parsed.hostname == "127.0.0.1"
        and parsed.port is not None
        and not parsed.path
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None,
        "local browser origin differs",
    )
    observations = receipt.get("viewports", [])
    require(
        [row.get("width") for row in observations] == [1440, 390],
        "viewport population differs",
    )
    expected = {
        row["path"]: {k: row[k] for k in ("bytes", "sha256")}
        for row in plan["downloads"]
    }
    for row in observations:
        require(
            row.get("entry") == ENTRY
            and row.get("entry_heading")
            and row.get("entry_overflow") is False,
            "scientific entry missing",
        )
        routes = row.get("routes", [])
        require(
            [item.get("path") for item in routes] == list(ROUTES),
            "clicked route population differs",
        )
        require(
            all(
                item.get("clicked") is True
                and item.get("heading")
                and item.get("overflow") is False
                for item in routes
            ),
            "reader route is unusable",
        )
        require(
            all(item.get("url") == origin + PREFIX + item["path"] for item in routes),
            "reader URL escaped production prefix",
        )
        downloads = row.get("downloads", [])
        require(
            len(downloads) == len(expected)
            and len({item.get("path") for item in downloads}) == len(expected),
            "download population differs",
        )
        require(
            {
                item.get("path"): {k: item.get(k) for k in ("bytes", "sha256")}
                for item in downloads
            }
            == expected,
            "browser download identity differs",
        )
        require(
            all(
                item.get("url") == origin + PREFIX + item["path"] for item in downloads
            ),
            "download URL escaped production prefix",
        )
        require(
            all(
                item.get("status") == 200
                and item.get("from_rendered_anchor") is True
                and item.get("clickable") is True
                for item in downloads
            ),
            "download lacks a successful rendered-link response",
        )
