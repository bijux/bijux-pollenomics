"""Replay embedded source products against the exact access-start parent."""

from __future__ import annotations

import json
from typing import cast

from ...contracts import manifest_sha256
from ..observation_access import (
    HeldoutPollenSourceLocator,
    MeasuredVegetationSourceLocator,
    OutcomeAccessStartReceipt,
)
from ..contracts import refuse
from .contracts import (
    HeldoutPollenCountSourceProduct,
    HeldoutPollenCountUnit,
    MeasuredVegetationSourceProduct,
    _expected_sites,
    _unit_provenance,
)
from .reading import _pollen_channel


def bind_products_to_start(
    products: tuple[MeasuredVegetationSourceProduct, HeldoutPollenCountSourceProduct],
    start: OutcomeAccessStartReceipt,
    reads: list[object],
) -> None:
    """Recheck every embedded product, unit and actual read against the plan."""
    taxa = start.plan.prediction_product.protocols[0].scope.taxa
    if any(
        protocol.scope.taxa != taxa
        for protocol in start.plan.prediction_product.protocols
    ):
        refuse("Observation completion scopes disagree on their taxon denominator")
    locators = (start.plan.sources.vegetation, start.plan.sources.pollen)
    kinds = ("independent_measured_vegetation", "heldout_pollen_counts")
    for raw_product, raw_locator, kind, raw_read in zip(
        products, locators, kinds, reads, strict=True
    ):
        product = cast(
            MeasuredVegetationSourceProduct | HeldoutPollenCountSourceProduct,
            raw_product,
        )
        locator = cast(
            MeasuredVegetationSourceLocator | HeldoutPollenSourceLocator,
            raw_locator,
        )
        if not isinstance(raw_read, dict):
            refuse("Observation completion read must be an exact object")
        read = cast(dict[str, object], raw_read)
        source = cast(dict[str, object], json.loads(product.canonical_product_json))
        raw_source = cast(
            dict[str, object], json.loads(cast(str, source["source_canonical_json"]))
        )
        byte_count = read.get("bytes")
        if (
            read.get("source_kind") != kind
            or read.get("path") != str(locator.path)
            or read.get("source_sha256") != locator.expected_source_sha256
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count <= 0
            or source.get("source_file_sha256") != read.get("source_sha256")
            or source.get("reader_profile") != locator.reader_profile
            or source.get("reader_code_sha256") != locator.reader_code_sha256
            or source.get("source_reference_id") != locator.source_reference_id
            or source.get("taxa") != list(taxa)
            or source.get("access_plan_sha256") != start.plan.plan_sha256
            or source.get("access_start_receipt_sha256") != start.receipt_sha256
            or source.get("source_locator_sha256") != manifest_sha256(locator.as_dict())
            or source.get("actual_reads") != [read]
        ):
            refuse("Observation product differs from its planned actual read")
        expected = _expected_sites(start, kind)
        if {unit.observation_id for unit in product.units} != set(expected):
            refuse("Embedded observation product denominator differs from its plan")
        for unit in product.units:
            site = expected[unit.observation_id]
            raw_unit = next(
                value
                for value in cast(list[dict[str, object]], raw_source["units"])
                if value["observation_id"] == unit.observation_id
            )
            provenance = _unit_provenance(raw_source, raw_unit)
            if (
                (
                    unit.record_id,
                    unit.site_id,
                    unit.group_id,
                    unit.block_id,
                    unit.bin_id,
                )
                != (
                    site.record_id,
                    site.site_id,
                    site.group_id,
                    site.block_id,
                    site.bin_id,
                )
                or unit.support != site.support
                or unit.source_reference_id != locator.source_reference_id
                or tuple(name for name, _ in unit.values) != taxa
                or (
                    unit.source_snapshot_sha256,
                    unit.source_member_sha256,
                    unit.reviewed_taxon_mapping_sha256,
                    unit.normalization_code_sha256,
                    unit.rights_evidence_sha256,
                    unit.source_unit_sha256,
                )
                != provenance
            ):
                refuse("Embedded observation unit differs from its frozen scope")
            if isinstance(unit, HeldoutPollenCountUnit):
                _pollen_channel(
                    start,
                    unit.observation_id,
                    unit.pollen_channel_input_id,
                    unit.pollen_channel_source_sha256,
                )
