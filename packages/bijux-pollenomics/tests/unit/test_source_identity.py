from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.source_identity import (
    SOURCE_IDENTITIES,
    resolve_source_identity,
)


class SourceIdentityUnitTests(unittest.TestCase):
    def test_source_identity_registry_covers_tracked_sources(self) -> None:
        self.assertEqual(
            tuple(SOURCE_IDENTITIES),
            ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead"),
        )
        self.assertEqual(SOURCE_IDENTITIES["raa"].display_name, "RAÄ")

    def test_resolve_source_identity_rejects_unknown_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported source identity"):
            resolve_source_identity("unknown")

    def test_resolve_source_identity_returns_stable_entry(self) -> None:
        identity = resolve_source_identity("landclim")

        self.assertEqual(identity.key, "landclim")
        self.assertEqual(identity.evidence_family, "pollen_paleoclimate_context")


if __name__ == "__main__":
    unittest.main()
