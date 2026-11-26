"""Capture bounded Nordic browser candidate bytes under a physical source seal."""

import argparse
import base64
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from types import MappingProxyType

from bijux_pollenomics.core.filesystem import (
    BoundedInputTree,
    DirectoryAnchor,
    OwnedTreeWriter,
    read_regular_file,
)
from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement


def capture_candidate(candidate: Path) -> Mapping[str, bytes]:
    """Return immutable bytes only after the candidate namespace is rechecked."""
    root = candidate.absolute()
    with BoundedInputTree(root, max_bytes=128 * 1024 * 1024, max_files=1024) as tree:
        result = {name: tree.read(root / name) for name in sorted(tree.files)}
        tree.validate()
    return MappingProxyType(result)


def validate_candidate_closure(
    candidate: Mapping[str, bytes], reference: Mapping[str, bytes]
) -> None:
    """Compare an input snapshot to an independently regenerated source candidate."""
    if "generation.json" not in candidate or "generation.json" not in reference:
        raise ValueError("Nordic candidate generation is missing")
    actual = json.loads(candidate["generation.json"])
    expected = json.loads(reference["generation.json"])
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        raise ValueError("Nordic candidate generation is invalid")
    fields = (
        "schema_version",
        "source_atlas_build_id",
        "candidate_build_id",
        "countries",
        "source_records",
        "selected_source_record_equality",
        "scientific_posture",
    )
    if (
        any(actual.get(key) != expected.get(key) for key in fields)
        or actual.get("schema_version") != "atlas-nordic-retained-source-candidate.v1"
        or actual.get("selected_source_record_equality") is not True
    ):
        raise ValueError("Nordic candidate source closure differs")
    expected_inputs = expected.get("inputs_sha256")
    actual_inputs = actual.get("inputs_sha256")
    prefixes = (
        "docs/report/regions/nordic/",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/assets/map/",
    )
    exact = {
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/geography.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_publication.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py",
    }
    if not isinstance(expected_inputs, dict) or not isinstance(actual_inputs, dict):
        raise ValueError("Nordic candidate input inventory differs")
    stable = {
        key: value
        for key, value in expected_inputs.items()
        if isinstance(key, str) and (key.startswith(prefixes) or key in exact)
    }
    if "docs/report/regions/nordic/nordic_map.html" not in stable or any(
        actual_inputs.get(key) != value for key, value in stable.items()
    ):
        raise ValueError("Nordic candidate input inventory differs")
    records = actual.get("source_records")
    if (
        not isinstance(records, list)
        or len(records) != 8
        or any(
            not isinstance(row, dict) or not isinstance(row.get("record_id"), str)
            for row in records
        )
        or len({row["record_id"] for row in records}) != 8
    ):
        raise ValueError("Nordic candidate source records differ")
    actual_files = {
        key: value for key, value in candidate.items() if key != "generation.json"
    }
    expected_files = {
        key: value for key, value in reference.items() if key != "generation.json"
    }
    if actual_files != expected_files or "index.html" not in actual_files:
        raise ValueError("Nordic candidate asset closure differs")


def validate_generation_inputs(repository: Path, generation: dict[str, object]) -> None:
    """Require every declared source input to retain its exact literal bytes."""
    records = generation.get("inputs_sha256")
    if not isinstance(records, dict) or not records or len(records) > 1024:
        raise ValueError("Nordic generation input inventory differs")
    total = 0
    root = repository.absolute()
    for name, expected in records.items():
        if not isinstance(name, str) or not name or "\\" in name:
            raise ValueError("Nordic generation input path differs")
        path = Path(name)
        if (
            path.as_posix() != name
            or path.is_absolute()
            or any(part in {".", ".."} for part in path.parts)
        ):
            raise ValueError("Nordic generation input path differs")
        if (
            not isinstance(expected, str)
            or len(expected) != 64
            or any(c not in "0123456789abcdef" for c in expected)
        ):
            raise ValueError("Nordic generation input digest differs")
        payload = read_regular_file(root / path, max_bytes=64 * 1024 * 1024)
        total += len(payload)
        if (
            total > 1024 * 1024 * 1024
            or hashlib.sha256(payload).hexdigest() != expected
        ):
            raise ValueError("Nordic generation input bytes differ")


def prepare_candidate(
    repository: Path, candidate: Path, reference_output: Path
) -> Mapping[str, bytes]:
    """Seal candidate bytes and compare with a fresh retained-source owner replay."""
    from .nordic_source_candidate import generate_nordic_source_candidate

    captured = capture_candidate(candidate)
    generation = json.loads(captured["generation.json"])
    if not isinstance(generation, dict):
        raise ValueError("Nordic candidate generation is invalid")
    validate_generation_inputs(repository, generation)
    generate_nordic_source_candidate(repository, reference_output)
    reference = capture_candidate(reference_output)
    reference_generation = json.loads(reference["generation.json"])
    validate_generation_inputs(repository, reference_generation)
    validate_candidate_closure(captured, reference)
    validate_generation_inputs(repository, reference_generation)
    validate_generation_inputs(repository, generation)
    return captured


def validate_output_destination(repository: Path, output: Path) -> Path:
    """Reserve an absent output path beneath the repository artifact root."""
    root = repository.absolute()
    target = output.absolute()
    artifacts = root / "artifacts"
    if (
        root.resolve(strict=True) != root
        or not artifacts.is_dir()
        or artifacts.is_symlink()
        or not target.is_relative_to(artifacts)
        or target == artifacts
        or target.exists()
        or target.is_symlink()
        or not target.parent.is_dir()
        or target.parent.resolve(strict=True) != target.parent
    ):
        raise ValueError("Nordic browser requires an absent repository artifact output")
    return target


def required_candidate_assets(candidate: Mapping[str, bytes]) -> set[str]:
    """Identify the map assets needed to inspect every selected source context."""
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.index_transport import (
        decode_index_payloads,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        candidate["index.html"].decode(),
        re.S,
    )
    if match is None:
        raise ValueError("candidate bootstrap missing")
    manifest = json.loads(match.group(1))
    inventory = normalize_asset_inventory(manifest["assets"])

    def chunk(row: dict[str, object]) -> dict[str, object]:
        path = str(row["path"])
        payload = candidate[path]
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError("candidate manifest digest differs")
        decoded_size = row.get("decoded_byte_count")
        if decoded_size is not None and (type(decoded_size) is not int):
            raise ValueError("candidate decoded byte count differs")
        return decode_chunk_script(
            payload,
            expected_asset_key=str(row["asset_key"]),
            expected_payload_sha256=str(row["payload_sha256"]),
            expected_payload_encoding=str(row["payload_encoding"]),
            expected_decoded_byte_count=decoded_size,
        )

    index_rows = [row for row in inventory if row["domain"] == "indexes"]
    indexes = decode_index_payloads(
        index_rows,
        {str(row["asset_key"]): chunk(row) for row in index_rows},
        manifest=manifest,
    )
    records = json.loads(candidate["generation.json"])["source_records"]
    record_assets = indexes.get("detail_record_asset_keys")
    if not isinstance(record_assets, dict):
        raise ValueError("candidate detail index differs")
    detail_keys = {record_assets[row["record_id"]] for row in records}
    selected = [
        row
        for row in inventory
        if row["domain"] in {"indexes", "provenance"}
        or (
            row["domain"] == "nodes"
            and row.get("layer_key") in {"sead-sites", "neotoma-pollen"}
        )
        or row["asset_key"] in detail_keys
    ]
    for row in selected:
        chunk(row)
    return {"index.html", *(str(row["path"]) for row in selected)}


def validate_browser_receipt(
    candidate: Mapping[str, bytes], receipt: dict[str, object], required: set[str]
) -> None:
    """Reconcile browser-observed rows and served bytes to the captured candidate."""
    generation_bytes = candidate.get("generation.json")
    if generation_bytes is None:
        raise ValueError("Nordic browser receipt generation is missing")
    generation = json.loads(generation_bytes)
    if not isinstance(generation, dict):
        raise ValueError("Nordic browser receipt generation is invalid")
    served = receipt.get("served_files_sha256")
    if (
        receipt.get("schema_version") != "atlas-nordic-source-browser-verification.v2"
        or receipt.get("status") != "PASS"
        or receipt.get("runtime_errors") != []
        or receipt.get("candidate_generation_sha256")
        != hashlib.sha256(generation_bytes).hexdigest()
        or receipt.get("candidate_build_id") != generation.get("candidate_build_id")
        or receipt.get("source_atlas_build_id")
        != generation.get("source_atlas_build_id")
        or not isinstance(served, dict)
        or not required.issubset(served)
        or "index.html" not in served
        or not any(isinstance(name, str) and ".atlas-nodes." in name for name in served)
        or not any(
            isinstance(name, str) and ".atlas-details." in name for name in served
        )
    ):
        raise ValueError("Nordic browser receipt is unbound")
    for name, digest in served.items():
        if (
            not isinstance(name, str)
            or name not in candidate
            or not isinstance(digest, str)
            or hashlib.sha256(candidate[name]).hexdigest() != digest
        ):
            raise ValueError("Nordic browser receipt served bytes differ")
    records = generation.get("source_records")
    tables = receipt.get("chronology_tables")
    if (
        not isinstance(records, list)
        or len(records) != 8
        or any(
            not isinstance(row, dict) or not isinstance(row.get("record_id"), str)
            for row in records
        )
        or not isinstance(tables, list)
        or len(tables) != 16
    ):
        raise ValueError("Nordic browser receipt record inventory differs")
    by_id = {row["record_id"]: row for row in records}
    if len(by_id) != 8:
        raise ValueError("Nordic browser receipt record identity differs")
    seen: set[tuple[int, str]] = set()
    for row in tables:
        if (
            not isinstance(row, dict)
            or type(row.get("width")) is not int
            or row.get("width") not in {390, 1440}
            or not isinstance(row.get("record_id"), str)
            or row["record_id"] not in by_id
        ):
            raise ValueError("Nordic browser receipt chronology identity differs")
        identity = (row["width"], row["record_id"])
        if identity in seen:
            raise ValueError("Nordic browser receipt chronology identity differs")
        seen.add(identity)
        chronology = by_id[row["record_id"]].get("chronology")
        if not isinstance(chronology, dict):
            raise ValueError("Nordic browser receipt chronology differs")
        expected_rows = chronology.get("records")
        if isinstance(expected_rows, list):
            if row.get("all_source_cells_equal") is not True or row.get("rows") != len(
                expected_rows
            ):
                raise ValueError("Nordic browser receipt chronology differs")
        elif (
            row.get("status") != "unavailable"
            or row.get("reason_code") != chronology.get("reason_code")
            or row.get("source_null_not_zero") is not True
        ):
            raise ValueError("Nordic browser receipt chronology differs")
    if seen != {(width, key) for width in (390, 1440) for key in by_id}:
        raise ValueError("Nordic browser receipt chronology inventory differs")


def publish_result(
    destination: Path, staging: Path, receipt: bytes, log: bytes
) -> None:
    """Attach only a completed, checked two-file result into an absent destination."""

    def validate(root: Path) -> None:
        with BoundedInputTree(root, max_bytes=16 * 1024 * 1024, max_files=2) as tree:
            if (
                set(tree.files) != {"receipt.json", "browser.log"}
                or tree.read(root / "receipt.json") != receipt
                or tree.read(root / "browser.log") != log
            ):
                raise ValueError("Nordic browser output changed")
            tree.validate()

    with OwnedTreeWriter(
        staging / "result-candidate", max_bytes=16 * 1024 * 1024, max_files=2
    ) as writer:
        writer.write_bytes("receipt.json", receipt)
        writer.write_bytes("browser.log", log)
        with DirectoryAnchor(staging / "result-recovery", create=True) as recovery:
            publish_owned_replacement(
                writer,
                final=destination,
                prior=None,
                recovery=recovery,
                validate=validate,
            )


def run(
    repository: Path,
    candidate: Path,
    output: Path,
    browser: Path,
    generation_sha256: str,
) -> dict[str, object]:
    """Verify source closure and run a browser only against captured candidate bytes."""
    root = repository.absolute()
    destination = validate_output_destination(root, output)
    candidate_root = candidate.absolute()
    artifacts = root / "artifacts"
    if (
        not candidate_root.is_relative_to(artifacts)
        or candidate_root == artifacts
        or destination.is_relative_to(candidate_root)
        or candidate_root.is_relative_to(destination)
    ):
        raise ValueError(
            "Nordic browser candidate and output must be disjoint repository artifacts"
        )
    if len(generation_sha256) != 64 or any(
        c not in "0123456789abcdef" for c in generation_sha256
    ):
        raise ValueError("Nordic browser generation digest is invalid")
    verifier_path = (
        root
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic-country-captured.mjs"
    )
    transport_path = (
        root
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_captured_transport.mjs"
    )
    verifier_bytes = read_regular_file(verifier_path, max_bytes=2 * 1024 * 1024)
    transport_bytes = read_regular_file(transport_path, max_bytes=2 * 1024 * 1024)
    with tempfile.TemporaryDirectory(
        prefix="nordic-browser-", dir=artifacts
    ) as directory:
        temporary = Path(directory)
        captured = prepare_candidate(root, candidate_root, temporary / "reference")
        reference_generation = json.loads(
            (temporary / "reference" / "generation.json").read_bytes()
        )
        generation_bytes = captured["generation.json"]
        if hashlib.sha256(generation_bytes).hexdigest() != generation_sha256:
            raise ValueError("Nordic browser generation digest differs")
        generation = json.loads(generation_bytes)
        payload = {
            "files": {
                name: base64.b64encode(content).decode("ascii")
                for name, content in captured.items()
            },
            "verifier_sha256": hashlib.sha256(verifier_bytes).hexdigest(),
            "transport_sha256": hashlib.sha256(transport_bytes).hexdigest(),
            "transport_source": base64.b64encode(transport_bytes).decode("ascii"),
        }
        browser_output = temporary / "browser"
        completed = subprocess.run(
            [
                "node",
                "--input-type=module",
                "-e",
                verifier_bytes.decode("utf-8"),
                str(browser_output),
                str(browser.absolute()),
            ],
            input=json.dumps(payload).encode(),
            capture_output=True,
            timeout=180,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"Nordic browser verifier failed with exit {completed.returncode}"
            )
        receipt_bytes = read_regular_file(
            browser_output / "receipt.json", max_bytes=8 * 1024 * 1024
        )
        log_bytes = read_regular_file(
            browser_output / "browser.log", max_bytes=8 * 1024 * 1024
        )
        receipt = json.loads(receipt_bytes)
        if not isinstance(receipt, dict):
            raise ValueError("Nordic browser receipt is invalid")
        validate_browser_receipt(captured, receipt, required_candidate_assets(captured))
        if (
            receipt.get("verifier_sha256") != payload["verifier_sha256"]
            or receipt.get("transport_sha256") != payload["transport_sha256"]
        ):
            raise ValueError("Nordic browser verifier identity differs")
        if capture_candidate(candidate_root) != captured:
            raise ValueError("Nordic browser candidate changed during verification")
        validate_generation_inputs(root, generation)
        validate_generation_inputs(root, reference_generation)
        receipt["independent_replay_inputs_sha256"] = reference_generation[
            "inputs_sha256"
        ]
        if (
            read_regular_file(verifier_path, max_bytes=2 * 1024 * 1024)
            != verifier_bytes
            or read_regular_file(transport_path, max_bytes=2 * 1024 * 1024)
            != transport_bytes
        ):
            raise ValueError("Nordic browser verifier source changed")
        receipt["producer_validation"] = {
            "source_candidate_regenerated": True,
            "selected_records_equal": True,
            "candidate_asset_bytes_equal": True,
            "posture": "retained source correspondence; not scientific admission or independent execution attestation",
        }
        receipt["candidate_files_sha256"] = {
            name: hashlib.sha256(content).hexdigest()
            for name, content in captured.items()
        }
        output_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
        validate_output_destination(root, destination)
        publish_result(destination, temporary, output_bytes, log_bytes)
    return receipt


def main() -> None:
    """Run the candidate-bound Nordic browser verifier to a fresh artifact path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--browser", required=True, type=Path)
    parser.add_argument("--generation-sha256", required=True)
    args = parser.parse_args()
    run(
        args.repository,
        args.candidate,
        args.output,
        args.browser,
        args.generation_sha256,
    )


if __name__ == "__main__":
    main()
