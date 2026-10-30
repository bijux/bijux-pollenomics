"""Join a separately dated, retained provider citation capture to native datasets.

The captured publication relation supplies provider metadata only. It neither
belongs to the original pollen acquisition nor selects a reviewed citation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path
import stat
from typing import cast

from bijux_pollenomics.analysis.lra.materialization.neotoma.publication_intake import (
    parse_dataset_publications,
)

from .io import _decode_json_object, _mapping, _regular_absolute_directory
from .records import _row_table

# Existing retained raw identity, also owned by the qualified publication source.
PUBLICATION_CAPTURE_MANIFEST_SHA256 = (
    "d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da"
)
PUBLICATION_SOURCE_API = "https://api.neotomadb.org/v2.0/data/datasets/"
PUBLICATION_CAPTURE_SOURCE_ID = "neotoma/publication-links/2026-09-29"
_DATASET_FIELDS = (
    "dataset_id",
    "status",
    "publication_count",
    "source_primary_count",
    "request_url",
    "retrieved_at_utc",
    "response_sha256",
    "response_byte_count",
)
_PUBLICATION_FIELDS = (
    "dataset_id",
    "publication_id",
    "source_primary_flag",
    "source_payload",
)


def _read(path: Path, limit: int) -> bytes:
    if not path.is_absolute():
        raise ValueError("Publication capture path must be absolute")
    for parent in reversed(path.parents):
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ValueError("Publication capture has a non-real ancestor")
    if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > limit:
        raise ValueError("Publication capture member is not a bounded regular file")
    return path.read_bytes()


def _positive(value: object) -> int:
    if type(value) is not int or not 0 < value <= 2**53 - 1:
        raise ValueError("Publication native ID must be a positive safe integer")
    return value


def _datasets(record: Mapping[str, object]) -> tuple[int, list[Mapping[str, object]]]:
    tabs = _mapping(record.get("tabs"), "source tabs")
    overview = _mapping(tabs.get("overview"), "source overview")
    site = overview.get("source_site_id")
    if not isinstance(site, str) or not site.isascii() or not site.isdigit():
        raise ValueError("Publication site identity is invalid")
    site_id = _positive(int(site))
    if site != str(site_id) or record.get("record_id") != f"neotoma:site:{site}":
        raise ValueError("Publication site identities disagree")
    table = _mapping(
        _mapping(tabs.get("samples"), "samples").get("datasets"), "datasets"
    )
    fields, rows = table.get("fields"), table.get("records")
    if not isinstance(fields, list) or not all(isinstance(x, str) for x in fields):
        raise ValueError("Publication dataset fields are invalid")
    if (
        len(set(fields)) != len(fields)
        or not isinstance(rows, list)
        or type(table.get("record_count")) is not int
        or table["record_count"] != len(rows)
        or table.get("identifier_prefixes")
    ):
        raise ValueError("Publication dataset table is invalid")
    result: list[Mapping[str, object]] = []
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, list) or len(row) != len(fields):
            raise ValueError("Publication dataset row is invalid")
        item = dict(zip(cast(list[str], fields), row, strict=True))
        native_id = _positive(item.get("source_dataset_id"))
        payload_id = _positive(
            _mapping(item.get("source_payload"), "native dataset").get("datasetid")
        )
        if (
            native_id in seen
            or item.get("dataset_id") != f"neotoma:dataset:{native_id}"
            or payload_id != native_id
        ):
            raise ValueError("Publication dataset identities disagree or repeat")
        seen.add(native_id)
        result.append(item)
    return site_id, result


def _manifest(payload: bytes) -> dict[int, Mapping[str, object]]:
    if hashlib.sha256(payload).hexdigest() != PUBLICATION_CAPTURE_MANIFEST_SHA256:
        raise ValueError("Publication capture manifest identity differs")
    value = _decode_json_object(payload, "publication capture manifest")
    rows = value.get("responses")
    if (
        value.get("schema_version") != "neotoma-candidate-publication-capture.v1"
        or value.get("source_api") != PUBLICATION_SOURCE_API
        or not isinstance(rows, list)
        or type(value.get("response_count")) is not int
        or value["response_count"] != len(rows)
    ):
        raise ValueError("Publication capture manifest contract differs")
    result: dict[int, Mapping[str, object]] = {}
    for row in rows:
        item = _mapping(row, "publication capture response")
        identity = _positive(item.get("dataset_id"))
        if (
            identity in result
            or item.get("path") != f"responses/dataset-{identity}-publications.json"
        ):
            raise ValueError("Publication capture response identity repeats or differs")
        result[identity] = item
    return result


def _response(
    root: Path,
    dataset_id: int,
    site_id: int,
    entry: Mapping[str, object],
) -> tuple[list[list[object]], list[object], tuple[Path, bytes]]:
    url = f"{PUBLICATION_SOURCE_API}{dataset_id}/publications"
    retrieved = entry.get("retrieved_at_utc")
    if (
        type(entry.get("http_status")) is not int
        or entry["http_status"] != 200
        or entry.get("url") != url
        or not isinstance(retrieved, str)
        or not retrieved
        or type(entry.get("bytes")) is not int
    ):
        raise ValueError("Publication response request metadata differs")
    path = root / str(entry["path"])
    payload = _read(path, 4 * 1024 * 1024)
    if len(payload) != entry["bytes"] or hashlib.sha256(
        payload
    ).hexdigest() != entry.get("sha256"):
        raise ValueError("Publication response bytes differ")
    links = parse_dataset_publications(dataset_id, payload)
    native = _decode_json_object(payload, "publication response")
    publications = cast(list[dict[str, object]], native["data"])
    by_id = {link["publication_id"]: link for link in links}
    result: list[list[object]] = []
    for item in publications:
        publication = _mapping(item["publication"], "native publication")
        _positive(publication.get("publicationid"))
        relations = publication.get("datasets")
        matching = [
            row
            for row in cast(list[object], relations)
            if isinstance(row, Mapping) and row.get("datasetid") == dataset_id
        ]
        if (
            len(matching) != 1
            or type(matching[0].get("datasetid")) is not int
            or type(matching[0].get("siteid")) is not int
            or matching[0]["siteid"] != site_id
        ):
            raise ValueError("Publication dataset/site relation differs")
        result.append(
            [
                f"neotoma:dataset:{dataset_id}",
                publication["publicationid"],
                by_id[publication["publicationid"]]["source_primary_flag"],
                publication,
            ]
        )
    if type(entry.get("publication_count")) is not int or entry[
        "publication_count"
    ] != len(result):
        raise ValueError("Publication capture count differs")
    count = sum(row[2] is True for row in result)
    status = (
        "no_publication_link"
        if not result
        else "one_source_primary_publication"
        if count == 1
        else "multiple_source_primary_publications"
        if count > 1
        else "no_source_primary_flag"
    )
    metadata = [
        f"neotoma:dataset:{dataset_id}",
        status,
        len(result),
        count,
        url,
        retrieved,
        entry["sha256"],
        len(payload),
    ]
    return result, metadata, (path, payload)


def attach_publication_capture(
    records: Sequence[dict[str, object]], root: Path
) -> None:
    """Attach only projected dataset responses, with independent capture identity.

    Original source snapshot/build values are left untouched. Uncaptured datasets
    differ from captured successful empty responses. Configured corrupt input
    refuses the build; no packet is accessed when the optional input is absent.
    """
    root = _regular_absolute_directory(root, "publication capture root")
    manifest_path = root / "capture-manifest.json"
    manifest_bytes = _read(manifest_path, 1024 * 1024)
    captured = _manifest(manifest_bytes)
    consumed = [(manifest_path, manifest_bytes)]
    seen: set[int] = set()
    for record in records:
        site_id, datasets = _datasets(record)
        dataset_rows: list[list[object]] = []
        publication_rows: list[list[object]] = []
        for dataset in datasets:
            native_id = _positive(dataset["source_dataset_id"])
            if native_id in seen:
                raise ValueError("Publication dataset is assigned to multiple sites")
            seen.add(native_id)
            entry = captured.get(native_id)
            if entry is None:
                dataset_rows.append(
                    [
                        dataset["dataset_id"],
                        "not_captured",
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                    ]
                )
                continue
            publications, metadata, source = _response(root, native_id, site_id, entry)
            publication_rows.extend(publications)
            dataset_rows.append(metadata)
            consumed.append(source)
        tabs = cast(dict[str, object], record["tabs"])
        provenance = cast(dict[str, object], tabs["provenance"])
        provenance["publication_capture"] = {
            "source_id": PUBLICATION_CAPTURE_SOURCE_ID,
            "manifest_sha256": PUBLICATION_CAPTURE_MANIFEST_SHA256,
            "source_api": PUBLICATION_SOURCE_API,
            "epoch_posture": "separate_provider_capture_not_original_pollen_snapshot",
            "datasets": _row_table(_DATASET_FIELDS, dataset_rows),
            "publications": _row_table(_PUBLICATION_FIELDS, publication_rows),
        }
    for path, payload in consumed:
        if _read(path, max(1024 * 1024, len(payload))) != payload:
            raise ValueError("Publication capture changed during projection")
