"""Publish a traceable grouped view from one authenticated retained result."""

from __future__ import annotations

import csv
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import re
import secrets
from typing import Any

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
)
from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement

from .projection import project_retained_result


def _encoded(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, allow_nan=False, ensure_ascii=False) + "\n"
    ).encode()


def _csv(rows: list[dict[str, Any]], population: dict[str, Any]) -> str:
    flattened = []
    for row in rows:
        item = {k: v for k, v in row.items() if not isinstance(v, dict)}
        item.update(
            {
                f"variance_{name}_percentage_points_squared": value
                for name, value in row[
                    "variance_components_percentage_points_squared"
                ].items()
            }
        )
        item.update(
            {
                k: population[k]
                for k in (
                    "conditioning_event",
                    "requested_draws",
                    "complete_draws",
                    "undefined_draws",
                    "source_result_sha256",
                    "denominator",
                    "cover_policy",
                    "uncertainty",
                )
            }
        )
        flattened.append(item)
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=list(flattened[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(flattened)
    return output.getvalue()


def _html(result: dict[str, Any]) -> str:
    unconditional = (
        "Unconditional moments remain unavailable because some saved age states are undefined."
        if result["undefined_draws"]
        else "All saved age states are defined; the same moments cover the full saved population."
    )
    rows = "".join(
        f"<tr><td>{row['window_id']}: {row['younger_bp']}–{row['older_bp']}</td><td>{escape(row['group'])}</td>"
        f"<td>{row['mean_percent']:.3f}</td><td>{row['standard_deviation_percentage_points']:.3f}</td></tr>"
        for row in result["components"]
    )
    contrasts = "".join(
        f"<tr><td>{row['older_window_id']} minus {row['younger_window_id']}</td><td>{escape(row['group'])}</td>"
        f"<td>{row['mean_difference_percentage_points']:.3f}</td><td>{row['standard_deviation_percentage_points']:.3f}</td></tr>"
        for row in result["contrasts"]
    )
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>ABBO grouped conditional composition</title>"
        "<style>body{font:17px system-ui;max-width:65rem;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0}th,td{text-align:left;padding:.5rem;border-bottom:1px solid #bbb}"
        "code{overflow-wrap:anywhere}caption{text-align:left;font-weight:600}</style>"
        "<h1>ABBO grouped conditional composition</h1>"
        f"<p>{result['complete_draws']:,} of {result['requested_draws']:,} saved joint age states satisfy the complete-panel event; "
        f"{result['undefined_draws']:,} remain undefined. {unconditional}</p>"
        "<p>Fractions of the selected five-taxon panel, not whole vegetation or forest/open cover. "
        "SD is conditional spread in percentage points, not a confidence interval or measured accuracy. "
        "The source uses positive REVEALS inverse closure; this view performs no LOVE clipping.</p>"
        '<p><a href="components.csv">Grouped means and variance components (CSV)</a> · '
        '<a href="contrasts.csv">Shared-source time contrasts (CSV)</a> · '
        '<a href="report.json">Full grouped covariance (JSON)</a> · '
        '<a href="source-result.json">Exact retained source result</a> · '
        '<a href="manifest.json">File digests</a></p>'
        "<table><caption>Conditional panel composition</caption><thead><tr><th>Window: calibrated BP [younger, older)</th>"
        "<th>Literal group</th><th>Mean (%)</th><th>SD (percentage points)</th></tr></thead><tbody>"
        + rows
        + "</tbody></table>"
        "<table><caption>Older minus younger contrasts; original window IDs retained</caption>"
        "<thead><tr><th>Window contrast</th><th>Literal group</th><th>Difference (percentage points)</th>"
        "<th>SD (percentage points)</th></tr></thead><tbody>"
        + contrasts
        + "</tbody></table>"
        "<p>Each covariance component is projected as GΣGᵀ, including cross-window terms. "
        "Age, counting and shared-PPE variances sum to total; mean-gradient PPE plus age/PPE interaction "
        "sum to shared PPE. Those last two are a decomposition, not additional independent sources.</p>"
        + "<h2>Preserved source assumptions and limits</h2><ul>"
        + "".join(f"<li>{escape(limit)}</li>" for limit in result["source_limits"])
        + "</ul>"
        f"<p>Source SHA-256: <code>{result['source_result_sha256']}</code>.</p></html>"
    )


def publish_grouped_result(
    source: Path, *, expected_result_sha256: str, destination: Path
) -> dict[str, str]:
    """Create an immutable self-contained view without rerunning a scientific fit."""
    if re.fullmatch(r"[0-9a-f]{64}", expected_result_sha256) is None:
        raise ValueError("Expected source digest must be an independent SHA-256")
    source, destination = source.absolute(), destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    with BoundedInputTree(
        source.parent, max_bytes=512 * 1024, max_files=1, selected=source.name
    ) as inputs:
        raw = inputs.read(source, max_bytes=512 * 1024)
        if sha256(raw).hexdigest() != expected_result_sha256:
            raise ValueError("Retained source result digest differs")
        result = project_retained_result(json.loads(raw))
        result["source_result_sha256"] = expected_result_sha256
        stage = (
            destination.parent
            / f".{destination.name}.candidate-{secrets.token_hex(16)}"
        )
        members = {
            "source-result.json": raw,
            "report.json": _encoded(result),
            "components.csv": _csv(result["components"], result).encode(),
            "contrasts.csv": _csv(result["contrasts"], result).encode(),
            "index.html": _html(result).encode(),
        }
        manifest = {
            "schema_version": "abborrtjarnen-grouped-view.v1",
            "source_result_sha256": expected_result_sha256,
            "scientific_admission": "unchanged_from_source",
            "files": {n: sha256(b).hexdigest() for n, b in members.items()},
        }
        encoded = _encoded(manifest)
        members["manifest.json"] = encoded

        def validate(candidate: Path) -> dict[str, str]:
            with BoundedInputTree(
                candidate, max_bytes=2 * 1024 * 1024, max_files=6
            ) as captured:
                if set(captured.files) != set(members):
                    raise ValueError("Grouped candidate inventory differs")
                for name, content in members.items():
                    if (
                        captured.read(candidate / name, max_bytes=len(content))
                        != content
                    ):
                        raise ValueError("Grouped candidate bytes differ")
            inputs.validate()
            return {
                "manifest_sha256": sha256(encoded).hexdigest(),
                "source_result_sha256": expected_result_sha256,
            }

        with (
            DirectoryAnchor(destination.parent, create=True) as parent,
            OwnedTreeWriter(stage, max_bytes=2 * 1024 * 1024, max_files=6) as writer,
            OwnedTreeWriter(
                destination.parent
                / f".{destination.name}.recovery-{secrets.token_hex(16)}",
                max_bytes=1,
                max_files=1,
            ) as recovery_writer,
        ):
            for name, content in members.items():
                writer.write_bytes(name, content)
            inputs.validate()
            writer.validate_closed_attachment(stage)
            parent.check()
            recovery_writer.validate_attachment()
            with DirectoryAnchor(recovery_writer.root) as recovery:
                receipt = publish_owned_replacement(
                    writer,
                    final=destination,
                    prior=None,
                    recovery=recovery,
                    validate=validate,
                )
                parent.check()
    return receipt
