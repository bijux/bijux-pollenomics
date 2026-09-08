"""Network-boundary behavior exercised by source registry workflows."""

from __future__ import annotations

import unittest

from bijux_pollenomics.adna.sources import library as source_library_module


class SourceRegistryAcquisitionTests(unittest.TestCase):
    def test_download_url_rejects_non_http_scheme(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported URL for network fetch"):
            source_library_module._download_url("file:///tmp/source.pdf")
