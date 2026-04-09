from __future__ import annotations

from pathlib import Path

AADR_HEADER = "\t".join(
    [
        "Genetic ID",
        "Master ID",
        "Group ID",
        "Locality",
        "Political Entity",
        "Lat.",
        "Long.",
        "Publication abbreviation",
        "Year first published",
        "Full Date",
        "Date mean in BP",
        "Data type",
        "Molecular Sex",
    ]
)


def write_anno_file(path: Path, rows: list[str], *, header: str = AADR_HEADER) -> None:
    """Write a small AADR anno test file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
