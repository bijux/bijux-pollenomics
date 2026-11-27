"""Check selected stored source buffers without publishing their contents."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.filesystem import read_regular_file


def _held(path: Path, pin: str, limit: int) -> bytes:
    if not isinstance(pin, str) or re.fullmatch(r"[0-9a-f]{64}", pin) is None:
        raise ValueError("Source identity is malformed")
    data = read_regular_file(path, max_bytes=limit)
    if sha256(data).hexdigest() != pin:
        raise ValueError("Selected source buffer differs")
    return data


def verify_source_inputs(
    root: Path, selected: list[dict[str, Any]], declarations: list[dict[str, Any]]
) -> None:
    """Verify selected capsule, capture, receipt and native body identities.

    This checks the stored evidence against caller-pinned declarations. It does
    not independently replay original HTTP execution, scope policy or rights.
    """
    by_dataset = {row["dataset_id"]: row for row in declarations}
    if len(by_dataset) != len(declarations) or len(selected) != len(declarations):
        raise ValueError("Selected source populations differ")
    total = 0
    for item in selected:
        dataset, site = item["dataset_id"], item["site_id"]
        if (
            type(dataset) is not int
            or type(site) is not int
            or dataset not in by_dataset
        ):
            raise ValueError("Selected source identity differs")
        declared = by_dataset[dataset]
        capsule_pin, capture_pin = item["capsule_sha256"], item["capture_sha256"]
        root_capsule = root / capsule_pin
        capsule = json.loads(
            _held(root_capsule / "manifest.json", capsule_pin, 16 * 1024**2)
        )
        descriptor = capsule["captures"][capture_pin]
        if (
            descriptor.get("kind") != "facet"
            or descriptor["files"]["capture-manifest.json"]["sha256"] != capture_pin
        ):
            raise ValueError("Selected capsule membership differs")
        directory = root_capsule / "captures" / capture_pin
        capture_raw = _held(
            directory / "capture-manifest.json", capture_pin, 8 * 1024**2
        )
        if len(capture_raw) != descriptor["files"]["capture-manifest.json"]["bytes"]:
            raise ValueError("Selected capture size differs")
        capture = json.loads(capture_raw)
        prefix = capture_pin + ":/facets/"
        observation = item["observation_id"]
        if (
            not isinstance(observation, str)
            or not observation.startswith(prefix)
            or not re.fullmatch(r"0|[1-9][0-9]*", observation[len(prefix) :])
        ):
            raise ValueError("Selected source observation differs")
        index = int(observation[len(prefix) :])
        entries = capture["facets"]
        if index >= len(entries):
            raise ValueError("Selected source observation is absent")
        entry = entries[index]
        identity = entry["root_identity"]
        if (
            capture.get("schema_version")
            != "neotoma-dataset-facet-scoped-http-capture.v1"
            or entry.get("facet") != "publications"
            or type(identity.get("dataset_id")) is not int
            or identity["dataset_id"] != dataset
            or type(identity.get("site_id")) is not int
            or identity["site_id"] != site
            or entry.get("parent_scope_role") != "development_resource_discovery"
            or entry.get("terminal_status") != "received_complete_unqualified_facet"
            or not isinstance(entry.get("attempts"), list)
            or not entry["attempts"]
        ):
            raise ValueError("Selected source capture differs")
        attempt = entry["attempts"][-1]
        receipt_name, body_name = attempt["receipt_file"], attempt["body_file"]
        if (
            not isinstance(receipt_name, str)
            or not isinstance(body_name, str)
            or Path(receipt_name).name != receipt_name
            or Path(body_name).name != body_name
            or attempt.get("receipt_sha256") != item["receipt_sha256"]
        ):
            raise ValueError("Selected source attempt differs")
        receipt_raw = _held(directory / receipt_name, item["receipt_sha256"], 1024**2)
        body = _held(directory / body_name, item["body_sha256"], 4 * 1024**2)
        total += len(body)
        if total > 64 * 1024**2:
            raise ValueError("Selected source body budget exceeded")
        for name, data, pin in (
            (receipt_name, receipt_raw, item["receipt_sha256"]),
            (body_name, body, item["body_sha256"]),
        ):
            member = descriptor["files"][name]
            if (
                member.get("sha256") != pin
                or type(member.get("bytes")) is not int
                or member["bytes"] != len(data)
            ):
                raise ValueError("Selected source capsule member differs")
        receipt = json.loads(receipt_raw)
        proof = declared["source_declarations"]
        if (
            declared.get("receipt_sha256") != item["receipt_sha256"]
            or declared.get("body_sha256") != item["body_sha256"]
            or receipt.get("expected_dataset_id") != dataset
            or type(receipt.get("expected_dataset_id")) is not int
            or receipt.get("expected_site_id") != site
            or type(receipt.get("expected_site_id")) is not int
            or receipt.get("http_status") != 200
            or type(receipt.get("http_status")) is not int
            or receipt.get("body_complete") is not True
            or receipt.get("retained_body_bytes") != len(body)
            or type(receipt.get("retained_body_bytes")) is not int
            or receipt.get("retained_body_sha256") != item["body_sha256"]
            or receipt.get("requested_url")
            != f"https://api.neotomadb.org/v2.0/data/datasets/{dataset}/publications"
            or proof.get("request_url") != receipt["requested_url"]
            or proof.get("request_utc_start") != receipt.get("utc_start")
            or proof.get("request_utc_end") != receipt.get("utc_end")
            or proof.get("capture_utc_start") != capture.get("capture_utc_start")
            or proof.get("capture_utc_end") != capture.get("capture_utc_end")
        ):
            raise ValueError("Selected source receipt or declaration differs")
        native = json.loads(body)
        if (
            not isinstance(native, dict)
            or native.get("status") != "success"
            or not isinstance(native.get("data"), list)
        ):
            raise ValueError("Selected source native response differs")
        for row in native["data"]:
            publication = row["publication"]
            links = [
                link
                for link in publication["datasets"]
                if isinstance(link, dict)
                and type(link.get("datasetid")) is int
                and link["datasetid"] == dataset
            ]
            if (
                len(links) != 1
                or type(links[0].get("siteid")) is not int
                or links[0]["siteid"] != site
            ):
                raise ValueError("Selected nonempty publication relation differs")
