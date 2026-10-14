"""Bind individual scientific reader qualifications to their authored evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any

FIELDS = (
    ("supported_claim", "Supported claim"),
    ("unsupported_claim", "Unsupported claim"),
    ("actual_verification_performed", "Actual verification performed"),
    ("remaining_input_or_review", "Remaining input or review"),
    ("cause_category", "Cause category"),
    ("consequence", "Consequence"),
    ("precise_next_acceptance_route", "Precise next acceptance route"),
    ("negative_or_refused_result", "Negative or refused result"),
    ("matched_denominator", "Matched denominator"),
)
SHA256 = re.compile(r"[a-f0-9]{64}\Z")


@dataclass(frozen=True)
class Evidence:
    """Exact public retained result bytes supporting one reader's qualification."""

    path: str
    sha256: str


@dataclass(frozen=True)
class Qualification:
    """Explicit reader-specific facts, without inferring scientific admission."""

    authored_reader_sha256: str
    fields: tuple[tuple[str, str], ...]
    evidence: tuple[Evidence, ...]


def _digest(value: object) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ValueError("Scientific qualification requires an exact source digest")
    return value


def evidence_path(value: object) -> str:
    """Constrain qualification evidence to regular public report source paths."""
    if not isinstance(value, str):
        raise ValueError("Scientific evidence path must be text")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != value
        or "\\" in value
        or any(ord(c) < 32 for c in value)
        or path.parts[:2] not in {("docs", "report"), ("reports", "science")}
    ):
        raise ValueError("Scientific evidence path escapes its public report scope")
    return value


def parse_qualification(value: Any) -> Qualification | None:
    """Refuse incomplete qualifications while keeping unreviewed routes distinct."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {
        "authored_reader_sha256",
        "fields",
        "evidence_pins",
    }:
        raise ValueError("Scientific qualification record is malformed")
    authored = _digest(value["authored_reader_sha256"])
    fields = value["fields"]
    if not isinstance(fields, dict) or set(fields) != {key for key, _ in FIELDS}:
        raise ValueError("Scientific qualification must contain all nine exact fields")
    qualified: list[tuple[str, str]] = []
    for key, label in FIELDS:
        text = fields[key]
        if (
            not isinstance(text, str)
            or not text.strip()
            or text != text.strip()
            or any(ord(c) < 32 for c in text)
            or "<!--" in text
            or re.search(r"</?[A-Za-z][^>]*>", text)
        ):
            raise ValueError(f"Scientific qualification has invalid {label}")
        qualified.append((label, text))
    pins = value["evidence_pins"]
    if not isinstance(pins, list) or not pins:
        raise ValueError("Scientific qualification evidence must be a nonempty list")
    evidence: list[Evidence] = []
    for pin in pins:
        if not isinstance(pin, dict) or set(pin) != {"path", "sha256"}:
            raise ValueError("Scientific qualification evidence is malformed")
        path = evidence_path(pin["path"])
        if path in {record.path for record in evidence}:
            raise ValueError("Scientific qualification evidence is duplicated")
        evidence.append(Evidence(path, _digest(pin["sha256"])))
    return Qualification(authored, tuple(qualified), tuple(evidence))


def validate_authored_reader(raw: bytes, qualification: Qualification) -> None:
    """Refuse edited reader prose rather than silently transferring old facts."""
    if hashlib.sha256(raw).hexdigest() != qualification.authored_reader_sha256:
        raise ValueError("Scientific qualification belongs to another authored reader")


def validate_evidence(
    root: Path, qualification: Qualification, *, portal: bool
) -> None:
    """Check exact evidence bytes; portal writers see their owned report subtree."""
    root = root.resolve(strict=True)
    for record in qualification.evidence:
        parts = PurePosixPath(record.path).parts
        if portal and parts[:2] != ("docs", "report"):
            # Root research accounts are checked by the repository-wide consumer.
            continue
        path = root.joinpath(*(parts[2:] if portal else parts))
        current = root
        for part in path.relative_to(root).parts:
            current /= part
            if current.is_symlink():
                raise ValueError("Scientific qualification evidence contains a symlink")
        if (
            not path.is_file()
            or not path.resolve().is_relative_to(root)
            or hashlib.sha256(path.read_bytes()).hexdigest() != record.sha256
        ):
            raise ValueError(
                f"Scientific qualification evidence changed: {record.path}"
            )
