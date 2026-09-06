from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
import io


def _render_csv(
    fieldnames: tuple[str, ...],
    rows: Sequence[Mapping[str, object]],
) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
