"""Bounded official source retrieval, literal-link custody and immutable guide identity."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit

PAGE = "https://www.slu.se/en/about-slu/organisation/departments/forest-resource-management/miljoanalys/nfi/our-data/"
PDF = "https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf"
RETAINED = "docs/report/validation/empd2-nfi-pairing/inputs/slu-calibration-guide.pdf"
PDF_SHA = "793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8"
PDF_BYTES = 136339
PAGE_LIMIT = 2097152
PDF_LIMIT = 262144
REDIRECT_LIMIT = 3
HEADER_LIMIT = 65536


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_absolute()
        and path.resolve() == path
        and path.is_file()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical source file required",
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def read(path: Path) -> Any:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        value = {}
        for key, item in rows:
            require(key not in value, "Duplicate JSON key")
            value[key] = item
        return value

    value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    json.dumps(value, allow_nan=False)
    return value


def dump(path: Path, value: Any) -> None:
    require(
        not path.exists() and not any(p.is_symlink() for p in (path, *path.parents)),
        "Exclusive physical output required",
    )
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def utc() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def https_url(value: str) -> str:
    require(
        isinstance(value, str) and not any(ord(c) < 33 or ord(c) == 127 for c in value),
        "Unsafe source URL",
    )
    parsed = urlsplit(value)
    require(
        parsed.scheme == "https"
        and parsed.hostname in {"slu.se", "www.slu.se"}
        and parsed.username is None
        and parsed.password is None
        and parsed.port in (None, 443)
        and not parsed.fragment
        and not parsed.query
        and parsed.path.startswith("/"),
        "Only official HTTPS SLU source URLs are admitted",
    )
    return value


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, Any]] = []
        self.active: dict[str, Any] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        require(self.active is None, "Nested source anchor")
        names = [name for name, _ in attrs]
        require(len(names) == len(set(names)), "Duplicate anchor attribute")
        values = dict(attrs)
        self.active = {
            "literal_href": values.get("href"),
            "raw_start_tag": self.get_starttag_text(),
            "line": self.getpos()[0],
            "column": self.getpos()[1],
            "label": "",
        }

    def handle_data(self, text: str) -> None:
        if self.active is not None:
            self.active["label"] += text

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.active is not None:
            self.links.append(self.active)
            self.active = None


def literal_pdf_link(body: bytes, final_page_url: str) -> dict[str, Any]:
    https_url(final_page_url)
    require(0 < len(body) <= PAGE_LIMIT, "Official page byte budget")
    parser = Links()
    parser.feed(body.decode("utf-8", errors="strict"))
    parser.close()
    found = []
    for link in parser.links:
        href = link["literal_href"]
        if not isinstance(href, str):
            continue
        resolved = urljoin(final_page_url, href)
        if resolved == PDF:
            https_url(resolved)
            require(
                href in {PDF, urlsplit(PDF).path},
                "Official PDF href must remain literal absolute or root-relative",
            )
            found.append({**link, "resolved_url": resolved})
    require(bool(found), "Official page does not literally link the exact guide")
    return {"page_url": final_page_url, "matches": found, "resolved_pdf_url": PDF}


def guide_bytes(raw: bytes, retained: bytes) -> None:
    require(
        len(raw) == PDF_BYTES
        and raw.startswith(b"%PDF-")
        and hashlib.sha256(raw).hexdigest() == PDF_SHA,
        "Current official PDF differs from the sealed retained guide",
    )
    require(raw == retained, "Current and retained guide raw bytes differ")


def response_headers(rows: list[tuple[str, str]], kind: str) -> None:
    require(
        sum(len(k) + len(v) for k, v in rows) <= HEADER_LIMIT, "Response header budget"
    )
    values: dict[str, list[str]] = {}
    for key, value in rows:
        values.setdefault(key.lower(), []).append(value)
    for name in ["content-type", "content-length", "content-encoding"]:
        require(len(values.get(name, [])) <= 1, "Ambiguous HTTP response header")
    require(
        values.get("content-encoding", ["identity"])[0].lower() == "identity",
        "Encoded HTTP response refused",
    )
    media = values.get("content-type", [""])[0].split(";", 1)[0].strip().lower()
    require(
        media
        in (
            {"text/html", "application/xhtml+xml"}
            if kind == "page"
            else {"application/pdf"}
        ),
        "Official response content type differs",
    )
    if "content-length" in values:
        length = int(values["content-length"][0])
        require(
            0 < length <= (PAGE_LIMIT if kind == "page" else PDF_LIMIT),
            "Declared response byte budget",
        )


def validate_response(
    record: dict[str, Any], request_url: str, body: bytes, kind: str
) -> None:
    require(record["requested_url"] == request_url, "Official request URL differs")
    https_url(record["final_url"])
    require(
        type(record["status"]) is int and record["status"] == 200,
        "Official HTTP response not200",
    )
    response_headers([tuple(row) for row in record["headers"]], kind)
    limit = PAGE_LIMIT if kind == "page" else PDF_LIMIT
    require(
        0 < len(body) <= limit
        and type(record["bytes"]) is int
        and record["bytes"] == len(body)
        and record["sha256"] == hashlib.sha256(body).hexdigest(),
        "Official response body identity differs",
    )
    require(len(record["redirects"]) <= REDIRECT_LIMIT, "Redirect budget")
    current = request_url
    for hop in record["redirects"]:
        require(
            hop["from_url"] == current
            and type(hop["status"]) is int
            and hop["status"] in [301, 302, 303, 307, 308],
            "Redirect chain differs",
        )
        current = https_url(urljoin(current, hop["literal_location"]))
        require(current == hop["to_url"], "Redirect resolution differs")
    require(
        current == record["final_url"], "Final response URL is not linked to request"
    )
    declared_length = [
        value for key, value in record["headers"] if key.lower() == "content-length"
    ]
    require(
        not declared_length or int(declared_length[0]) == len(body),
        "Declared and observed response lengths differ",
    )
    start = datetime.fromisoformat(record["started_UTC"])
    end = datetime.fromisoformat(record["completed_UTC"])
    require(
        start.utcoffset() == end.utcoffset() == UTC.utcoffset(start) and start <= end,
        "UTC request chronology differs",
    )
