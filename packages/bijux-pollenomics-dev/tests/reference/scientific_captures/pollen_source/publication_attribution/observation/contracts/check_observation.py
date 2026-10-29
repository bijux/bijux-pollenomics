"""Exercise only controlled publication, input-custody and entrypoint guards."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any
import unittest

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = {
    "common_runner.py",
    "prepare.py",
    "run.py",
    "runtime_contracts.py",
    "check_contracts.py",
    "runtime_guarded_runner.py",
    "source_runtime.py",
    "observe.py",
    "execute_source.py",
    "contracts.py",
    "metadata.py",
    "observation_custody.py",
    "check_observation.py",
}
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
import contracts as c  # noqa: E402
import observation_custody as o  # noqa: E402


class ObservationControls(unittest.TestCase):
    def test_saved_completed_history_preserves_failed_observer(self) -> None:
        rows = [{"id": str(i), "actual_exit": code} for i, code in enumerate([0, 0, 1])]
        self.assertEqual(o.producer_progress(rows, rows), rows[:2])
        for bad in (
            rows[:2],
            [*rows, rows[0]],
            [{"id": "0", "actual_exit": False}, *rows[1:]],
        ):
            with self.assertRaises(ValueError):
                o.producer_progress(bad, rows)

    def test_actual_source_roles_without_native_execution(self) -> None:
        saved = c.load(c.SOURCE / "saved-execution-context.json")
        retention = Path(saved["source_retention"]["path"]).parent
        original = c.load(Path(saved["original_plan"]["path"]))
        for kind in ("publication", "doi"):
            raw = (retention / "source" / c.PRODUCERS[kind]).read_bytes()
            record = c.load(
                Path(original["output"]) / (kind + "-source-execution.json")
            )
            origins = record["first_party_origins"]
            o.source_role(kind, raw, origins, origins)
            with self.assertRaises(ValueError):
                o.source_role(
                    kind, raw + b"\nimport bijux_pollenomics\n", origins, origins
                )
            with self.assertRaises(ValueError):
                o.source_role(kind, raw, False, origins)
            forged = [
                {
                    "module": "foreign.module",
                    "path": "/foreign/module.py",
                    "sha256": "0" * 64,
                    "bytes": 1,
                }
            ]
            with self.assertRaises(ValueError):
                o.source_role(kind, raw, forged, origins)
            if kind == "publication":
                for bad in ([], origins[:-1], [*origins, origins[0]]):
                    with self.assertRaises(ValueError):
                        o.source_role(kind, raw, bad, origins)
            else:
                with self.assertRaises(ValueError):
                    o.source_role(kind, raw, forged, forged)

    def test_exact_nested_metadata_bridge_and_other_typed_values(self) -> None:
        old: dict[str, Any] = {
            "provider_policy": {"governed_review_sha256": "old", "rights": False},
            "records": [{"id": 1, "missing": None, "zero": 0}],
        }
        new = deepcopy(old)
        new["provider_policy"]["governed_review_sha256"] = "current"
        o.bridge(new, old, "provider_policy.governed_review_sha256", "old", "current")
        for label in (
            "rights",
            "number_type",
            "missing",
            "extra",
            "wrong_old",
            "wrong_new",
        ):
            a, b = deepcopy(new), deepcopy(old)
            if label == "rights":
                a["provider_policy"]["rights"] = True
            elif label == "number_type":
                a["records"][0]["zero"] = False
            elif label == "missing":
                a["records"][0].pop("missing")
            elif label == "extra":
                a["records"].append({"id": 2})
            elif label == "wrong_old":
                b["provider_policy"]["governed_review_sha256"] = "other"
            else:
                a["provider_policy"]["governed_review_sha256"] = "other"
            with self.assertRaises(ValueError):
                o.bridge(
                    a, b, "provider_policy.governed_review_sha256", "old", "current"
                )
        old_doi: dict[str, Any] = {
            "attribution_ledger_sha256": "old-ledger",
            "pairs": [None, False, 0, "literal"],
        }
        new_doi = {**old_doi, "attribution_ledger_sha256": "new-ledger"}
        o.bridge(
            new_doi, old_doi, "attribution_ledger_sha256", "old-ledger", "new-ledger"
        )
        bad = deepcopy(new_doi)
        bad["pairs"].reverse()
        with self.assertRaises(ValueError):
            o.bridge(
                bad, old_doi, "attribution_ledger_sha256", "old-ledger", "new-ledger"
            )
        with self.assertRaises(ValueError):
            invalid_hash: Any = False
            o.bridge(
                new_doi,
                old_doi,
                "attribution_ledger_sha256",
                invalid_hash,
                "new-ledger",
            )


if __name__ == "__main__":
    result = unittest.main(verbosity=2, exit=False)
    if not result.result.wasSuccessful():
        raise AssertionError("Controlled observation guards failed")
