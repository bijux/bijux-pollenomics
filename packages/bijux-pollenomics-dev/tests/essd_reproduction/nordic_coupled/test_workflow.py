"""Controlled coupled workflow and file custody; no real fits or scores."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
import unittest
from unittest.mock import patch

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import workflow as MODULE


class Refusal(Exception):
    reason_code = "artificial_refusal"


class TestWorkflow(unittest.TestCase):
    root: Path
    calls: list[tuple[str, dict[str, Any]]]
    rows: list[dict[str, Any]]
    payload: dict[str, Any]
    methods: tuple[str, ...]
    api: dict[str, Any]

    @pytest.fixture(autouse=True)
    def owned_output(self, tmp_path: Path) -> None:
        self.root = tmp_path

    def setUp(self) -> None:
        self.calls = []
        self.rows = [
            {"directory": n, "experiment": {"sha256": "1" * 64}} for n in MODULE.NAMES
        ]
        self.payload = {
            "sites": [
                {"record_id": str(i), "raw": {"path": str(i), "sha256": "2" * 64}}
                for i in range(3)
            ]
        }
        self.methods = MODULE.METHODS
        self.api = {
            "spec": lambda x: x,
            "prepare": self.prepare,
            "reopen": self.reopen,
            "score": self.score,
            "product": lambda p, **k: (
                None,
                {
                    "phase": "scores",
                    "scientific_payload": {
                        "prediction_manifest_sha256": "3" * 64,
                        "scores": [{"score": {"status": "prediction_failed"}}] * 9,
                    },
                },
            ),
            "refusals": (Refusal,),
        }

    def prepare(self, spec: object, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(("prepare", kwargs))
        return SimpleNamespace(
            directory=kwargs["destination"], manifest_sha256="3" * 64
        )

    def reopen(self, directory: Path, **kwargs: Any) -> tuple[Any, ...]:
        self.calls.append(("reopen", kwargs))
        product = SimpleNamespace(
            directory=directory,
            manifest_sha256=kwargs["expected_manifest_sha256"],
            scientific_content_sha256="4" * 64,
        )
        failures = [
            {
                "fold_id": "fold2",
                "status": "refused",
                "reason_code": "negative_cover",
                "detail": "Artificial negative remains",
            }
        ]
        predictions: dict[tuple[str, str], dict[str, Any]] = {
            (fold, m): {} for fold in ("fold0", "fold1") for m in self.methods
        }
        return (
            product,
            {
                "files": dict.fromkeys(
                    (
                        "training.json",
                        "preparations.json",
                        "operations.json",
                        "failures.json",
                        "predictions.json",
                    ),
                    "7" * 64,
                ),
                "scientific_payload": {"failures": failures},
            },
            {f"fold{i}": {} for i in range(3)},
            predictions,
            self.methods,
        )

    def score(self, predictions: Path, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(("score", kwargs))
        return SimpleNamespace(
            directory=kwargs["destination"],
            manifest_sha256="5" * 64,
            scientific_content_sha256="6" * 64,
        )

    def execute(
        self, phase: str = "prepare", prior: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        def fake_read(path: Path, checksum: str, maximum: int) -> tuple[bytes, Any]:
            return b"", prior if path.name == "batch.json" else self.payload

        with (
            patch.object(MODULE, "apis", return_value=self.api),
            patch.object(MODULE, "input_scope", return_value=(self.rows, [])),
            patch.object(MODULE, "read", side_effect=fake_read),
        ):
            return MODULE.batch(
                self.root / "inputs",
                self.root / "manifest",
                "a" * 64,
                self.root / phase,
                phase=phase,
                execution_epoch="0" * 40,
                prediction_index=self.root / "prepare/batch.json" if prior else None,
                prediction_index_sha256="b" * 64 if prior else None,
            )

    def test_actual80member_input_boundary_and_missing_file(self) -> None:
        root = self.root / "inputs"
        root.mkdir()
        members = ["source-pins.json"]
        rows = []
        for name in MODULE.NAMES:
            (root / name).mkdir()
            for member in (
                "chronology",
                "taxa",
                "parameters",
                "dependency_lock",
                "decision",
                "BOKE-raw",
                "BUS-raw",
                "SOLSOE83-raw",
                "BOKE-geometry",
                "BUS-geometry",
                "SOLSOE83-geometry",
                "experiment",
                "projection",
            ):
                relative = name + "/" + member + ".json"
                members.append(relative)
                (root / relative).write_text("{}")
            checksum = hashlib.sha256(b"{}").hexdigest()
            rows.append(
                {
                    "directory": name,
                    "experiment": {"path": "experiment.json", "sha256": checksum},
                }
            )
        (root / "source-pins.json").write_text("[]")
        (root / "inputs.json").write_text(json.dumps({"experiments": rows}))
        members.append("inputs.json")
        pins = [
            {
                "path": n,
                "sha256": hashlib.sha256((root / n).read_bytes()).hexdigest(),
                "bytes": (root / n).stat().st_size,
            }
            for n in members
        ]
        manifest = self.root / "input-manifest.json"
        manifest.write_text(json.dumps(pins))
        checksum = hashlib.sha256(manifest.read_bytes()).hexdigest()
        self.assertEqual(MODULE.input_scope(root, manifest, checksum)[0], rows)
        (root / members[1]).unlink()
        with self.assertRaises(FileNotFoundError):
            MODULE.input_scope(root, manifest, checksum)

    def test_complete_predictions_preserve_method_refusals(self) -> None:
        result = self.execute()
        self.assertEqual(result["bin_status_counts"], {"completed": 6})
        self.assertEqual(len([x for x in self.calls if x[0] == "prepare"]), 6)
        self.assertTrue(
            all(x[1]["workers"] == 1 for x in self.calls if x[0] == "prepare")
        )
        self.assertEqual(
            result["bins"][0]["prediction"]["status_counts"],
            {"predicted": 6, "refused": 3},
        )
        self.assertFalse(any(x[0] == "score" for x in self.calls))

    def test_scoring_reopens_before_every_call(self) -> None:
        prepared = self.execute()
        self.calls.clear()
        result = self.execute("score", prepared)
        self.assertEqual(result["bin_status_counts"], {"completed": 6})
        self.assertEqual([x[0] for x in self.calls[:6]], ["reopen"] * 6)
        for i, (kind, kwargs) in enumerate(self.calls):
            if kind == "score":
                self.assertEqual(self.calls[i - 1][0], "reopen")
                self.assertEqual(
                    kwargs["outcome_inventory"]["records"],
                    {s["record_id"]: s["raw"] for s in self.payload["sites"]},
                )
        self.assertEqual(
            result["bins"][0]["scoring"]["status_counts"], {"prediction_failed": 9}
        )

    def test_unknown_failure_remains_fatal_and_unrun(self) -> None:
        self.api["prepare"] = lambda *a, **k: (_ for _ in ()).throw(
            RuntimeError("unknown")
        )
        with self.assertRaisesRegex(RuntimeError, "unknown"):
            self.execute()
        result = json.loads((self.root / "prepare/batch.json").read_text())
        self.assertEqual(
            [r["status"] for r in result["bins"]], ["fatal"] + ["not_run"] * 5
        )

    def test_known_batch_refusal_does_not_erase_other_bins(self) -> None:
        self.api["prepare"] = lambda *a, **k: (_ for _ in ()).throw(Refusal("known"))
        result = self.execute()
        self.assertEqual(result["bin_status_counts"], {"refused": 6})
        self.assertTrue(
            all(r["reason_code"] == "artificial_refusal" for r in result["bins"])
        )

    def test_wrong_frozen_source_stops_before_score(self) -> None:
        prior = self.execute()
        prior["input_manifest_sha256"] = "wrong"
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, "identity differs"):
            self.execute("score", prior)
        self.assertEqual(self.calls, [])

    def test_reader_population_mismatch_refuses(self) -> None:
        self.methods = ("training_mean",)
        with self.assertRaisesRegex(ValueError, "population differs"):
            MODULE.prediction_receipt(self.root, "1" * 64, self.api)

    def test_same_buffer_hash_and_nonfinite_refused(self) -> None:
        import hashlib

        path = self.root / "member.json"
        path.write_text('{"x":NaN}')
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            MODULE.read(path, hashlib.sha256(path.read_bytes()).hexdigest(), 100)
        with self.assertRaisesRegex(ValueError, "identity differs"):
            MODULE.read(path, "f" * 64, 100)


class TestStableIdentity(unittest.TestCase):
    root: Path
    path: Path
    body: bytes
    checksum: str

    @pytest.fixture(autouse=True)
    def owned_output(self, tmp_path: Path) -> None:
        self.root = tmp_path

    def setUp(self) -> None:
        self.path = self.root / "member.json"
        self.body = b'{"owned": true, "count": 2}\n'
        self.path.write_bytes(self.body)
        self.checksum = hashlib.sha256(self.body).hexdigest()

    def test_fresh_json_buffer_and_object(self) -> None:
        raw, value = MODULE.read(self.path, self.checksum, 1024)
        self.assertEqual(raw, self.body)
        self.assertEqual(value, {"owned": True, "count": 2})

    def test_digest_and_changed_content_refuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "identity"):
            MODULE.read(self.path, "0" * 64, 1024)
        self.path.write_bytes(b'{"owned": false, "count": 2}\n')
        with self.assertRaisesRegex(ValueError, "identity"):
            MODULE.read(self.path, self.checksum, 1024)

    def test_atime_alone_can_change_while_stable_identity_passes(self) -> None:
        original = Path.stat
        visits: list[int] = []

        def accessed(path: Path, *, follow_symlinks: bool = True) -> os.stat_result:
            info = original(path, follow_symlinks=follow_symlinks)
            if path != self.path or not follow_symlinks:
                return info
            fields = {
                key: getattr(info, key)
                for key in (
                    "st_dev",
                    "st_ino",
                    "st_mode",
                    "st_nlink",
                    "st_size",
                    "st_mtime_ns",
                    "st_ctime_ns",
                )
            }
            visits.append(info.st_atime_ns + len(visits) + 1)
            # Only the unused access-time field changes between the real read stats.
            return cast(
                os.stat_result, SimpleNamespace(**fields, st_atime_ns=visits[-1])
            )

        with patch.object(Path, "stat", accessed):
            self.assertEqual(MODULE.read(self.path, self.checksum, 1024)[0], self.body)
        self.assertEqual(len(visits), 2)
        self.assertNotEqual(visits[0], visits[1])
