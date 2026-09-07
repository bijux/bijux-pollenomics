"""Fixtures for compact AADR accountability tests."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrSourceTable,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    AadrPanelReconciliation,
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    AadrReleaseManifestIdentity,
)
from bijux_pollenomics.collection.sources.aadr.materialization.source_rows import (
    load_aadr_source_table,
)

HEADER = "\t".join(
    (
        "Genetic ID",
        "Political Entity",
        "Method for Determining Date",
        "Date mean in BP",
        "Date standard deviation in BP",
        "Full Date",
        "Latitude",
        "Longitude",
        "Source note",
    )
)


def source_table(
    tmp_path: Path,
    dataset_name: str,
    rows: tuple[tuple[str, ...], ...],
) -> AadrSourceTable:
    physical_path = tmp_path / dataset_name / f"{dataset_name}.anno"
    physical_path.parent.mkdir(parents=True)
    data_rows = "\n".join("\t".join(row) for row in rows)
    physical_path.write_text(
        HEADER + "\n" + (data_rows + "\n" if data_rows else ""),
        encoding="utf-8",
    )
    return load_aadr_source_table(
        physical_path,
        source_release="v66",
        dataset_name=dataset_name,
        logical_source_path=f"data/aadr/v66/{dataset_name}/{dataset_name}.anno",
    )


def reconciliation(tmp_path: Path) -> AadrPanelReconciliation:
    ho = source_table(
        tmp_path,
        "ho",
        (
            ("ID-DK", " Denmark ", "Direct", "0", "0", "1-0 BP", "0", "0", "zero"),
            ("ID-FI", "Finland", "Modern", "-25.50", "", "modern", "", "", "negative"),
            (
                "ID-SE",
                "Sweden",
                "Context",
                "100",
                "20",
                "120-80 BP",
                "59",
                "18",
                "sweden",
            ),
            (
                "ID-OTHER",
                "Estonia",
                "Context",
                "unknown",
                "10",
                "text",
                "bad",
                "18",
                "other",
            ),
            ("ID-MISSING", "", "", "", "", "", "", "", "missing"),
            (
                "ID-CONFLICT",
                "Denmark",
                "Direct",
                "50",
                "5",
                "55-45 BP",
                "56",
                "12",
                "left",
            ),
            ("", "Norway", "Context", "0", "", "text", "60", "10", "unkeyed"),
            ("ID-COMP", "Norway", "Known", "-1", "0", "1 CE", "60", "10", "known"),
        ),
    )
    capture = source_table(
        tmp_path,
        "1240k",
        (
            (
                "ID-DK",
                "Denmark",
                "Direct",
                "0.0",
                "0.0",
                "1-0 BP",
                "0",
                "0",
                "zero decimal",
            ),
            (
                "ID-SE",
                "Sweden",
                "Context",
                "100",
                "20",
                "120-80 BP",
                "59",
                "18",
                "sweden duplicate",
            ),
            (
                "ID-CONFLICT",
                "Sweden",
                "Direct",
                "50",
                "5",
                "55-45 BP",
                "56",
                "12",
                "right",
            ),
            ("ID-COMP", "", "Known", "-1", "0", "1 CE", "60", "10", "country absent"),
        ),
    )
    return reconcile_aadr_panels((ho, capture))


def release_manifest_identity() -> AadrReleaseManifestIdentity:
    content = b'{"source":"AADR","requested_version":"v66"}\n'
    return AadrReleaseManifestIdentity(
        logical_path="data/aadr/v66/release_manifest.json",
        source_release="v66",
        sha256=sha256(content).hexdigest(),
        byte_count=len(content),
    )
