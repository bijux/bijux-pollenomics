from __future__ import annotations

from dataclasses import asdict

from ..core.files import write_json
from .models import DataCollectionSummary


def write_collection_summary(summary: DataCollectionSummary) -> None:
    """Write a machine-readable summary for the collected data tree."""
    payload = asdict(summary)
    payload["output_root"] = str(summary.output_root)
    payload["summary_path"] = str(summary.summary_path)
    write_json(summary.summary_path, payload)
