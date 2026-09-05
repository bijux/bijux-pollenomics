from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def write_baseline(
    output_path: Path,
    *,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    build_baseline: Any,
    canonical_json: Callable[[object], bytes],
    read_file: Callable[[Path], bytes],
    write_atomic: Callable[[Path, bytes], None],
) -> Path:
    baseline = build_baseline(
        raw_archive_root=raw_archive_root,
        relational_root=relational_root,
        compact_geojson_path=compact_geojson_path,
        lineage_path=lineage_path,
    )
    path = Path(output_path)
    content = canonical_json(baseline)
    if path.exists():
        if read_file(path) == content:
            return path
        raise FileExistsError(
            "Neotoma refresh baseline already exists with different content; "
            "review drift before replacing it"
        )
    write_atomic(path, content)
    return path


def write_review(
    output_path: Path,
    *,
    baseline_path: Path,
    raw_archive_root: Path,
    relational_root: Path,
    compact_geojson_path: Path,
    lineage_path: Path,
    explanations: Mapping[str, str] | None,
    markdown_path: Path | None,
    parse_object: Callable[[bytes, str], dict[str, object]],
    read_file: Callable[[Path], bytes],
    build_baseline: Any,
    build_review: Any,
    write_atomic: Callable[[Path, bytes], None],
    canonical_json: Callable[[object], bytes],
    render_markdown: Callable[[Mapping[str, object]], str],
) -> Path:
    missing: list[str] = []
    prior: dict[str, object] | None = None
    candidate: dict[str, object] | None = None
    if Path(baseline_path).exists():
        prior = parse_object(read_file(Path(baseline_path)), "Neotoma prior baseline")
    else:
        missing.append("missing_prior_baseline")
    candidate_inputs = (
        ("raw_archive", Path(raw_archive_root)),
        ("relational_detail", Path(relational_root)),
        ("compact_site_layer", Path(compact_geojson_path)),
        ("compact_lineage", Path(lineage_path)),
    )
    missing.extend(
        f"missing_candidate_{role}"
        for role, path in candidate_inputs
        if not path.exists()
    )
    if not any(reason.startswith("missing_candidate_") for reason in missing):
        candidate = build_baseline(
            raw_archive_root=raw_archive_root,
            relational_root=relational_root,
            compact_geojson_path=compact_geojson_path,
            lineage_path=lineage_path,
        )
    review = build_review(
        prior, candidate, explanations=explanations, missing_reasons=missing
    )
    write_atomic(Path(output_path), canonical_json(review))
    if markdown_path is not None:
        write_atomic(Path(markdown_path), render_markdown(review).encode("utf-8"))
    return Path(output_path)


def render_markdown(payload: Mapping[str, object]) -> str:
    changes = payload.get("changes")
    change_rows = changes if isinstance(changes, list) else []
    rendered = "\n".join(
        f"| `{change.get('change_id', '')}` | `{change.get('prior')}` | "
        f"`{change.get('candidate')}` | {change.get('explanation') or 'Unexplained'} |"
        for change in change_rows
        if isinstance(change, Mapping)
    )
    if not rendered:
        rendered = (
            "| None | — | — | Candidate is byte- and count-equivalent to baseline. |"
        )
    refusals = payload.get("refusal_reasons")
    refusal_values = refusals if isinstance(refusals, list) else []
    refusal_text = ", ".join(str(value) for value in refusal_values) or "none"
    return f"""# Neotoma refresh review

This generated review compares a retained governed baseline with the current candidate. It records drift but does not authorize replacing a changed baseline.

- Status: `{payload.get("status", "refused")}`
- Fixed point: `{str(payload.get("fixed_point", False)).lower()}`
- Changes: `{payload.get("change_count", 0)}`
- Unexplained changes: `{payload.get("unexplained_change_count", 0)}`
- Refusal reasons: `{refusal_text}`
- Baseline update permitted by this automated check: `{str(payload.get("baseline_update_permitted", False)).lower()}`

| Change | Prior | Candidate | Explanation |
| --- | --- | --- | --- |
{rendered}
"""
