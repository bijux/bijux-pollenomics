from __future__ import annotations

from email.message import Message
from io import BytesIO
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from bijux_pollenomics.collection.sources.neotoma.collection import (
    fetch_neotoma_api_rows,
)


class NeotomaDataTests(unittest.TestCase):
    def test_fetch_neotoma_api_rows_retries_retryable_http_errors(self) -> None:
        retry_error = HTTPError(
            url="https://api.neotomadb.org/v2.0/data/datasets",
            code=503,
            msg="Service Unavailable",
            hdrs=Message(),
            fp=BytesIO(b"retry later"),
        )

        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=[
                retry_error,
                {"data": [{"site": {"siteid": 20, "datasets": [{"datasetid": 201}]}}]},
                {"data": []},
            ],
        ):
            rows = fetch_neotoma_api_rows("datasets")

        self.assertEqual(len(rows), 1)

    def test_fetch_neotoma_api_rows_retries_retryable_timeouts(self) -> None:
        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=[
                TimeoutError("read timed out"),
                {"data": [{"site": {"siteid": 20, "datasets": [{"datasetid": 201}]}}]},
                {"data": []},
            ],
        ):
            rows = fetch_neotoma_api_rows("datasets")

        self.assertEqual(len(rows), 1)
