from __future__ import annotations

import unittest
from pathlib import Path

from bijux_pollenomics_dev.api.freeze_contracts import run as run_api_freeze_contracts


class ApiFreezeContractsTests(unittest.TestCase):
    def test_api_freeze_contracts_pass_for_repository(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.assertEqual(run_api_freeze_contracts(repo_root), 0)


if __name__ == "__main__":
    unittest.main()
