"""Authenticate native resource identities and retain portable source descriptors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..capture import replay_neotoma_metadata_capture
from ..capture.receipts import _object, _read, _safe_root
from ..capture.resources import NeotomaRetainedSource, replay_neotoma_resource_capture
from ..capture.resources.frozen import (
    qualify_neotoma_frozen_capture,
    qualify_neotoma_frozen_snapshot_capture,
)
from ..client import positive_native_id


@dataclass
class CatalogueSources:
    roster: dict[str, Any]
    metadata: dict[int, dict[str, Any]]
    sites: list[dict[str, Any]]
    original_epochs: dict[int, dict[str, Any]] | None
    descriptors: dict[str, dict[str, Any]]
    selected: dict[str, tuple[str, dict[str, Any]]]
    roots: dict[str, Path]
    manifests: dict[str, dict[str, Any]]
    qualifications: dict[str, dict[str, Any]]
    retained: Mapping[str, NeotomaRetainedSource]
    source_snapshots: dict[str, dict[str, Any]] = field(default_factory=dict)

    def source(
        self, digest: str, entry: dict[str, Any]
    ) -> tuple[dict[str, Any], bytes | None]:
        """Resolve original source time and entity bytes through authenticated reuse."""
        while "reused_from" in entry:
            digest = entry["reused_from"]["manifest_sha256"]
            manifest = self.manifests[digest]
            entry = next(
                row
                for row in manifest["resources"]
                if row["resource_key"] == entry["resource_key"]
            )
        if "retained_source" in entry:
            retained = self.retained[entry["resource_key"]]
            body = _read(retained.body_path, 32 * 1024 * 1024)
            if sha256(body).hexdigest() != retained.body_sha256:
                raise ValueError("Retained catalogue body identity differs")
            return {
                "source_kind": "retained_public_response",
                "epoch_kind": "original_timed_public_response",
                **entry["retained_source"],
            }, body
        reference: dict[str, Any] = {
            "capture_manifest_sha256": digest,
            "resource_key": entry["resource_key"],
            "epoch_kind": "provider_frozen_response"
            if entry["version"] == "doi_frozen"
            else "timed_live_api_response",
        }
        if not entry["attempts"]:
            reference["source_kind"] = "no_source_entity"
            reference["epoch_kind"] = "not_acquired"
            return reference, None
        attempt = entry["attempts"][-1]
        receipt = pinned_object(
            self.roots[digest] / attempt["receipt_file"],
            attempt["receipt_sha256"],
            65536,
        )
        reference.update(
            source_kind="source_http_attempt",
            receipt_file=attempt["receipt_file"],
            receipt_sha256=attempt["receipt_sha256"],
            requested_url=receipt["requested_url"],
            utc_start=receipt["utc_start"],
            utc_end=receipt["utc_end"],
            tls_mode=receipt["tls_mode"],
        )
        if "body_file" not in attempt:
            return reference, None
        body = _read(self.roots[digest] / attempt["body_file"], 32 * 1024 * 1024 + 1)
        if sha256(body).hexdigest() != receipt["retained_body_sha256"]:
            raise ValueError("Catalogue source body identity differs")
        reference.update(
            body_file=attempt["body_file"],
            body_sha256=receipt["retained_body_sha256"],
            body_bytes=len(body),
            http_status=receipt["http_status"],
            body_complete=receipt["body_complete"],
        )
        return reference, body


def pinned_object(path: Path, digest: str, bound: int) -> dict[str, Any]:
    content = _read(path, bound)
    if sha256(content).hexdigest() != digest:
        raise ValueError("Catalogue source identity differs")
    return _object(content)


def public_member(name: str) -> str:
    if not name or Path(name).name != name or name in {".", ".."} or "\\" in name:
        raise ValueError("Catalogue source member is not a portable file name")
    return name


def _receipt_source(
    digest: str, reference: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    source = {
        "capture_manifest_sha256": digest,
        "request_name": reference["request_name"],
        "receipt_file": reference["receipt_file"],
        "receipt_sha256": reference["receipt_sha256"],
        "body_file": receipt["body_file"],
        "body_sha256": receipt["retained_body_sha256"],
    }
    for key in (
        "requested_url",
        "request_method",
        "parameters",
        "role",
        "expected_site_id",
        "expected_dataset_id",
        "utc_start",
        "utc_end",
        "tls_mode",
    ):
        if key in receipt:
            source[key] = receipt[key]
    return source


def describe_capture(root: Path, digest: str, kind: str) -> dict[str, Any]:
    manifest = pinned_object(root / "capture-manifest.json", digest, 16 * 1024 * 1024)
    files = []
    for path in sorted(root.iterdir()):
        name = public_member(path.name)
        content = _read(path, 32 * 1024 * 1024 + 1)
        files.append(
            {
                "name": name,
                "bytes": len(content),
                "sha256": sha256(content).hexdigest(),
                "source_entity": name.endswith(".body"),
            }
        )
    return {
        "schema_version": "neotoma-resource-source-descriptor.v1",
        "capture_manifest_sha256": digest,
        "capture_kind": kind,
        "native_schema_version": manifest["schema_version"],
        "files": files,
        "body_resolver": "explicit capture_sources mapping keyed by capture_manifest_sha256",
        "source_bodies_in_descriptor": False,
    }


def _pointer(document: object, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError("Catalogue metadata pointer is invalid")
    value: Any = document
    try:
        for token in pointer.split("/")[1:]:
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                index = int(token)
                if index < 0 or str(index) != token:
                    raise ValueError("Noncanonical metadata array pointer")
                value = value[index]
            else:
                value = value[token]
    except (TypeError, KeyError, IndexError) as error:
        raise ValueError("Catalogue metadata pointer does not resolve") from error
    return value


def _original_metadata(
    root: Path | None,
) -> tuple[dict[int, dict[str, Any]] | None, dict[str, tuple[Path, dict[str, Any]]]]:
    if root is None:
        return None, {}
    root = _safe_root(root)
    manifest_bytes = _read(root / "manifest.json", 1024 * 1024)
    manifest = _object(manifest_bytes)
    originals, parts = {}, {}
    surface = manifest["surfaces"]["datasets"]
    count = 0
    for part in surface["parts"]:
        relative = Path(part["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Original catalogue metadata path escapes its source")
        path = root / relative
        payload = pinned_object(path, part["sha256"], 16 * 1024 * 1024)
        parts[part["sha256"]] = path, payload
        for index, row in enumerate(payload["rows"]):
            dataset_id = positive_native_id(row["source_dataset_id"])
            if dataset_id in originals:
                raise ValueError("Duplicate original dataset metadata")
            originals[dataset_id] = {
                "status": "retained_dataset_metadata",
                "epoch_kind": "original_relational_snapshot",
                "source_snapshot_id": row["source_snapshot_id"],
                "build_id": row["build_id"],
                "relational_manifest_sha256": sha256(manifest_bytes).hexdigest(),
                "dataset_metadata_sha256": part["sha256"],
                "json_pointer": f"/rows/{index}",
                "public_path": "data/neotoma/relational/" + relative.as_posix(),
                "native_row": row,
            }
            count += 1
    if count != surface["row_count"]:
        raise ValueError("Original dataset metadata population differs")
    return originals, parts


def prepare_catalogue_sources(
    *,
    roster_path: Path,
    expected_roster_sha256: str,
    metadata_captures: Mapping[str, Path],
    resource_captures: Mapping[str, Path],
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    original_relational_root: Path | None = None,
) -> CatalogueSources:
    content = _read(roster_path, 16 * 1024 * 1024)
    if sha256(content).hexdigest() != expected_roster_sha256:
        raise ValueError("Catalogue roster identity differs")
    roster = _object(content)
    rows = roster.get("resources")
    if (
        not isinstance(rows, list)
        or type(roster.get("resource_count")) is not int
        or roster["resource_count"] != len(rows)
    ):
        raise ValueError("Catalogue roster resource population differs")
    required = set(roster.get("source_metadata_capture_manifest_sha256", []))
    required.update(
        row["current_metadata_lookup"]["manifest_sha256"]
        for row in rows
        if "current_metadata_lookup" in row
    )
    if not required <= set(metadata_captures):
        raise ValueError("Catalogue metadata capture resolver is incomplete")
    descriptors, metadata_results = {}, {}
    body_index: dict[str, tuple[Path, dict[str, Any]]] = {}
    lookup_sources: dict[tuple[str, int], dict[str, Any]] = {}
    for digest, directory in metadata_captures.items():
        root = _safe_root(directory)
        metadata_results[digest] = replay_neotoma_metadata_capture(
            root, expected_manifest_sha256=digest
        )
        descriptors[digest] = describe_capture(root, digest, "metadata")
        manifest = pinned_object(root / "capture-manifest.json", digest, 1024 * 1024)
        for record in manifest["records"]:
            receipt = pinned_object(
                root / record["receipt_file"], record["receipt_sha256"], 65536
            )
            if (
                digest in roster["source_metadata_capture_manifest_sha256"]
                and receipt.get("expected_site_id") is not None
            ):
                body_index.setdefault(
                    receipt["retained_body_sha256"],
                    (
                        root / receipt["body_file"],
                        _receipt_source(digest, record, receipt),
                    ),
                )
            if receipt.get("expected_dataset_id") is not None:
                lookup_sources[(digest, receipt["expected_dataset_id"])] = (
                    _receipt_source(digest, record, receipt)
                )
    originals, original_parts = _original_metadata(original_relational_root)
    metadata, sites = {}, []
    roles = {
        "development_resource_discovery",
        "exposed_development",
        "reserved_candidate_confirmation",
        "heldout_no_numerical_access",
    }
    for row in rows:
        dataset_id = positive_native_id(row["dataset_id"])
        site_id, unit_id = (
            positive_native_id(row["site_id"]),
            positive_native_id(row["collection_unit_id"]),
        )
        if dataset_id in metadata:
            raise ValueError("Duplicate catalogue roster dataset")
        if (
            set(row["exposure_roles"]) != {"current", "doi_frozen"}
            or row["exposure_roles"]["current"] not in roles
            or row["exposure_roles"]["current"] != row["exposure_roles"]["doi_frozen"]
        ):
            raise ValueError(
                "Catalogue exposure roles are unsupported or contradictory"
            )
        locator = row["metadata_locator"]
        if (
            locator.get("source_kind")
            == "retained_relational_dataset_metadata_not_current_HTTP"
        ):
            if locator["response_sha256"] not in original_parts:
                raise ValueError("Original catalogue metadata source is unavailable")
            _, payload = original_parts[locator["response_sha256"]]
            native = _pointer(payload, locator["json_pointer"])
            outer = _pointer(payload, "/".join(locator["json_pointer"].split("/")[:-1]))
            if (
                outer["site_id"] != f"neotoma:site:{site_id}"
                or outer["collection_unit_id"] != f"neotoma:collection-unit:{unit_id}"
            ):
                raise ValueError("Original native metadata parent owner differs")
            lookup = row["current_metadata_lookup"]
            lookup_result = metadata_results[lookup["manifest_sha256"]]
            response = lookup_result.dataset_responses.get(dataset_id)
            if (
                response is None
                or _object(response)["data"] != []
                or sha256(response).hexdigest() != lookup["body_sha256"]
                or lookup.get("absence_certified") is not False
            ):
                raise ValueError(
                    "Historical catalogue lookup is not its declared successful-empty source"
                )
            source = {
                "source_kind": "original_relational_metadata",
                "body_sha256": locator["response_sha256"],
                "json_pointer": locator["json_pointer"],
                "current_metadata_lookup": lookup,
                "current_metadata_lookup_source": lookup_sources[
                    (lookup["manifest_sha256"], dataset_id)
                ],
            }
            site = {"siteid": site_id}
        else:
            if locator["response_sha256"] not in body_index:
                raise ValueError("Current native metadata body is unavailable")
            path, source = body_index[locator["response_sha256"]]
            payload = pinned_object(path, locator["response_sha256"], 32 * 1024 * 1024)
            native = _pointer(payload, locator["json_pointer"])
            site = _pointer(payload, "/".join(locator["json_pointer"].split("/")[:-2]))
            if (
                positive_native_id(site.get("siteid")) != site_id
                or positive_native_id(site.get("collectionunitid")) != unit_id
            ):
                raise ValueError(
                    "Native metadata site or collection unit owner differs"
                )
            source = {
                **source,
                "source_kind": "current_http_metadata",
                "json_pointer": locator["json_pointer"],
            }
            sites.append(
                {key: value for key, value in site.items() if key != "datasets"}
            )
        if (
            not isinstance(native, dict)
            or positive_native_id(native.get("datasetid")) != dataset_id
            or native.get("datasettype") != row["dataset_type"]
            or "database" not in native
            or native["database"] != row["database"]
            or native.get("doi", []) != row["dataset_doi_values"]
        ):
            raise ValueError(
                "Native metadata dataset/type/database/DOI owner identity differs"
            )
        metadata[dataset_id] = {
            "source": source,
            "native_dataset": native,
            "native_site": {
                key: value for key, value in site.items() if key != "datasets"
            },
        }
    roots = {**(source_captures or {}), **resource_captures}
    selected: dict[str, tuple[str, dict[str, Any]]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    qualifications: dict[str, dict[str, Any]] = {}
    source_snapshots: dict[str, dict[str, Any]] = {}
    for digest, directory in resource_captures.items():
        result = replay_neotoma_resource_capture(
            directory,
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        for entry in result.resources:
            if entry["resource_key"] in selected:
                raise ValueError("Duplicate selected resource/version capture")
            selected[entry["resource_key"]] = digest, entry
        qualification = qualify_neotoma_frozen_capture(
            directory,
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        qualifications.update(
            (entry["resource_key"], entry) for entry in qualification["resources"]
        )
        snapshots = qualify_neotoma_frozen_snapshot_capture(
            directory,
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        source_snapshots.update(
            (entry["resource_key"], entry) for entry in snapshots["resources"]
        )
    used_roots = set()
    pending = list(resource_captures)
    while pending:
        digest = pending.pop()
        if digest in used_roots:
            continue
        if digest not in roots:
            raise ValueError("Catalogue source ancestor resolver is missing")
        used_roots.add(digest)
        manifest = pinned_object(
            roots[digest] / "capture-manifest.json", digest, 16 * 1024 * 1024
        )
        control = pinned_object(
            roots[digest] / "request-plan.json",
            manifest["plan_sha256"],
            4 * 1024 * 1024,
        )
        pending.extend(control["input_captures"])
    roots = {digest: roots[digest] for digest in used_roots}
    for digest, directory in roots.items():
        manifests[digest] = pinned_object(
            directory / "capture-manifest.json", digest, 16 * 1024 * 1024
        )
        descriptors[digest] = describe_capture(directory, digest, "resources")
    return CatalogueSources(
        roster,
        metadata,
        sites,
        originals,
        descriptors,
        selected,
        dict(roots),
        manifests,
        qualifications,
        retained_sources or {},
        source_snapshots,
    )
