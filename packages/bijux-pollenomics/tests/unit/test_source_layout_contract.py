from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.source_layout_contract import (
    build_source_layout_contract,
    validate_source_layout_contract,
)


class SourceLayoutContractUnitTests(unittest.TestCase):
    def test_validate_source_layout_contract_accepts_complete_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            contract = build_source_layout_contract(root)
            root.mkdir(parents=True, exist_ok=True)
            for source_dir in contract.source_directories:
                (root / source_dir).mkdir(parents=True, exist_ok=True)

            validate_source_layout_contract(contract)

    def test_validate_source_layout_contract_rejects_missing_source_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            contract = build_source_layout_contract(root)
            root.mkdir(parents=True, exist_ok=True)
            (root / "aadr").mkdir(parents=True, exist_ok=True)

            with self.assertRaisesRegex(ValueError, "source layout contract violation"):
                validate_source_layout_contract(contract)


if __name__ == "__main__":
    unittest.main()
