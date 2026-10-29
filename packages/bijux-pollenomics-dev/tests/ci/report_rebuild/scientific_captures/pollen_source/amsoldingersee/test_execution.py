"""Keep failed production history separate from the successful saved observation."""

from __future__ import annotations

from copy import deepcopy
import importlib
from pathlib import Path
from typing import Any
import unittest


def refusal_checks(module: Any, jobs: dict[str, dict[str, Any]]) -> int:
    module.native_histories(jobs)
    cases = (
        ("production", "terminal.json", "actual_exit", 0),
        ("production", "amsoldingersee-terminal.json", "actual_exit", False),
        ("observation", "terminal.json", "actual_exit", True),
        ("observation", "independent-source-review.json", "producer_repeated", True),
        (
            "observation",
            "independent-source-review.json",
            "historical_E69_identity_admitted",
            True,
        ),
        (
            "observation",
            "independent-source-review.json",
            "tracked_byte_checker_exit",
            False,
        ),
    )
    for label, name, key, value in cases:
        changed = deepcopy(jobs)
        changed[label][name][key] = value
        try:
            module.native_histories(changed)
        except (ValueError, KeyError, TypeError):
            continue
        raise AssertionError("Native-history inflation accepted: " + key)
    changed = deepcopy(jobs)
    changed["observation"]["plan.json"]["stages"][0]["argv"][-2] = "--other-plan"
    try:
        module.native_histories(changed)
    except (ValueError, KeyError, TypeError):
        return len(cases) + 1
    raise AssertionError("Rebound source role accepted")


class NativeHistories(unittest.TestCase):
    def test_retained_failed_and_saved_histories_have_separate_authority(self) -> None:
        execution = importlib.import_module(
            "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.amsoldingersee.execution"
        )
        members = importlib.import_module(
            "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.amsoldingersee.members"
        )
        transport = importlib.import_module(
            "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source.amsoldingersee.transport"
        )

        root = next(
            parent
            for parent in Path(__file__).resolve().parents
            if (parent / "pyproject.toml").is_file()
            and (parent / "configs/pytest.ini").is_file()
        )
        capture_path = root / transport.CAPTURE
        capture = members.load(capture_path)
        jobs = {
            label: {
                name: members.load(capture_path.parent / member)
                for name, member in refs.items()
            }
            for label, refs in capture["jobs"].items()
        }
        self.assertEqual(refusal_checks(execution, jobs), 7)


if __name__ == "__main__":
    unittest.main()
