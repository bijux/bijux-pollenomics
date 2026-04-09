from __future__ import annotations

from pathlib import Path
import unittest

from bijux_pollenomics_dev.api.openapi_drift import run as run_openapi_drift


class OpenapiDriftTests(unittest.TestCase):
    def test_openapi_drift_passes_for_repository(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.assertEqual(run_openapi_drift(repo_root), 0)


if __name__ == "__main__":
    unittest.main()
