"""Compare the author's REVEALS inputs with the published PPE/FSP table."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Any

from .neotoma_parameter_mass import _identity

AUTHOR = Path(
    "docs/report/source-relations/neotoma/author-parameter-binding/report.json"
)
PUBLISHED = Path(
    "docs/report/source-relations/neotoma/parameter-candidates/report.json"
)
DISPLAY_LIMIT = Decimal("0.00050001")
PPE_PATTERN = re.compile(r"([0-9.]+) \(([0-9.]+)\)")


def publish(repository: Path, output: Path) -> dict[str, Any]:
    """Pair unique mean/FSP rows and retain every SD discrepancy."""
    repository = repository.resolve()
    author_path = repository / AUTHOR
    published_path = repository / PUBLISHED
    author = json.loads(author_path.read_text(encoding="utf-8"))
    published = json.loads(published_path.read_text(encoding="utf-8"))
    if (
        author["schema_version"] != "swedish-landclim-author-parameter-binding.v1"
        or author["author_target_count"] != 31
        or author["lra_admitted_samples"] != 0
        or published["parameter_row_count"] != 31
        or published["lra_accepted_samples"] != 0
    ):
        raise ValueError("Author or published parameter scope changed")
    paper_rows = []
    for row in published["rows"]:
        match = PPE_PATTERN.fullmatch(row["parameter_ppe_source_text"])
        if match is None:
            raise ValueError("Published PPE/SD source text changed")
        paper_rows.append(
            {
                "name": row["parameter_source_name"],
                "ppe": Decimal(match.group(1)),
                "sd": Decimal(match.group(2)),
                "fsp": Decimal(row["parameter_fsp_source_text"].rstrip("*")),
                "fsp_footnote": row["parameter_fsp_source_text"].endswith("*"),
            }
        )
    rows: list[dict[str, object]] = []
    used_names: set[str] = set()
    for entry in author["parameters"]:
        alpha = Decimal(entry["alpha_source_text"])
        vg = Decimal(entry["fall_speed_source_text"])
        source_sd = Decimal(entry["alpha_variance_source_text"]).sqrt()
        candidates = [
            row
            for row in paper_rows
            if abs(alpha - row["ppe"]) <= DISPLAY_LIMIT and vg == row["fsp"]
        ]
        if len(candidates) != 1 or candidates[0]["name"] in used_names:
            raise ValueError("Author-to-published parameter pairing is ambiguous")
        paper = candidates[0]
        used_names.add(str(paper["name"]))
        alpha_delta = alpha - paper["ppe"]
        sd_delta = source_sd - paper["sd"]
        rows.append(
            {
                "author_target": entry["author_target"],
                "published_parameter_name": paper["name"],
                "author_alpha": entry["alpha_source_text"],
                "published_ppe": str(paper["ppe"]),
                "alpha_difference": str(alpha_delta),
                "author_vg": entry["fall_speed_source_text"],
                "published_fsp": str(paper["fsp"]),
                "published_fsp_footnote": paper["fsp_footnote"],
                "author_sd_from_variance": str(source_sd),
                "published_sd": str(paper["sd"]),
                "sd_difference": str(sd_delta),
                "sd_display_correspondence": (
                    "within_three_decimal_display"
                    if abs(sd_delta) <= DISPLAY_LIMIT
                    else "exceeds_three_decimal_display"
                ),
            }
        )
    if len(rows) != 31 or used_names != {str(row["name"]) for row in paper_rows}:
        raise ValueError("Published parameter coverage is incomplete")
    exceptions = [
        {
            "author_target": row["author_target"],
            "published_parameter_name": row["published_parameter_name"],
            "sd_difference": row["sd_difference"],
        }
        for row in rows
        if row["sd_display_correspondence"] == "exceeds_three_decimal_display"
    ]
    report: dict[str, Any] = {
        "schema_version": "landclim-author-published-parameter-correspondence.v1",
        "pairing_rule": "unique author alpha within 0.00050001 of published three-decimal PPE and exact numeric FSP",
        "parameter_count": len(rows),
        "exact_fsp_count": len(rows),
        "alpha_within_display_count": len(rows),
        "sd_within_display_count": len(rows) - len(exceptions),
        "sd_exceptions": exceptions,
        "lra_admitted_samples": 0,
        "interpretation": (
            "Mean and fall-speed pairs identify all 31 published rows in this "
            "version; three source covariance SDs differ beyond the displayed "
            "three-decimal precision. No parameter values were substituted."
        ),
        "rows": rows,
        "inputs": [
            _identity(author_path, repository),
            _identity(published_path, repository),
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.output)
    print(f"{report['parameter_count']} author/published parameter pairs retained")


if __name__ == "__main__":
    main()
