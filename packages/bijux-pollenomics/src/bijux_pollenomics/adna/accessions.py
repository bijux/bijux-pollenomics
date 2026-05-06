from __future__ import annotations

from dataclasses import dataclass
import re

__all__ = [
    "AdnaAccessionReference",
    "resolve_accession_reference",
    "resolve_accession_lineage",
]

_GENBANK_RANGE_RE = re.compile(
    r"^(?P<start>[A-Z]{1,4}\d{5,8}(?:\.\d+)?)\s*-\s*(?P<end>[A-Z]{1,4}\d{5,8}(?:\.\d+)?)$"
)
_ENA_PROJECT_RE = re.compile(r"^PRJ[EDN][A-Z]?\d+$")
_SRA_SAMPLE_RE = re.compile(r"^(SAMEA|SAMN|SAMD|ERS|SRS)\d+$")
_GENBANK_ACCESSION_RE = re.compile(r"^[A-Z]{1,4}\d{5,8}(?:\.\d+)?$")


@dataclass(frozen=True)
class AdnaAccessionReference:
    """Typed accession reference that preserves upstream accession family."""

    family: str
    accession: str
    relation: str
    range_end: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "accession": self.accession,
            "relation": self.relation,
            "range_end": self.range_end,
        }


def resolve_accession_reference(value: str) -> AdnaAccessionReference:
    """Resolve one accession-like token without flattening accession families."""
    token = value.strip()
    if not token:
        raise ValueError("Accession value is required")

    relation = "direct"
    if ":" in token:
        prefix, suffix = token.split(":", 1)
        lowered = prefix.strip().casefold()
        if lowered in {"ena", "bioproject", "sra", "genbank"}:
            relation = lowered
            token = suffix.strip()

    if _ENA_PROJECT_RE.fullmatch(token):
        family = "ena_project" if token.startswith(("PRJEB", "PRJED")) else "bioproject"
        return AdnaAccessionReference(family=family, accession=token, relation=relation)
    if _SRA_SAMPLE_RE.fullmatch(token):
        return AdnaAccessionReference(
            family="sra_sample",
            accession=token,
            relation=relation,
        )
    if match := _GENBANK_RANGE_RE.fullmatch(token):
        return AdnaAccessionReference(
            family="genbank_range",
            accession=match.group("start"),
            range_end=match.group("end"),
            relation=relation,
        )
    if _GENBANK_ACCESSION_RE.fullmatch(token):
        return AdnaAccessionReference(
            family="genbank_accession",
            accession=token,
            relation=relation,
        )
    raise ValueError(f"Unsupported accession reference: {value}")


def resolve_accession_lineage(lineage: tuple[str, ...]) -> tuple[AdnaAccessionReference, ...]:
    """Resolve every accession-like token inside a lineage while preserving family type."""
    references: list[AdnaAccessionReference] = []
    for token in lineage:
        try:
            references.append(resolve_accession_reference(token))
        except ValueError:
            continue
    return tuple(references)
