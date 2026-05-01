from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import runtime_surface_contract


class RuntimeSurfaceContractUnitTests(unittest.TestCase):
    def test_runtime_surface_contract_marks_canonical_runtime(self) -> None:
        contract = runtime_surface_contract()

        self.assertEqual(contract.package_name, "bijux-pollenomics")
        self.assertEqual(contract.runtime_module, "bijux_pollenomics")
        self.assertEqual(contract.engine_status, "atlas_builder_with_engine_roadmap")
        self.assertIn("collects, normalizes, and publishes", contract.description)


if __name__ == "__main__":
    unittest.main()
