from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PUBLIC_INFORMATION_ROLE_MEANINGS = {
    "audit": "systematic inspection that reports findings across a surface or inventory",
    "blockers": "ordered or grouped reasons a surface is still stopped",
    "checklist": "explicit recovery checklist with bounded completion criteria",
    "completeness": "measured completeness surface for a bounded source or evidence family",
    "contract": "declared structure or publication promise that downstream work must honor",
    "coverage": "scope and completeness counts for a bounded publication surface",
    "country": "country-focused aggregation surface whose question is geographic rather than procedural",
    "dictionary": "normalization vocabulary surface that keeps naming decisions inspectable",
    "dossier": "assembled intake evidence for one bounded acquisition or review topic",
    "drift": "cross-surface disagreement that should stay visible until reconciled",
    "evidence": "direct evidence surface rather than a claim or publication wrapper",
    "first": "first-occurrence surface whose subject already defines the main question",
    "gate": "pass or fail claim boundary for publication or release language",
    "guard": "pass or fail governance control that predates clearer validation naming",
    "honesty": "public caveat surface that keeps limitations visible beside shipped outputs",
    "inventory": "listed tracked members of a governed source or publication family",
    "ledger": "accumulated caveats, conflicts, or exclusions that should remain reviewable",
    "matrix": "cross-domain comparison table with one repeated question across multiple surfaces",
    "overlap": "comparison surface showing where two evidence families intersect in time or space",
    "posture": "current repository truth stance about scope, thinness, or restraint",
    "queue": "ordered recovery pressure for unresolved work that still blocks evidence quality",
    "readiness": "current publication state under stated thresholds and caveats",
    "reconciliation": "alignment surface that resolves mismatches between two tracked registries",
    "registry": "governed member list for a source or publication family",
    "report": "reader-facing report surface whose subject already supplies the main boundary",
    "review": "reader-facing judgment surface that explains why a bounded result is or is not trusted",
    "scenario": "explicit modelled storyline that should not be mistaken for fixed evidence",
    "summary": "machine-readable or reader-facing aggregate orientation surface",
    "truth": "claim-calibration surface that refuses stronger language than the evidence warrants",
    "validation": "structural check surface with explicit pass or fail conditions",
    "workflow": "governed sequence for human review or manual curation",
}

DISALLOWED_PUBLIC_ARTIFACT_TOKENS = frozenset(
    {
        "packets",
        "scorecard",
        "viewer",
    }
)


@dataclass(frozen=True)
class PublicArtifactLanguageFinding:
    artifact_path: str
    stem: str
    heading: str | None
    information_role: str | None
    issues: tuple[str, ...]


def split_public_artifact_stem(stem: str) -> tuple[str, ...]:
    return tuple(part for part in stem.split("_") if part)


def infer_public_information_role(stem: str) -> str | None:
    for token in reversed(split_public_artifact_stem(stem)):
        if token in PUBLIC_INFORMATION_ROLE_MEANINGS:
            return token
    return None


def validate_public_artifact_stem(stem: str) -> tuple[str, ...]:
    tokens = set(split_public_artifact_stem(stem))
    issues: list[str] = []
    disallowed = sorted(tokens & DISALLOWED_PUBLIC_ARTIFACT_TOKENS)
    if disallowed:
        issues.append(f"disallowed_tokens:{','.join(disallowed)}")
    return tuple(issues)


def extract_markdown_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def audit_public_artifact_inventory(
    repo_root: Path,
) -> tuple[PublicArtifactLanguageFinding, ...]:
    repo_root = Path(repo_root)
    findings: list[PublicArtifactLanguageFinding] = []
    for path in _iter_public_artifact_paths(repo_root):
        stem = path.stem
        issues = list(validate_public_artifact_stem(stem))
        heading = None
        if path.suffix == ".md":
            heading = extract_markdown_heading(path.read_text(encoding="utf-8"))
            if heading is None:
                issues.append("missing_markdown_heading")
            else:
                heading_tokens = set(
                    split_public_artifact_stem(
                        heading.lower().replace(" ", "_").replace("-", "_")
                    )
                )
                disallowed_heading_tokens = sorted(
                    heading_tokens & DISALLOWED_PUBLIC_ARTIFACT_TOKENS
                )
                if disallowed_heading_tokens:
                    issues.append(
                        "heading_disallowed_tokens:"
                        + ",".join(disallowed_heading_tokens)
                    )
        findings.append(
            PublicArtifactLanguageFinding(
                artifact_path=str(path.relative_to(repo_root)),
                stem=stem,
                heading=heading,
                information_role=infer_public_information_role(stem),
                issues=tuple(issues),
            )
        )
    return tuple(findings)


def _iter_public_artifact_paths(repo_root: Path) -> tuple[Path, ...]:
    roots = (
        repo_root / "docs" / "report",
        repo_root / "data" / "adna" / "governance" / "source_library",
    )
    paths: list[Path] = []
    for root in roots:
        for path in sorted(root.iterdir()):
            if path.name.startswith(".") or not path.is_file():
                continue
            if path.suffix not in {".json", ".md"}:
                continue
            paths.append(path)
    return tuple(paths)
