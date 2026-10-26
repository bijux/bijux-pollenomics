"""Compare a current ABBO provider capture with retained native source evidence."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.roundtrip import (
    SURFACES,
    native_hierarchy,
    reconcile_hierarchy,
)

_OLD_PART = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json")
_URLS = {
    "dataset_download": "https://api.neotomadb.org/v2.0/data/downloads/19913",
    "dataset_metadata": "https://api.neotomadb.org/v2.0/data/datasets/19913",
    "neotoma_policy": "https://www.neotomadb.org/data/data-use-and-embargo-policy",
    "epd_policy": "https://epdweblog.org/epd_data_home/epd_policy/",
}


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Neotoma source must contain an object")
    return value


def _array(value: object) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError("Neotoma source must contain an array")
    return value


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("Neotoma source contains a duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> object:
    raise ValueError(f"Nonfinite Neotoma source token: {value}")


def _json(content: bytes, *, exact_numbers: bool = False) -> dict[str, Any]:
    return _object(
        json.loads(
            content,
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
            parse_float=Decimal if exact_numbers else float,
        )
    )


def _changed_number(value: object) -> object:
    if not isinstance(value, Decimal):
        raise TypeError("Unsupported changed source value")
    return {"json_numeric_kind": "decimal", "exact_value": str(value)}


def _retained_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    selected = []
    for row_value in _array(payload.get("rows")):
        row = _object(row_value)
        dataset = _object(
            _object(_object(row.get("site")).get("collectionunit")).get("dataset")
        )
        if dataset.get("datasetid") == 19913:
            selected.append(row)
    if len(selected) != 1:
        raise ValueError("Retained Neotoma dataset identity is missing or duplicated")
    return selected[0]


def _read(path: Path, bound: int) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > bound:
        raise ValueError(f"Neotoma input is not a bounded regular file: {path}")
    return path.read_bytes()


def _utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Neotoma capture timestamp is missing")
    instant = datetime.fromisoformat(value)
    offset = instant.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("Neotoma capture timestamp is not UTC")
    return instant


def read_capture(
    directory: Path, expected_manifest_sha256: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read the completed acquisition owner's actual schema without copying inputs."""
    manifest_bytes = _read(directory / "capture-manifest.json", 100_000)
    if sha256(manifest_bytes).hexdigest() != expected_manifest_sha256:
        raise ValueError("Neotoma capture manifest identity differs")
    manifest = _json(manifest_bytes)
    if (
        manifest.get("schema_version") != "neotoma-single-dataset-http-capture.v1"
        or manifest.get("status") != "complete"
    ):
        raise ValueError("Neotoma capture is incomplete or has an unknown schema")
    start, end = (
        _utc(manifest.get("capture_utc_start")),
        _utc(manifest.get("capture_utc_end")),
    )
    if start > end or manifest.get("historical_capture_replaced") is not False:
        raise ValueError("Neotoma capture time or historical boundary differs")
    records = manifest.get("records")
    if not isinstance(records, list) or len(records) != len(_URLS):
        raise ValueError("Neotoma capture request population differs")
    bodies: dict[str, bytes] = {}
    for record_value in records:
        record = _object(record_value)
        role = record.get("role")
        if (
            not isinstance(role, str)
            or role not in _URLS
            or role in bodies
            or record.get("requested_url") != _URLS[role]
        ):
            raise ValueError("Neotoma capture endpoint identity differs")
        if record.get("request_target") != urlsplit(_URLS[role]).path:
            raise ValueError("Neotoma capture request target differs")
        filename = record.get("body_file")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError("Neotoma capture body path is not a direct member")
        body = _read(directory / filename, 4 * 1024 * 1024)
        if record.get("retained_body_sha256") != sha256(body).hexdigest() or record.get(
            "retained_body_bytes"
        ) != len(body):
            raise ValueError("Neotoma capture response body identity differs")
        request_start, request_end = (
            _utc(record.get("utc_start")),
            _utc(record.get("utc_end")),
        )
        if (
            not start <= request_start <= request_end <= end
            or record.get("request_method") != "GET"
            or record.get("http_status") != 200
            or record.get("body_complete") is not True
            or record.get("terminal_status") != "complete_http_200"
        ):
            raise ValueError("Neotoma capture request did not complete successfully")
        if not isinstance(record.get("response_headers"), list) or not isinstance(
            record.get("request_headers"), list
        ):
            raise ValueError("Neotoma capture HTTP headers are absent")
        for name in ("response_headers", "request_headers"):
            if any(
                not isinstance(pair, list)
                or len(pair) != 2
                or any(not isinstance(value, str) for value in pair)
                for pair in record[name]
            ):
                raise ValueError("Neotoma capture header pairs are malformed")
        bodies[role] = body
    rights = _object(manifest.get("rights"))
    if rights.get("licence_url") != "https://creativecommons.org/licenses/by/4.0/":
        raise ValueError("Neotoma current attribution terms differ")
    payload = _json(bodies["dataset_download"])
    if (
        payload.get("status") != "success"
        or not isinstance(payload.get("data"), list)
        or len(payload["data"]) != 1
    ):
        raise ValueError("Neotoma download is not one successful dataset response")
    row = _object(payload["data"][0])
    _core(row)
    metadata = _json(bodies["dataset_metadata"])
    if metadata.get("status") != "success" or len(_array(metadata.get("data"))) != 1:
        raise ValueError("Neotoma dataset metadata scope differs")
    site = _object(_object(metadata["data"][0]).get("site"))
    if any(
        type(site.get(key)) is not int for key in ("siteid", "collectionunitid")
    ) or (site.get("siteid"), site.get("collectionunitid"), site.get("handle")) != (
        13338,
        14910,
        "ABBO",
    ):
        raise ValueError("Neotoma metadata core identity differs")
    datasets = site.get("datasets")
    if (
        not isinstance(datasets, list)
        or len(datasets) != 1
        or _object(datasets[0]).get("datasetid") != 19913
        or _object(datasets[0]).get("doi") != _core(row)["doi"]
    ):
        raise ValueError("Neotoma metadata and download dataset identities differ")
    return row, manifest


def _core(row: Mapping[str, Any]) -> dict[str, Any]:
    site = _object(row.get("site"))
    unit = _object(site.get("collectionunit"))
    dataset = _object(unit.get("dataset"))
    if any(
        type(value) is not int
        for value in (
            site.get("siteid"),
            unit.get("collectionunitid"),
            dataset.get("datasetid"),
        )
    ) or (
        site.get("siteid"),
        unit.get("collectionunitid"),
        unit.get("handle"),
        dataset.get("datasetid"),
    ) != (13338, 14910, "ABBO", 19913):
        raise ValueError("Neotoma download core identity differs")
    return dataset


def source_changes(
    prior: object, current: object, path: str = ""
) -> list[dict[str, object]]:
    """Compare exact decoded values and number kinds, not JSON number spellings."""
    if type(prior) is not type(current):
        return [
            {"path": path, "kind": "type_changed", "prior": prior, "current": current}
        ]
    changes: list[dict[str, object]] = []
    if isinstance(prior, dict) and isinstance(current, dict):
        for key in sorted(prior.keys() | current.keys()):
            pointer = f"{path}/{key.replace('~', '~0').replace('/', '~1')}"
            if key not in prior:
                changes.append(
                    {"path": pointer, "kind": "added", "current": current[key]}
                )
            elif key not in current:
                changes.append(
                    {"path": pointer, "kind": "removed", "prior": prior[key]}
                )
            else:
                changes.extend(source_changes(prior[key], current[key], pointer))
    elif isinstance(prior, list) and isinstance(current, list):
        for index in range(max(len(prior), len(current))):
            if index >= len(prior):
                changes.append(
                    {
                        "path": f"{path}/{index}",
                        "kind": "added",
                        "current": current[index],
                    }
                )
            elif index >= len(current):
                changes.append(
                    {
                        "path": f"{path}/{index}",
                        "kind": "removed",
                        "prior": prior[index],
                    }
                )
            else:
                changes.extend(
                    source_changes(prior[index], current[index], f"{path}/{index}")
                )
    elif prior != current:
        changes.append(
            {"path": path, "kind": "value_changed", "prior": prior, "current": current}
        )
    return changes


def compare_rows(
    prior: dict[str, Any],
    current: dict[str, Any],
    *,
    prior_source: str,
    current_source: str,
    prior_values: dict[str, Any],
    current_values: dict[str, Any],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    """Exercise the existing native projection separately for both source states."""
    comparisons: dict[str, object] = {}
    for label, row, identity in (
        ("retained", prior, prior_source),
        ("current", current, current_source),
    ):
        _core(row)
        snapshot = build_neotoma_relational_snapshot(
            [row],
            source_snapshot_id=identity,
            build_id="neotoma-single-core-capture-comparison",
        )
        surfaces = {
            name: [_object(record) for record in _array(snapshot[name])]
            for name in SURFACES
        }
        result = reconcile_hierarchy(
            native_hierarchy([row]),
            surfaces,
            [_object(record) for record in _array(snapshot["conflicts"])],
        )
        comparisons[label] = {
            "source_snapshot_id": identity,
            "native_preservation": result,
            "reconciliation": snapshot["reconciliation"],
            "conflicts": snapshot["conflicts"],
            "orphans": snapshot["orphans"],
        }
    changes = source_changes(prior_values, current_values)
    return {
        "captures": comparisons,
        "source_value_equal": not changes,
        "changed_paths": len(changes),
        "change_kinds": dict(Counter(str(row["kind"]) for row in changes)),
        "array_comparison": "literal positional source arrays; no identity matching or reordering",
        "numeric_comparison": "exact JSON numeric values and integer-versus-decimal kind; wire lexical formatting is not compared",
        "native_projection_numeric_semantics": "unchanged Python JSON binary64 decoding",
        "changed_decimal_serialization": "tagged object with json_numeric_kind=decimal and unrounded exact_value string",
        "historical_http_custody_recovered": False,
        "scientific_admission": False,
        "canonical_data_replaced": False,
    }, changes


def run(
    repository: Path, capture: Path, expected_manifest_sha256: str, output: Path
) -> dict[str, object]:
    """Write a bounded comparison only; native source bytes remain in their owners."""
    repository = repository.resolve(strict=True)
    if (
        output.exists()
        or output.is_symlink()
        or not output.resolve().is_relative_to(repository / "artifacts")
    ):
        raise ValueError(
            "Neotoma comparison requires a new repository artifact directory"
        )
    current, manifest = read_capture(capture, expected_manifest_sha256)
    old_bytes = _read(repository / _OLD_PART, 32_000_000)
    # Return only the selected core so each full part tree is released before
    # decoding the other numeric representation or constructing either snapshot.
    prior = _retained_row(_json(old_bytes))
    prior_values = _retained_row(_json(old_bytes, exact_numbers=True))
    download = next(
        record for record in manifest["records"] if record["role"] == "dataset_download"
    )
    current_bytes = _read(capture / download["body_file"], 4 * 1024 * 1024)
    if sha256(current_bytes).hexdigest() != download["retained_body_sha256"]:
        raise ValueError("Neotoma capture response body changed before comparison")
    current_values = _object(
        _array(_json(current_bytes, exact_numbers=True).get("data"))[0]
    )
    report, changes = compare_rows(
        prior,
        current,
        prior_source=f"sha256:{sha256(old_bytes).hexdigest()}",
        current_source=f"sha256:{download['retained_body_sha256']}",
        prior_values=prior_values,
        current_values=current_values,
    )
    report.update(
        {
            "schema_version": "neotoma-current-abbo-capture-comparison.v1",
            "capture_identity": manifest["capture_identity"],
            "capture_manifest_sha256": expected_manifest_sha256,
            "capture_utc_start": manifest["capture_utc_start"],
            "capture_utc_end": manifest["capture_utc_end"],
            "retained_part": {
                "path": _OLD_PART.as_posix(),
                "sha256": sha256(old_bytes).hexdigest(),
            },
            "rights": manifest["rights"],
            "current_source_attribution": {
                key: _core(current).get(key)
                for key in ("doi", "database", "datasetpi", "datasetnotes")
            },
        }
    )
    # The named raw inputs are rechecked after projection; no wire history is inferred.
    read_capture(capture, expected_manifest_sha256)
    if _read(repository / _OLD_PART, 32_000_000) != old_bytes:
        raise ValueError("Retained Neotoma input changed during comparison")
    encoded = (
        json.dumps(
            report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
        ).encode()
        + b"\n"
    )
    differences = (
        json.dumps(
            changes,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
            default=_changed_number,
        ).encode()
        + b"\n"
    )
    if len(encoded) > 100_000 or len(differences) > 2_000_000:
        raise ValueError("Neotoma comparison exceeds the declared output bounds")
    output.mkdir(parents=True)
    (output / "report.json").write_bytes(encoded)
    (output / "changes.json").write_bytes(differences)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--capture-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(
        args.repository, args.capture, args.capture_manifest_sha256, args.output
    )
    preserved = all(
        _object(_object(value)["native_preservation"])["match"]
        for value in _object(report["captures"]).values()
    )
    print(
        json.dumps(
            {"native_preservation": preserved, "changed_paths": report["changed_paths"]}
        )
    )
    return 0 if preserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
