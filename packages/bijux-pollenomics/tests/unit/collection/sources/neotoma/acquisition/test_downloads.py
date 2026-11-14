from __future__ import annotations

from email.message import Message
from io import BytesIO
import ssl
from typing import cast
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    fetch_neotoma_dataset_download_row,
    fetch_neotoma_dataset_download_rows,
    neotoma_download_dataset_id,
    validate_neotoma_download_coverage,
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


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "error", "data": []},
        {"success": 0, "data": []},
        {"status": "success"},
        {"status": "success", "data": None},
        {"status": "success", "data": {}},
        {"status": "success", "data": [None]},
    ],
)
def test_download_refuses_invalid_envelope(payload: dict[str, object]) -> None:
    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            return_value=payload,
        ),
        pytest.raises(ValueError, match="Neotoma"),
    ):
        fetch_neotoma_dataset_download_row(201)


@pytest.mark.parametrize("returned_ids", [[201, 201], [201, 999], [None]])
def test_download_coverage_refuses_extra_duplicate_or_unidentified_rows(
    returned_ids: list[int | None],
) -> None:
    rows = [
        {"site": {"collectionunit": {"dataset": {"datasetid": identity}}}}
        for identity in returned_ids
    ]
    with pytest.raises(ValueError, match="Neotoma"):
        validate_neotoma_download_coverage([201], rows)


def test_download_refuses_swapped_request_owners() -> None:
    def response(dataset_id: int) -> list[dict[str, object]]:
        return [
            {"site": {"collectionunit": {"dataset": {"datasetid": 403 - dataset_id}}}}
        ]

    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_download_row",
            side_effect=response,
        ),
        pytest.raises(ValueError, match="Neotoma"),
    ):
        fetch_neotoma_dataset_download_rows([201, 202])


def test_download_authenticates_https_server() -> None:
    def response(*_: object, context: ssl.SSLContext | None, **__: object) -> BytesIO:
        assert context is None or (
            context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        )
        return BytesIO(
            b'{"status":"success","data":[{"site":{"collectionunit":{"dataset":{"datasetid":201}}}}]}'
        )

    with patch("bijux_pollenomics.core.http.urlopen", side_effect=response):
        assert fetch_neotoma_dataset_download_rows([201]) == [
            {"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}
        ]


@pytest.mark.parametrize("identity", [True, False, 0, -1, "0", "-1"])
def test_download_native_identity_requires_positive_nonboolean_identifier(
    identity: object,
) -> None:
    row = {"site": {"collectionunit": {"dataset": {"datasetid": identity}}}}
    assert neotoma_download_dataset_id(row) is None


@pytest.mark.parametrize("mirror_id", [999, None, True])
def test_download_refuses_contradictory_or_invalid_mirrored_dataset_identity(
    mirror_id: object,
) -> None:
    row = {
        "site": {
            "dataset": {"datasetid": mirror_id},
            "collectionunit": {"dataset": {"datasetid": 201}},
        }
    }
    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            return_value={"status": "success", "data": [row]},
        ),
        pytest.raises(ValueError, match="Neotoma"),
    ):
        fetch_neotoma_dataset_download_row(201)


@pytest.mark.parametrize("identity", [201, "201", " 201 "])
@pytest.mark.parametrize("shape", ["unit", "site", "mirrored"])
def test_download_preserves_agreeing_native_identity_shapes(
    identity: int | str, shape: str
) -> None:
    site: dict[str, object] = {}
    if shape in {"site", "mirrored"}:
        site["dataset"] = {"datasetid": identity}
    if shape in {"unit", "mirrored"}:
        site["collectionunit"] = {"dataset": {"datasetid": identity}}
    row = {"site": site}
    with patch(
        "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
        return_value={"status": "success", "data": [row]},
    ):
        assert fetch_neotoma_dataset_download_row(201) == [row]


@pytest.mark.parametrize("identity", [True, False, 0, -1, 201.9, "201", None])
@pytest.mark.parametrize("entrypoint", ["single", "batch", "coverage"])
def test_requested_dataset_identity_is_refused_before_any_download(
    identity: object, entrypoint: str
) -> None:
    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json"
        ) as network,
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_download_row"
        ) as batch_fetch,
    ):
        with pytest.raises(ValueError, match="Neotoma.*positive integer"):
            if entrypoint == "single":
                fetch_neotoma_dataset_download_row(cast(int, identity))
            elif entrypoint == "batch":
                fetch_neotoma_dataset_download_rows([201, cast(int, identity)])
            else:
                validate_neotoma_download_coverage([cast(int, identity)], [])
        network.assert_not_called()
        batch_fetch.assert_not_called()
