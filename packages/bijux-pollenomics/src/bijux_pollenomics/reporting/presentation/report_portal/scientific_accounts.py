"""Route scientific wrappers to their exact maintained claim accounts."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from typing import Any
from urllib.parse import quote

from .scientific_qualifications import (
    Qualification,
    parse_qualification,
    validate_authored_reader,
    validate_evidence,
)

BEGIN = "\n\n<!-- scientific-account-route:begin -->\n"
END = "<!-- scientific-account-route:end -->\n"
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


@dataclass(frozen=True)
class Account:
    """A canonical report and the exact qualified reading revision."""

    report_path: str
    source_sha256: str


@dataclass(frozen=True)
class Route:
    """An explicit scientific wrapper relationship, without scientific admission."""

    reader_path: str
    accounts: tuple[Account, ...]
    scope_reason: str
    qualification: Qualification | None = None


def _path(value: object, *, reader: bool) -> str:
    if not isinstance(value, str):
        raise ValueError("Scientific reading path must be text")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.suffix != ".md"
        or path.as_posix() != value
        or "\\" in value
        or any(ord(c) < 32 for c in value)
    ):
        raise ValueError("Scientific reading path escapes its Markdown scope")
    if reader and path.parts[:2] != ("docs", "report"):
        raise ValueError("Scientific wrapper must belong to docs/report")
    if not reader and path.parts[:2] not in {
        ("reports", "science"),
        ("docs", "report"),
    }:
        raise ValueError("Scientific account is outside its maintained scope")
    return value


def parse_routes(raw: str) -> dict[str, Route]:
    """Refuse duplicate readers, malformed paths and unbound account identities."""
    value: Any = json.loads(raw)
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != 1
        or not isinstance(value.get("routes"), list)
    ):
        raise ValueError("Scientific reading authority is invalid")
    result: dict[str, Route] = {}
    for item in value["routes"]:
        if not isinstance(item, dict):
            raise ValueError("Scientific reading route must be an object")
        reader = _path(item.get("reader_path"), reader=True)
        reason = item.get("scope_reason")
        accounts = item.get("canonical_accounts")
        if (
            reader in result
            or not isinstance(reason, str)
            or not reason.strip()
            or not isinstance(accounts, list)
            or not accounts
        ):
            raise ValueError("Scientific reading route is duplicated or incomplete")
        qualified: list[Account] = []
        for account in accounts:
            if not isinstance(account, dict):
                raise ValueError("Scientific reading account must be an object")
            source = _path(account.get("report_path"), reader=False)
            digest = account.get("source_sha256")
            if (
                source == reader
                or not isinstance(digest, str)
                or SHA256.fullmatch(digest) is None
                or source in {a.report_path for a in qualified}
            ):
                raise ValueError("Scientific reading account is duplicated or unbound")
            qualified.append(Account(source, digest))
        qualification = parse_qualification(item.get("qualification"))
        if qualification is not None and any(
            record.path == reader for record in qualification.evidence
        ):
            raise ValueError(
                "Scientific qualification cannot bind its own rendered hash"
            )
        result[reader] = Route(reader, tuple(qualified), reason, qualification)

    for route in result.values():
        if route.qualification is not None and any(
            pin.path in result for pin in route.qualification.evidence
        ):
            raise ValueError(
                "Scientific qualification cannot bind another rendered wrapper hash"
            )
    return result


def load_routes() -> dict[str, Route]:
    """Read packaged, explicitly reviewed scientific account relationships."""
    return parse_routes(
        files(__package__)
        .joinpath("scientific_accounts.json")
        .read_text(encoding="utf-8")
    )


def authored_reader(raw: bytes) -> bytes:
    """Preserve all original prose and reject ambiguous managed route markers."""
    text = raw.decode("utf-8")
    if "scientific-account-route:" not in text:
        return raw
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("Scientific account route markers are malformed")
    original, block = text.split(BEGIN)
    if not block.endswith(END):
        raise ValueError("Scientific account route must be terminal")
    return original.encode("utf-8")


def verified_authored_reader(raw: bytes, route: Route) -> bytes:
    """Compare generated prose only after authenticating its exact managed account."""
    expected = render_route(raw, route)
    if BEGIN.encode() in raw and raw != expected:
        raise ValueError("Scientific account route differs from its source authority")
    return authored_reader(raw)


def render_route(raw: bytes, route: Route) -> bytes:
    """Expose exact account links while retaining each wrapper's own denominator."""
    base = authored_reader(raw)
    if route.qualification is not None:
        validate_authored_reader(base, route.qualification)
    parent = posixpath.dirname(route.reader_path)
    lines = [
        "## Scientific verification and limits",
        "",
        route.scope_reason,
        "",
    ]
    if route.qualification is None:
        lines.extend(
            (
                "Individual wrapper qualification remains unreviewed. "
                "The linked canonical accounts state the supported and unsupported claim, "
                "actual verification performed, remaining input or review, cause category, "
                "consequence, precise next acceptance route, negative or refused result and "
                "matched denominator. Read those limits alongside this page's own source "
                "population; an account link does not substitute another study's denominator "
                "or establish scientific validity.",
                "",
            )
        )
    else:
        for label, text in route.qualification.fields:
            lines.extend((f"**{label}.** {text}", ""))
        lines.extend(
            (
                "Qualified authored reader SHA-256: "
                f"`{route.qualification.authored_reader_sha256}`.",
                "",
            )
        )
        for evidence in route.qualification.evidence:
            target = (
                "https://github.com/bijux/bijux-pollenomics/blob/main/"
                + quote(evidence.path, safe="/")
                if evidence.path.startswith("reports/science/")
                else posixpath.relpath(evidence.path, parent)
            )
            lines.extend(
                (
                    f"- [Retained qualification evidence: {evidence.path}]({target}) "
                    f"(SHA-256 `{evidence.sha256}`).",
                    "",
                )
            )
    for account in route.accounts:
        relative = (
            "https://github.com/bijux/bijux-pollenomics/blob/main/"
            + quote(account.report_path, safe="/")
            if account.report_path.startswith("reports/science/")
            else posixpath.relpath(account.report_path, parent)
        )
        lines.extend(
            (
                f"- [Canonical scientific account: {account.report_path}]({relative}) "
                f"(source SHA-256 `{account.source_sha256}`).",
                "",
            )
        )
    lines.append(
        "JSON and CSV retain their domain source and numerical manifests; "
        "a reading route does not rerun those producers. PDF exports retain "
        "their export inventory and source pins and must be regenerated "
        "when their canonical account changes."
    )
    return base + (BEGIN + "\n".join(lines) + "\n" + END).encode("utf-8")


def publish_scientific_routes(output_root: Path) -> int:
    """Apply reviewed routes to present wrappers before portal content is indexed."""
    root = Path(output_root)
    prepared: list[tuple[Path, bytes]] = []
    for relative, route in load_routes().items():
        path = root.joinpath(*PurePosixPath(relative).parts[2:])
        if not path.exists() and not path.is_symlink():
            continue
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(root.resolve())
        ):
            raise ValueError("Scientific reader is not a regular in-scope file")
        if route.qualification is not None:
            validate_evidence(root, route.qualification, portal=True)
        prepared.append((path, render_route(path.read_bytes(), route)))
    for path, rendered in prepared:
        path.write_bytes(rendered)
    return len(prepared)
