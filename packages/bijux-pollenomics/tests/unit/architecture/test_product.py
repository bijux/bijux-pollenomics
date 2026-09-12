from __future__ import annotations

import unittest

from bijux_pollenomics.architecture import ProductScope, build_product_scope


class ProductScopeUnitTests(unittest.TestCase):
    def test_product_scope_keeps_current_mode_and_non_claims_explicit(self) -> None:
        scope = build_product_scope()

        self.assertIsInstance(scope, ProductScope)
        self.assertEqual(scope.current_product_mode, "atlas_builder")
        self.assertEqual(scope.roadmap_mode, "future_engine")
        self.assertIn(
            "run exploratory REVEALS and LOVE with the optional LRA extension",
            scope.current_capabilities,
        )
        self.assertIn(
            "scientifically accepted LRA or independent vegetation prediction accuracy",
            scope.not_yet_supported_claims,
        )
        self.assertIn(
            "full pollenomics scientific decision engine",
            scope.not_yet_supported_claims,
        )


if __name__ == "__main__":
    unittest.main()
