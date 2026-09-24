"""Build typed inputs while sealed pollen and NFI outcomes remain unopened."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics.analysis.lra_validation.channels import (
    ObservationChannels,
    PollenChannel,
)
from bijux_pollenomics.analysis.lra_validation.contracts import (
    SiteRecord,
    site_group_id,
)
from bijux_pollenomics.analysis.lra_validation.evaluation.api import (
    ExternalInput,
    Support,
)

from .projection import digest

_ADMISSION_KEYS = {"evidence_row_sha256", "taxon_ppe_receipt_sha256"}


def _support(value: dict[str, Any]) -> Support:
    return Support(age_type="BP", **value)


def parse_admission(
    value: object,
    candidate: dict[str, Any],
    evidence: dict[str, Any],
    projection: dict[str, Any],
    receipt: dict[str, Any],
    receipt_sha256: str,
) -> tuple[SiteRecord, dict[str, Any], ObservationChannels, ExternalInput]:
    """Construct deterministic identities; the return may only select pinned evidence."""
    if not isinstance(value, dict) or set(value) != _ADMISSION_KEYS:
        raise ValueError("admission fields differ from the exact schema")
    if value["evidence_row_sha256"] != digest(evidence):
        raise ValueError("admission targets another reviewed evidence row")
    if value["taxon_ppe_receipt_sha256"] != receipt_sha256:
        raise ValueError("admission targets another taxon/PPE trust anchor")

    sample = candidate["pollen_sample"]
    tract = candidate["nfi_tract"]
    plot = candidate["nfi_plot"]
    year = candidate["nfi_year"]
    record_id = candidate["record_id"]
    sample_alias = f"empd2:sample:{sample}"
    plot_alias = f"nfi:plot:{tract}:{plot}"
    site_id = f"empd2-site:{sample}"
    pollen_binding = evidence["pollen_source_binding"]
    index_row = pollen_binding["index_row"]
    workbook_sha = projection["source_identities"]["nfi_workbook"]
    pollen_payload_sha = index_row["sample_payload_sha256"]
    pollen_input_id = f"empd2-count-sample:{sample}:{index_row['index_row_sha256']}"
    nfi_observation_sha = digest(
        {
            "nfi_workbook_sha256": workbook_sha,
            "nfi_tract": tract,
            "nfi_plot": plot,
            "nfi_year": year,
        }
    )
    vegetation_input_id = f"nfi-source-row:{nfi_observation_sha}"
    pollen_support = _support(evidence["pollen_support"])
    vegetation_support = _support(evidence["vegetation_support"])
    record = SiteRecord(
        record_id=record_id,
        site_id=site_id,
        identity_keys=tuple(sorted((sample_alias, plot_alias))),
        block_id=f"nfi-tract:{tract}",
    )
    site = {
        "record_id": record_id,
        "site_id": site_id,
        "block_id": record.block_id,
        "bin_id": f"nfi-year:{year}",
        "strata": (
            f"country:{candidate['country_code']}",
            "reference:nfi-point-plot",
        ),
        "vegetation_observation_id": f"nfi-observation:{nfi_observation_sha}",
        "pollen_observation_id": pollen_input_id,
        "support": pollen_support,
    }
    channel = ObservationChannels(
        record_id=record_id,
        group_id="pending-derived-group",
        pollen_channels=(
            PollenChannel(
                pollen_input_id,
                pollen_payload_sha,
            ),
        ),
        vegetation_input_ids=(vegetation_input_id,),
    )
    external = ExternalInput(
        input_id=vegetation_input_id,
        role="observed_source",
        source_manifest_sha256=workbook_sha,
        support=vegetation_support,
    )
    return record, site, channel, external


def derived_group_ids(records: list[SiteRecord]) -> dict[str, str]:
    """Derive connected physical-site groups without reading outcomes."""
    parents = {record.record_id: record.record_id for record in records}

    def root(key: str) -> str:
        while parents[key] != key:
            parents[key] = parents[parents[key]]
            key = parents[key]
        return key

    owners: dict[str, str] = {}
    for record in records:
        for key in (record.site_id, *record.identity_keys):
            owner = owners.setdefault(key, record.record_id)
            parents[root(record.record_id)] = root(owner)
    members: dict[str, list[str]] = {}
    for record in records:
        members.setdefault(root(record.record_id), []).append(record.record_id)
    return {
        record_id: site_group_id(tuple(sorted(group)))
        for group in members.values()
        for record_id in group
    }
