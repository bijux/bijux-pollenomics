from __future__ import annotations

import unittest
from email.message import Message
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from bijux_pollenomics.collection.sources.neotoma.collection import (
    fetch_neotoma_dataset_download_rows,
)


class NeotomaDownloadTests(unittest.TestCase):
    def test_fetch_neotoma_dataset_download_rows_rejects_missing_dataset_payloads(
        self,
    ) -> None:
        with (
            patch(
                "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_download_row",
                side_effect=[
                    [{"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}],
                    [],
                ],
            ),
            self.assertRaisesRegex(ValueError, "missing dataset IDs: 202"),
        ):
            fetch_neotoma_dataset_download_rows([201, 202])

    def test_fetch_neotoma_dataset_download_rows_retries_retryable_http_errors(
        self,
    ) -> None:
        retry_error = HTTPError(
            url="https://api.neotomadb.org/v2.0/data/downloads/201",
            code=429,
            msg="Too Many Requests",
            hdrs=Message(),
            fp=BytesIO(b"slow down"),
        )

        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=[
                retry_error,
                {
                    "data": [
                        {"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}
                    ]
                },
            ],
        ):
            rows = fetch_neotoma_dataset_download_rows([201])

        self.assertEqual(len(rows), 1)

    def test_fetch_neotoma_dataset_download_rows_retries_retryable_timeouts(
        self,
    ) -> None:
        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=[
                TimeoutError("read timed out"),
                {
                    "data": [
                        {"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}
                    ]
                },
            ],
        ):
            rows = fetch_neotoma_dataset_download_rows([201])

        self.assertEqual(len(rows), 1)
