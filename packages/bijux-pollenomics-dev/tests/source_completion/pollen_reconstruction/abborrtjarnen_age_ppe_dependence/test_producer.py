"""Qualification, complete identity traversal and full fifty-scalar publication."""

from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence import (
    inputs,
    producer,
    quadratic_forms,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    WINDOWS,
)


def protocol_template() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (Path(__file__).resolve().parents[6] / inputs.PROTOCOL).read_text()
    )
    return result


def controlled_ledger(*, duplicate: bool = False, short: bool = False) -> bytes:
    target = io.BytesIO()
    fields = [
        "seed",
        "native_row",
        "complete",
        *[f"bin_{b}_status" for b in WINDOWS],
        *[f"cover_{b}_{t}" for b in WINDOWS for t in TAXON_IDS],
    ]
    with (
        gzip.GzipFile(fileobj=target, mode="wb", mtime=0) as compressed,
        io.TextIOWrapper(compressed, newline="") as stream,
    ):
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i in range(1 if short else 32000):
            row: dict[str, Any] = {
                "seed": (314159, 271828)[i // 16000],
                "native_row": 3502 + i % 16000,
                "complete": int(i != 31999),
            }
            if duplicate and i == 1:
                row["native_row"] = 3502
            for b in WINDOWS:
                missing = b == 4 and i == 31999
                row[f"bin_{b}_status"] = "empty_native_window" if missing else "defined"
                for t in TAXON_IDS:
                    row[f"cover_{b}_{t}"] = "" if missing else 0.2
            writer.writerow(row)
    return target.getvalue()


def source_result() -> dict[str, Any]:
    source: dict[str, Any] = {
        "source_commit": "controlled-producer",
        "count_profile": "pangaea_recorded_zeros_local_nc",
        "requested_draws": 32000,
        "complete_draws": 31999,
        "undefined_draws": 1,
        "unconditional": {"status": "refused_undefined_mass"},
        "parameters": [
            {
                "name": name,
                "native_taxon_id": taxon,
                "ppe": 1.0,
                "published_sd": 0.1 if i < 4 else 0.0,
            }
            for i, (name, taxon) in enumerate(zip(TAXA, TAXON_IDS, strict=True))
        ],
        "support_by_window": {
            str(b): {
                "status_counts": {"defined": 31999, "empty_native_window": 1}
                if b == 4
                else {"defined": 32000}
            }
            for b in WINDOWS
        },
        "conditional_on_complete": {
            "status": "conditional_on_complete",
            "mean": [0.2] * 20,
            "covariance_components": {
                k: (np.eye(20) * v).tolist()
                for k, v in [("age", 0.1), ("count", 0.2), ("shared_ppe", 1.0)]
            },
            "contrasts": [
                {
                    **{
                        k: v
                        for k, v in identity.items()
                        if k not in {"kind", "native_taxon_id"}
                    },
                    "mean_difference": 0.01,
                    "variance_components": {
                        "age": 0.2,
                        "count": 0.4,
                        "shared_ppe": 1.0,
                    },
                }
                for identity in quadratic_forms.scalar_axes()[20:]
            ],
        },
    }
    return source


def controlled_inputs(root: Path) -> dict[str, Any]:
    protocol = protocol_template()
    protocol.update(
        source_result="artifacts/source.json",
        source_ledger="artifacts/ledger.gz",
        source_verification="artifacts/verified.json",
        producer_source_commit="controlled-producer",
        observer_source_commit="controlled-observer",
    )
    source = source_result()
    ledger = controlled_ledger()
    source["draw_ledger"] = {
        "path": "ledger.gz",
        "rows": 32000,
        "bytes": len(ledger),
        "sha256": hashlib.sha256(ledger).hexdigest(),
    }
    source_body = json.dumps(source).encode()
    verified = {
        "status": "passed",
        "producer_source_commit": "controlled-producer",
        "observer_source_commit": "controlled-observer",
        "result_sha256": hashlib.sha256(source_body).hexdigest(),
        "count_profile": "pangaea_recorded_zeros_local_nc",
        "native_samples_checked": 107,
        "saved_joint_age_rows_checked": 32000,
        "complete_rows": 31999,
        "undefined_rows": 1,
        "original_count_slots_checked": 535,
        "native_reported_count_pairs_checked": 527,
        "source_zero_slots_checked": 8,
        "covariance_entries_checked": 2400,
        "contrasts_checked": 30,
        "model_fits": 0,
        "maximum_ledger_cover_gap": 0.0,
        "maximum_moment_gap": 0.0,
        "common_native_maximum_moment_gap": 0.0,
        "maximum_profile_difference_gap": 0.0,
    }
    bodies = {
        protocol["source_result"]: source_body,
        protocol["source_ledger"]: ledger,
        protocol["source_verification"]: json.dumps(verified).encode(),
    }
    protocol["repository_inputs"] = {
        name: {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
        for name, body in bodies.items()
    }
    for name, body in bodies.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    path = root / inputs.PROTOCOL
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(protocol))
    return protocol


@pytest.mark.parametrize(
    "corruption", ["none", "missing_qualification", "changed_body", "extra_pin"]
)
def test_three_qualified_inputs_are_checked_before_any_saved_cover_read(
    tmp_path: Path, corruption: str
) -> None:
    protocol = controlled_inputs(tmp_path)
    if corruption == "changed_body":
        (tmp_path / protocol["source_ledger"]).write_bytes(b"changed")
    elif corruption == "extra_pin":
        protocol["repository_inputs"]["artifacts/source.json.extra"] = {
            "bytes": 0,
            "sha256": "other",
        }
        (tmp_path / inputs.PROTOCOL).write_text(json.dumps(protocol))
    elif corruption == "missing_qualification":
        path = tmp_path / protocol["source_verification"]
        value = json.loads(path.read_text())
        value["source_zero_slots_checked"] = 7
        body = json.dumps(value).encode()
        path.write_bytes(body)
        protocol["repository_inputs"][protocol["source_verification"]] = {
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
        (tmp_path / inputs.PROTOCOL).write_text(json.dumps(protocol))
    if corruption != "none":
        with pytest.raises(ValueError):
            inputs.load(tmp_path)
    else:
        case = inputs.load(tmp_path)
        assert len(case["parameters"]) == 5 and case["ledger_body"]


@pytest.mark.parametrize("mode", ["complete", "duplicate", "truncated"])
def test_saved_cover_ledger_counts_every_identity_and_refusal(mode: str) -> None:
    body = controlled_ledger(duplicate=mode == "duplicate", short=mode == "truncated")
    if mode != "complete":
        with pytest.raises(ValueError):
            list(inputs.cover_rows(body, source_result()))
    else:
        rows = list(inputs.cover_rows(body, source_result()))
        assert (
            len(rows) == 32000
            and rows[-1] is None
            and sum(row is not None for row in rows) == 31999
        )


@pytest.mark.parametrize("corruption", ["none", "baseline", "source_revision"])
def test_publish_keeps_all_fifty_scalar_outcomes_and_source_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    controlled_inputs(tmp_path)
    forms = np.repeat(np.diag([1.0, 0.0, 0.0, 0.0])[None, :, :], 50, axis=0)
    if corruption == "baseline":
        forms[0, 0, 0] = 2
    monkeypatch.setattr(
        quadratic_forms, "accumulate", lambda *_: (copy.deepcopy(forms), 32000, 31999)
    )
    revisions = iter(
        ["before", "after"]
        if corruption == "source_revision"
        else ["controlled", "controlled"]
    )
    monkeypatch.setattr(producer, "source_revision", lambda _: next(revisions))
    output = tmp_path / "artifacts/scientific-output"
    if corruption != "none":
        with pytest.raises(ValueError):
            producer.publish(tmp_path, output)
        assert not (output / "result.json").exists()
    else:
        result = producer.publish(tmp_path, output)
        saved = json.loads((output / "result.json").read_text())
        assert saved == result and len(result["scalars"]) == 50
        assert result["summary"]["status_counts"] == {"tight_global_enclosure": 50}
        assert result["summary"]["optimizer_attempts"] == 800
        assert result["native_population"] == {
            "rows": 32000,
            "complete": 31999,
            "undefined": 1,
            "samples": 107,
        }
        assert (
            result["model_fits"] == 0
            and result["raw_count_or_age_inputs_read"] is False
        )
        assert result["fixed_parameter"]["output_uncertainty_retained"] is True
        assert [
            r["scalar_id"] for r in result["scalars"]
        ] == quadratic_forms.scalar_axes()
