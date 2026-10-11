"""Preserve training exclusion, target membership and source count closure."""

from __future__ import annotations

import hashlib

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    require_mapping,
)

from .fixtures import Packet, _mutate_product, _run, _unpublished
from .fixtures import packet as packet


@pytest.mark.parametrize(
    "failure",
    [
        "held-out-country",
        "missing-nordic-site",
        "missing-swedish-site",
        "site-identity",
        "taxon-axis",
        "negative-count",
        "bool-count",
        "mass",
        "shared-bin",
    ],
)
def test_training_membership_axis_and_source_counts_refuse_drift(
    packet: Packet, failure: str
) -> None:
    def mutate(payload: JsonObject) -> None:
        key = next(iter(payload))
        profile = require_mapping(payload[key], "training fixture")
        bins = require_mapping(profile["bins"], "training fixture bins")
        cell = require_mapping(next(iter(bins.values())), "training fixture cell")
        counts = require_mapping(cell["counts"], "training fixture counts")
        if failure == "held-out-country":
            profile["country"] = "DK"
        elif failure == "missing-nordic-site":
            payload.pop(key)
        elif failure == "missing-swedish-site":
            swedish = next(
                k
                for k, v in payload.items()
                if require_mapping(v, "profile fixture")["country"] == "SE"
            )
            payload.pop(swedish)
        elif failure == "site-identity":
            profile["site_id"] = "wrong"
        elif failure == "taxon-axis":
            counts.pop(next(iter(counts)))
        elif failure in {"negative-count", "bool-count"}:
            counts[next(iter(counts))] = -1 if failure == "negative-count" else False
        elif failure == "mass":
            cell["all_pollen_nisp"] = 1
        else:
            cell["sample_count"] = 2

    _mutate_product(packet, "inputs/training-DK.json.gz", mutate)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize(
    "failure",
    [
        "country",
        "samples",
        "site-coverage",
        "duplicate-site",
        "duplicate-sample",
        "bin-membership",
        "age-claims",
    ],
)
def test_target_metadata_membership_and_sample_denominators_refuse_drift(
    packet: Packet, failure: str
) -> None:
    def mutate(payload: JsonObject) -> None:
        sites_value = payload["sites"]
        assert isinstance(sites_value, list)
        sites = [require_mapping(value, "target site fixture") for value in sites_value]
        site = sites[0]
        if failure == "country":
            payload["country"] = "DK"
        elif failure == "samples":
            payload["candidate_samples"] = 1
        elif failure == "site-coverage":
            sites.pop()
        elif failure == "duplicate-site":
            sites[1] = sites[0]
        elif failure == "duplicate-sample":
            sites[1]["candidate_sample_ids"] = sites[0]["candidate_sample_ids"]
        elif failure == "bin-membership":
            site["candidate_bin_ids"] = ["999"]
        else:
            claims = require_mapping(
                payload["selected_age_claim_ids"], "selected claim fixture"
            )
            claims.pop(next(iter(claims)))
        payload["sites"] = sites

    _mutate_product(packet, "inputs/metadata-FI.json.gz", mutate)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize(
    "failure",
    [
        "missing-site",
        "missing-bin",
        "sample-count",
        "unmapped-mass",
        "extra-bin-field",
        "truncated-gzip",
    ],
)
def test_sealed_count_bins_cannot_change_the_source_account(
    packet: Packet, failure: str
) -> None:
    def mutate(payload: JsonObject) -> None:
        key = next(iter(payload))
        bins = require_mapping(payload[key], "sealed bins fixture")
        bin_id = next(iter(bins))
        cell = require_mapping(bins[bin_id], "sealed count fixture")
        if failure == "missing-site":
            payload.pop(key)
        elif failure == "missing-bin":
            bins.pop(bin_id)
        elif failure == "sample-count":
            cell["sample_count"] = 0
        elif failure == "unmapped-mass":
            cell["unmapped_nisp"] = 999
        else:
            cell["extra"] = 1

    relative = "sealed-outcomes/outcomes-DK.json.gz"
    if failure == "truncated-gzip":
        packet.products[relative] = packet.products[relative][:20]
        hashes = require_mapping(
            packet.manifest["produced_file_sha256"], "product fixture hashes"
        )
        hashes[relative] = hashlib.sha256(packet.products[relative]).hexdigest()
    else:
        _mutate_product(packet, relative, mutate)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    _unpublished(packet)
