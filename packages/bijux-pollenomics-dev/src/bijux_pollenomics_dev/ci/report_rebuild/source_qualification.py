"""Choose an explicit, reviewed external-source custody contract."""

from __future__ import annotations

from pathlib import Path

from .author_snapshot import SCHEMA as AUTHOR_SNAPSHOT_SCHEMA
from .author_snapshot import validated_author_snapshot
from .contracts import ReportRebuildError, require_relative_path
from .publisher_tables import (
    SCHEMA as PUBLISHER_TABLE_SCHEMA,
)
from .publisher_tables import (
    validated_publisher_report_tables,
)
from .qualified_sources import (
    SCHEMA as LEGACYAGE_SCHEMA,
)
from .qualified_sources import (
    QualifiedReportSources,
    _object,
    _regular_path,
)
from .qualified_sources import (
    validated_external_report_sources as validated_legacyage_sources,
)


def validated_external_report_sources(
    repository: Path, source_root: Path, descriptor_path: Path
) -> QualifiedReportSources:
    """Dispatch only declared custody formats; never infer from files."""
    relative = require_relative_path(descriptor_path.as_posix(), "source descriptor")
    if relative.startswith("external/"):
        raise ReportRebuildError("source descriptor overlaps external input namespace")
    descriptor = _object(
        _regular_path(repository.resolve(strict=True) / relative).read_bytes()
    )
    schema = descriptor.get("schema_version")
    if schema == LEGACYAGE_SCHEMA:
        return validated_legacyage_sources(repository, source_root, descriptor_path)
    if schema == PUBLISHER_TABLE_SCHEMA:
        return validated_publisher_report_tables(
            repository, source_root, descriptor_path
        )
    if schema == AUTHOR_SNAPSHOT_SCHEMA:
        return validated_author_snapshot(repository, source_root, descriptor_path)
    if schema == "qualified-rootsi-bokesjon-workbook.v1":
        from .rootsi_workbook import validated_rootsi_bokesjon_workbook

        return validated_rootsi_bokesjon_workbook(
            repository, source_root, descriptor_path
        )
    if schema == "qualified-landclim-two-grid-packet.v1":
        from .landclim_two_grid_packet import validated_landclim_two_grid_packet

        return validated_landclim_two_grid_packet(
            repository, source_root, descriptor_path
        )
    if schema == "qualified-neotoma-publication-link.v1":
        from .neotoma_publication_link import validated_neotoma_publication_link

        return validated_neotoma_publication_link(
            repository, source_root, descriptor_path
        )
    if schema == "qualified-pangaea-solsoe-age-table.v1":
        from .source_contracts.pangaea_age_controls import validated_solsoe_age_table

        return validated_solsoe_age_table(repository, source_root, descriptor_path)
    if schema == "qualified-pangaea-epd-age-table.v1":
        from .source_contracts.pangaea_epd_age_table import validated_epd_age_table

        return validated_epd_age_table(repository, source_root, descriptor_path)
    raise ReportRebuildError("unknown external report source schema")
