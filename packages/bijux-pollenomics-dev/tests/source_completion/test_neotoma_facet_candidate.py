"""Controlled reconciliation never exports native publication content."""

from copy import deepcopy
import os
from pathlib import Path
from typing import Any

import pytest


def inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    fields = ["dataset_id", "source_dataset_id", "source_payload"]
    status_fields = [
        "dataset_id",
        "status",
        "publication_count",
        "source_primary_count",
        "request_url",
        "retrieved_at_utc",
        "response_sha256",
        "response_byte_count",
    ]
    record = {
        "record_id": "neotoma:site:12",
        "tabs": {
            "samples": {
                "datasets": {
                    "fields": fields,
                    "records": [
                        [
                            "neotoma:dataset:21",
                            21,
                            {"datasetid": 21, "citation": "PRIVATE"},
                        ],
                        ["neotoma:dataset:22", 22, {"datasetid": 22}],
                    ],
                    "record_count": 2,
                }
            },
            "provenance": {
                "publication_capture": {
                    "source_id": "neotoma/publication-links/2026-09-29",
                    "manifest_sha256": "d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da",
                    "epoch_posture": "separate_provider_capture_not_original_pollen_snapshot",
                    "datasets": {
                        "fields": status_fields,
                        "records": [
                            [
                                "neotoma:dataset:21",
                                "not_captured",
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                            ],
                            [
                                "neotoma:dataset:22",
                                "not_captured",
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                            ],
                        ],
                        "record_count": 2,
                    },
                }
            },
        },
    }
    selected = []
    declarations = []
    for dataset in (21, 22):
        row = {
            "site_id": 12,
            "dataset_id": dataset,
            "observation_id": f"{dataset:064x}:/facets/0",
            "capsule_sha256": "a" * 64,
            "capture_sha256": f"{dataset:064x}",
            "receipt_sha256": f"{dataset + 100:064x}",
            "body_sha256": "b" * 64,
        }
        selected.append(row)
        declarations.append(
            {
                "site_id": 12,
                "dataset_id": dataset,
                "observation_id": row["observation_id"],
                "capsule_manifest_sha256": row["capsule_sha256"],
                "capture_manifest_sha256": row["capture_sha256"],
                "receipt_sha256": row["receipt_sha256"],
                "body_sha256": row["body_sha256"],
                "capture_terminal_status": "received_complete_unqualified_facet",
                "derived_source_qualification": "qualified_source_schema",
                "scientific_admission": "not_asserted",
                "source_declarations": {
                    "schema_version": "neotoma-scoped-facet-declarations.v1",
                    "capture_utc_start": "2026-11-15T00:00:00+00:00",
                    "capture_utc_end": "2026-11-15T00:00:01+00:00",
                    "request_utc_start": "2026-11-15T00:00:00+00:00",
                    "request_utc_end": "2026-11-15T00:00:01+00:00",
                    "request_url": f"https://api.neotomadb.org/v2.0/data/datasets/{dataset}/publications",
                    "original_parent_scope": "authenticated_original_parent_scope",
                    "original_scope_role": "development_resource_discovery",
                    "current_scope_role": "development_resource_discovery",
                    "scientific_admission": "not_asserted",
                },
            }
        )
    return [record], selected, declarations


def test_exact_join_and_no_native_content() -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.comparison import (
        reconcile,
    )

    records, selection, declarations = inputs()
    prior = deepcopy(records)
    result = reconcile(
        records,
        selection,
        declarations,
        expected_sites=1,
        expected_datasets=2,
        expected_selected=2,
    )
    assert (
        records == prior
        and len(result) == 2
        and "PRIVATE" not in repr(result)
        and "primary" not in repr(result)
        and "count" not in repr(result)
    )
    assert (
        result[0]["body_sha256"] == result[1]["body_sha256"]
        and result[0]["receipt_sha256"] != result[1]["receipt_sha256"]
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_site",
        "wrong_source_payload",
        "duplicate_dataset",
        "missing_selection",
        "wrong_status",
        "receipt_swap",
        "body_swap",
        "unqualified",
        "role",
        "duplicate_observation",
    ],
)
def test_reconciliation_refuses_substitution(mutation: str) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.comparison import (
        reconcile,
    )

    records, selection, declarations = inputs()
    if mutation == "wrong_site":
        selection[0]["site_id"] = 13
    elif mutation == "wrong_source_payload":
        records[0]["tabs"]["samples"]["datasets"]["records"][0][2]["datasetid"] = 22
    elif mutation == "duplicate_dataset":
        records[0]["tabs"]["samples"]["datasets"]["records"][1] = records[0]["tabs"][
            "samples"
        ]["datasets"]["records"][0]
    elif mutation == "missing_selection":
        selection.pop()
    elif mutation == "wrong_status":
        records[0]["tabs"]["provenance"]["publication_capture"]["datasets"]["records"][
            0
        ][1] = "no_publication_link"
    elif mutation == "receipt_swap":
        declarations[0]["receipt_sha256"] = declarations[1]["receipt_sha256"]
    elif mutation == "body_swap":
        declarations[0]["body_sha256"] = "c" * 64
    elif mutation == "unqualified":
        declarations[0]["derived_source_qualification"] = "unqualified_source_schema"
    elif mutation == "role":
        declarations[0]["source_declarations"]["current_scope_role"] = (
            "heldout_no_numerical_access"
        )
    else:
        selection[1]["observation_id"] = selection[0]["observation_id"]
    with pytest.raises(ValueError):
        reconcile(
            records,
            selection,
            declarations,
            expected_sites=1,
            expected_datasets=2,
            expected_selected=2,
        )


def test_private_output_exclusive_and_permissions(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.private_output import (
        write_private_receipt,
    )

    os.chmod(tmp_path, 0o700)
    path = tmp_path / "receipt.json"
    write_private_receipt(path, {"publication_allowed": False})
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_private_receipt(path, {"new": True})
    assert "publication_allowed" in path.read_text()


def test_bounded_static_details_decode_and_reject_changed_chunk(tmp_path: Path) -> None:
    import base64
    import gzip
    import hashlib
    import json

    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.static_details import (
        decode_details,
    )

    def digest(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    body = json.dumps(
        {
            "asset_key": "details:0",
            "build_id": "build",
            "records": [{"record_id": "neotoma:site:12"}],
        },
        separators=(",", ":"),
    ).encode()
    env = {
        "asset_key": "details:0",
        "payload_encoding": "gzip_base64",
        "payload_sha256": digest(body),
        "payload_gzip_base64": base64.b64encode(gzip.compress(body, mtime=0)).decode(),
    }
    raw = (
        b"globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
        + json.dumps(env).encode()
        + b");\n"
    )
    h = digest(raw)
    name = f"nordic.atlas-details.0000.{h[:16]}.js"
    (tmp_path / name).write_bytes(raw)
    fields = [
        "domain",
        "sha256",
        "payload_sha256",
        "decoded_byte_count",
        "byte_count",
        "record_count",
    ]
    bootstrap = {
        "build_id": "build",
        "assets": {
            "fields": fields,
            "records": [["details", h, digest(body), len(body), len(raw), 1]],
        },
    }
    html = (
        b'<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps(bootstrap).encode()
        + b"</script>"
    )
    (tmp_path / "nordic_map.html").write_bytes(html)
    files = {"nordic_map.html": digest(html), name: h}
    build, records = decode_details(tmp_path, files)
    assert build == "build" and records == [{"record_id": "neotoma:site:12"}]
    (tmp_path / name).write_bytes(raw + b"x")
    with pytest.raises(ValueError):
        decode_details(tmp_path, files)


def source_fixture(
    tmp_path: Path, selected: list[dict[str, Any]], declarations: list[dict[str, Any]]
) -> Path:
    import hashlib
    import json

    root = tmp_path / "capsules"
    root.mkdir()
    body = b'{"status":"success","message":"ok","data":[]}'

    def digest(x: bytes) -> str:
        return hashlib.sha256(x).hexdigest()

    for item, decl in zip(selected, declarations, strict=True):
        dataset = item["dataset_id"]
        receipt_name = (
            f"dataset-{dataset}-facet-publications-current-attempt-1.receipt.json"
        )
        body_name = f"dataset-{dataset}-facet-publications-current-attempt-1.body"
        receipt = {
            "expected_dataset_id": dataset,
            "expected_site_id": 12,
            "requested_url": decl["source_declarations"]["request_url"],
            "http_status": 200,
            "body_complete": True,
            "retained_body_sha256": digest(body),
            "retained_body_bytes": len(body),
            "utc_start": decl["source_declarations"]["request_utc_start"],
            "utc_end": decl["source_declarations"]["request_utc_end"],
        }
        rb = json.dumps(receipt).encode()
        entry = {
            "facet": "publications",
            "root_identity": {"dataset_id": dataset, "site_id": 12},
            "parent_scope_role": "development_resource_discovery",
            "terminal_status": "received_complete_unqualified_facet",
            "attempts": [
                {
                    "receipt_file": receipt_name,
                    "receipt_sha256": digest(rb),
                    "body_file": body_name,
                }
            ],
        }
        cap = {
            "schema_version": "neotoma-dataset-facet-scoped-http-capture.v1",
            "capture_utc_start": decl["source_declarations"]["capture_utc_start"],
            "capture_utc_end": decl["source_declarations"]["capture_utc_end"],
            "facets": [entry],
        }
        cb = json.dumps(cap).encode()
        capture = digest(cb)
        descriptor = {
            "kind": "facet",
            "files": {
                "capture-manifest.json": {"bytes": len(cb), "sha256": capture},
                receipt_name: {"bytes": len(rb), "sha256": digest(rb)},
                body_name: {"bytes": len(body), "sha256": digest(body)},
            },
        }
        capsule_body = json.dumps({"captures": {capture: descriptor}}).encode()
        capsule = digest(capsule_body)
        directory = root / capsule / "captures" / capture
        directory.mkdir(parents=True)
        (root / capsule / "manifest.json").write_bytes(capsule_body)
        (directory / "capture-manifest.json").write_bytes(cb)
        (directory / receipt_name).write_bytes(rb)
        (directory / body_name).write_bytes(body)
        item.update(
            capsule_sha256=capsule,
            capture_sha256=capture,
            receipt_sha256=digest(rb),
            body_sha256=digest(body),
            observation_id=capture + ":/facets/0",
        )
        decl.update(
            capsule_manifest_sha256=capsule,
            capture_manifest_sha256=capture,
            receipt_sha256=digest(rb),
            body_sha256=digest(body),
            observation_id=item["observation_id"],
        )
    return root


def test_source_receipts_distinguish_same_empty_body_by_dataset(tmp_path: Path) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.source_inputs import (
        verify_source_inputs,
    )

    _, selected, declarations = inputs()
    root = source_fixture(tmp_path, selected, declarations)
    verify_source_inputs(root, selected, declarations)
    declarations[0]["receipt_sha256"] = declarations[1]["receipt_sha256"]
    with pytest.raises(ValueError):
        verify_source_inputs(root, selected, declarations)


def test_not_captured_requires_null_metadata() -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.comparison import (
        reconcile,
    )

    records, selection, declarations = inputs()
    records[0]["tabs"]["provenance"]["publication_capture"]["datasets"]["records"][0][
        2
    ] = 0
    with pytest.raises(ValueError):
        reconcile(
            records,
            selection,
            declarations,
            expected_sites=1,
            expected_datasets=2,
            expected_selected=2,
        )


def test_declarations_reject_unexpected_nested_content() -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.comparison import (
        reconcile,
    )

    records, selection, declarations = inputs()
    declarations[0]["source_declarations"]["citation"] = "private"
    with pytest.raises(ValueError):
        reconcile(
            records,
            selection,
            declarations,
            expected_sites=1,
            expected_datasets=2,
            expected_selected=2,
        )


def test_post_link_cleanup_failure_keeps_complete_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate import (
        private_output,
    )

    os.chmod(tmp_path, 0o700)
    path = tmp_path / "receipt.json"
    original = os.unlink

    def refuse_staging(
        name: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        *,
        dir_fd: int | None = None,
    ) -> None:
        if isinstance(name, str) and name.startswith(".receipt-"):
            raise OSError("injected cleanup failure")
        original(name, dir_fd=dir_fd)

    monkeypatch.setattr(os, "unlink", refuse_staging)
    private_output.write_private_receipt(path, {"publication_allowed": False})
    assert (
        path.read_text().strip() == '{\n  "publication_allowed": false\n}'
        and path.stat().st_mode & 0o777 == 0o600
    )


def test_complete_candidate_audit_and_tampered_source_refusal(tmp_path: Path) -> None:
    from dataclasses import replace
    import hashlib
    import json

    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.static_details import (
        _PREFIX,
    )
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.workflow import (
        AuditInputs,
        PinnedInput,
        audit_to_private_receipt,
    )

    def digest(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    input_dir = tmp_path / "receipt-inputs"
    input_dir.mkdir()

    def pin(name: str, value: object) -> PinnedInput:
        data = json.dumps(value).encode()
        path = input_dir / name
        path.write_bytes(data)
        return PinnedInput(path, digest(data))

    records, selected, declarations = inputs()
    capsules = source_fixture(tmp_path, selected, declarations)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    body = json.dumps(
        {"build_id": "build", "asset_key": "details:0", "records": records}
    ).encode()
    body_sha = digest(body)
    envelope = {
        "asset_key": "details:0",
        "payload_sha256": body_sha,
        "payload_encoding": "json",
        "payload_json": body.decode(),
    }
    raw = _PREFIX + json.dumps(envelope).encode() + b");\n"
    chunk_sha = digest(raw)
    chunk_name = f"nordic.atlas-details.0000.{chunk_sha[:16]}.js"
    (candidate / chunk_name).write_bytes(raw)
    bootstrap = {
        "build_id": "build",
        "assets": {
            "fields": [
                "domain",
                "sha256",
                "payload_sha256",
                "decoded_byte_count",
                "byte_count",
                "record_count",
            ],
            "records": [["details", chunk_sha, body_sha, len(body), len(raw), 1]],
        },
    }
    html = (
        b'<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps(bootstrap).encode()
        + b"</script>"
    )
    (candidate / "nordic_map.html").write_bytes(html)
    producer = pin(
        "producer.json",
        {
            "status": "producer_returned",
            "output_files": {"nordic_map.html": digest(html), chunk_name: chunk_sha},
        },
    )
    supervisor = pin(
        "supervisor.json",
        {
            "status": "completed",
            "exit_code": 0,
            "timed_out": False,
            "producer_receipt_sha256": producer.sha256,
        },
    )
    assets = pin(
        "assets.json",
        {
            "status": "PASS",
            "producer_receipt_sha256": producer.sha256,
            "supervisor_receipt_sha256": supervisor.sha256,
            "candidate_build": "build",
            "document_sha256": digest(html),
        },
    )
    comparison = pin(
        "comparison.json",
        {
            "status": "PASS",
            "candidate_build": "build",
            "producer_receipt_sha256": producer.sha256,
            "supervisor_receipt_sha256": supervisor.sha256,
            "asset_receipt_sha256": assets.sha256,
            "reference_sha256": "b" * 64,
            "reference_receipt_sha256": "c" * 64,
            "reference_supervisor_sha256": "d" * 64,
            "sites": 1,
            "datasets": 2,
        },
    )
    comparison_supervisor = pin(
        "comparison-supervisor.json",
        {
            "status": "completed",
            "exit_code": 0,
            "timed_out": False,
            "verification_receipt_sha256": comparison.sha256,
        },
    )
    selection = pin("selection.json", {"status": "PASS", "selected": selected})
    source = pin(
        "source.json",
        {
            "status": "PASS",
            "source_revision": "a" * 40,
            "inventory_sha256": selection.sha256,
            "declaration_profile": "neotoma-scoped-facet-declarations.v1",
            "selected": declarations,
        },
    )
    source_supervisor = pin(
        "source-supervisor.json",
        {
            "status": "completed",
            "exit_code": 0,
            "timed_out": False,
            "experiment_receipt_sha256": source.sha256,
        },
    )
    config = AuditInputs(
        candidate,
        capsules,
        producer,
        supervisor,
        assets,
        comparison,
        comparison_supervisor,
        selection,
        source,
        source_supervisor,
        "a" * 40,
        "b" * 64,
        "c" * 64,
        "d" * 64,
        1,
        2,
        2,
    )
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    output = private / "receipt.json"
    wrong_assets = pin(
        "wrong-assets.json",
        {
            "status": "PASS",
            "producer_receipt_sha256": producer.sha256,
            "supervisor_receipt_sha256": supervisor.sha256,
            "candidate_build": "build",
            "document_sha256": "f" * 64,
        },
    )
    with pytest.raises(ValueError):
        audit_to_private_receipt(
            replace(config, asset_audit=wrong_assets), private / "wrong.json"
        )
    assert not (private / "wrong.json").exists()
    with pytest.raises(ValueError):
        audit_to_private_receipt(
            replace(config, expected_comparison_reference_sha256="e" * 64),
            private / "bad-reference.json",
        )
    assert not (private / "bad-reference.json").exists()
    original_comparison = json.loads(comparison.path.read_bytes())
    for field, value in (
        ("producer_receipt_sha256", "f" * 64),
        ("supervisor_receipt_sha256", "f" * 64),
        ("asset_receipt_sha256", "f" * 64),
        ("candidate_build", "different-build"),
        ("sites", True),
        ("datasets", 3),
    ):
        changed = {**original_comparison, field: value}
        changed_pin = pin(f"bad-{field}.json", changed)
        changed_supervisor = pin(
            f"bad-{field}-supervisor.json",
            {
                "status": "completed",
                "exit_code": 0,
                "timed_out": False,
                "verification_receipt_sha256": changed_pin.sha256,
            },
        )
        with pytest.raises(ValueError):
            audit_to_private_receipt(
                replace(
                    config,
                    source_comparison=changed_pin,
                    source_comparison_supervisor=changed_supervisor,
                ),
                private / f"bad-{field}.json",
            )
        assert not (private / f"bad-{field}.json").exists()
    failed_supervisor = pin(
        "failed-comparison-supervisor.json",
        {
            "status": "failed",
            "exit_code": 0,
            "timed_out": False,
            "verification_receipt_sha256": comparison.sha256,
        },
    )
    with pytest.raises(ValueError):
        audit_to_private_receipt(
            replace(config, source_comparison_supervisor=failed_supervisor),
            private / "failed-comparison.json",
        )
    assert not (private / "failed-comparison.json").exists()
    bad_supervisor = pin(
        "bad-comparison-supervisor.json",
        {
            "status": "completed",
            "exit_code": 0,
            "timed_out": False,
            "verification_receipt_sha256": "f" * 64,
        },
    )
    with pytest.raises(ValueError):
        audit_to_private_receipt(
            replace(config, source_comparison_supervisor=bad_supervisor),
            private / "bad-comparison.json",
        )
    assert not (private / "bad-comparison.json").exists()

    with pytest.raises(ValueError, match="outside input directories"):
        audit_to_private_receipt(config, candidate / "receipt.json")
    with pytest.raises(ValueError, match="outside input directories"):
        audit_to_private_receipt(config, capsules / "receipt.json")
    with pytest.raises(ValueError, match="outside input directories"):
        audit_to_private_receipt(config, input_dir / "receipt.json")
    audit_to_private_receipt(config, output)
    receipt = output.read_text()
    assert "PRIVATE" not in receipt and "publication_allowed" in receipt
    assert output.stat().st_mode & 0o777 == 0o600
    (candidate / chunk_name).write_bytes(raw + b"x")
    with pytest.raises(ValueError):
        audit_to_private_receipt(config, private / "refused.json")
    assert not (private / "refused.json").exists()
    assert output.read_text() == receipt


def test_private_receipt_failure_before_link_leaves_no_final(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate import (
        private_output,
    )

    os.chmod(tmp_path, 0o700)

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("injected link failure")

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(OSError):
        private_output.write_private_receipt(tmp_path / "receipt.json", {"safe": True})
    assert list(tmp_path.iterdir()) == []


def test_selected_cohort_must_cover_all_not_captured_datasets() -> None:
    from bijux_pollenomics_dev.source_completion.neotoma_facet_candidate.comparison import (
        reconcile,
    )

    records, selected, declarations = inputs()
    with pytest.raises(ValueError, match="population"):
        reconcile(
            records,
            selected[:1],
            declarations[:1],
            expected_sites=1,
            expected_datasets=2,
            expected_selected=1,
        )
