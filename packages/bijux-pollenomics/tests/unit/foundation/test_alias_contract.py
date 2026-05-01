from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import compatibility_alias_contract


class CompatibilityAliasContractUnitTests(unittest.TestCase):
    def test_alias_contract_marks_alias_only_role(self) -> None:
        contract = compatibility_alias_contract()

        self.assertEqual(contract.alias_distribution, "pollenomics")
        self.assertEqual(contract.runtime_distribution, "bijux-pollenomics")
        self.assertEqual(contract.alias_module, "pollenomics")
        self.assertEqual(contract.runtime_module, "bijux_pollenomics")
        self.assertEqual(contract.role, "compatibility_alias_only")


if __name__ == "__main__":
    unittest.main()
