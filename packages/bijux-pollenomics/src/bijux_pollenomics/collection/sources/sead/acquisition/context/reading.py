"""Reopen only an externally pinned, finite private source-context packet."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from ..scoped.models import NORDIC_TARGET_COUNTRIES
from .contracts import SeadContextSite
from .transport import decode
from .workflow import CONTEXT_PLANS, CONTEXT_SCHEMA, UNEXPANDED_REFERENCES

PACKET_MAX_BYTES = 64 * 1024 * 1024
PACKET_MAX_FILES = 512
MANIFEST_MAX_BYTES = 4 * 1024 * 1024


def read_sead_context(root: Path, *, expected_manifest_sha256: str) -> dict[str, Any]:
    """Hash all private packet members, retaining explicit unresolved authority.

    This reader consumes the packet's raw context responses and table bodies. It
    is not a metadata-only reader or scientific/context-to-country admission.
    The expected manifest identity must come from an independent receipt.
    """
    if not re.fullmatch(r"[a-f0-9]{64}", expected_manifest_sha256):
        raise ValueError("Context manifest pin must be an explicit SHA256")
    with BoundedInputTree(
        Path(root), max_bytes=PACKET_MAX_BYTES, max_files=PACKET_MAX_FILES
    ) as tree:
        raw = tree.read(tree.root / "manifest.json", max_bytes=MANIFEST_MAX_BYTES)
        if hashlib.sha256(raw).hexdigest() != expected_manifest_sha256:
            raise ValueError("Context manifest pin differs from independent authority")
        manifest = decode(raw)
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != CONTEXT_SCHEMA
        ):
            raise ValueError("Context manifest schema is not supported")
        if (
            manifest.get("country_admission") is not False
            or manifest.get("ecological_event_admission") is not False
        ):
            raise ValueError("Context packet cannot confer country or event admission")
        if (
            manifest.get("status") != "complete_context_only"
            or manifest.get("legacy_country_scope_meaning")
            != "regional_request_intent_only"
            or manifest.get("regional_request_intent") != list(NORDIC_TARGET_COUNTRIES)
            or manifest.get("unexpanded_native_references")
            != list(UNEXPANDED_REFERENCES)
            or manifest.get("tables") != [plan.table for plan in CONTEXT_PLANS]
        ):
            raise ValueError("Context packet scope or completion contract differs")
        sites = manifest.get("sites")
        if not isinstance(sites, list) or not 1 <= len(sites) <= 2:
            raise ValueError("Context selected sites are absent")
        for site in sites:
            if not isinstance(site, dict) or set(site) != {
                "site_id",
                "site_uuid",
                "membership_status",
            }:
                raise ValueError(
                    "Context site contract contains an unexpected authority"
                )
            SeadContextSite(**site)
        records = manifest.get("files")
        if not isinstance(records, list) or any(
            not isinstance(record, dict) for record in records
        ):
            raise ValueError("Context manifest lacks finite member pins")
        names = [record.get("path") for record in records]
        if (
            any(not isinstance(name, str) for name in names)
            or len(set(names)) != len(names)
            or set(names) | {"manifest.json"} != set(tree.files)
        ):
            raise ValueError("Context namespace differs from pinned members")
        required = {
            f"{kind}/{plan.table}.json"
            for plan in CONTEXT_PLANS
            for kind in ("payloads", "receipts")
        } | {"query-receipts.json"}
        if not required <= set(names):
            raise ValueError("Context namespace lacks fixed table evidence")
        for record in records:
            count = record.get("byte_count")
            if type(count) is not int or not 0 <= count <= PACKET_MAX_BYTES:
                raise ValueError("Context member pin has invalid byte count")
            body = tree.read(tree.root / record["path"], max_bytes=count)
            if len(body) != count or hashlib.sha256(body).hexdigest() != record.get(
                "sha256"
            ):
                raise ValueError("Context member pin differs from retained bytes")
        tree.check()
        return manifest
