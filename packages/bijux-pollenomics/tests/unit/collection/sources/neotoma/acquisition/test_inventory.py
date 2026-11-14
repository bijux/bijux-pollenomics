from __future__ import annotations

from io import BytesIO
from pathlib import Path
import ssl
from typing import cast
import unittest
from unittest.mock import patch
from urllib.error import URLError

import pytest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    collect_neotoma_data,
    fetch_neotoma_api_rows,
    fetch_neotoma_dataset_inventory_rows,
)


class NeotomaInventoryTests(unittest.TestCase):
    def test_fetch_neotoma_dataset_inventory_rows_reads_dataset_inventory_rows(
        self,
    ) -> None:
        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            return_value={
                "data": [
                    {
                        "site": {
                            "siteid": 20,
                            "sitename": "Agerods Mosse",
                            "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                            "datasets": [
                                {"datasetid": 201, "datasettype": "pollen"},
                                {"datasetid": 202, "datasettype": "pollen"},
                            ],
                        }
                    }
                ]
            },
        ):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))
        site = cast(dict[str, object], rows[0]["site"])
        datasets = cast(list[dict[str, object]], site["datasets"])

        self.assertEqual(len(rows), 1)
        self.assertEqual(site["siteid"], 20)
        self.assertEqual(
            [dataset["datasetid"] for dataset in datasets],
            [201, 202],
        )

    def test_fetch_neotoma_dataset_inventory_rows_uses_wide_bbox_inventory_limit(
        self,
    ) -> None:
        observed_params: list[dict[str, str]] = []

        def fake_fetch_json(
            url: str, params: dict[str, str] | None = None, **_: object
        ) -> object:
            self.assertEqual(url, "https://api.neotomadb.org/v2.0/data/datasets")
            self.assertIsNotNone(params)
            observed_params.append(dict(params or {}))
            return {
                "data": [
                    {
                        "site": {
                            "siteid": 20,
                            "sitename": "Agerods Mosse",
                            "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                            "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                        }
                    }
                ]
            }

        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(observed_params), 1)
        self.assertEqual(observed_params[0]["limit"], "400")
        self.assertEqual(observed_params[0]["offset"], "0")
        self.assertEqual(observed_params[0]["datasettype"], "pollen")


@pytest.mark.parametrize("after_full_page", [False, True])
@pytest.mark.parametrize(
    "payload",
    [
        {"status": "error", "message": "database unavailable", "data": []},
        {"success": False, "data": []},
        {"status": "success"},
        {"status": "success", "data": None},
        {"status": "success", "data": {"error": "invalid query"}},
        {"status": "success", "data": [None]},
    ],
)
def test_inventory_refuses_invalid_page_before_publishing(
    tmp_path: Path, payload: dict[str, object], *, after_full_page: bool
) -> None:
    pages: list[object] = []
    if after_full_page:
        pages.append({"status": "success", "data": [{"site": {}}, {"site": {}}]})
    pages.append(payload)
    output = tmp_path / "neotoma"
    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.NEOTOMA_INVENTORY_QUERY_LIMIT",
            2,
        ),
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=pages,
        ),
        pytest.raises(ValueError, match="Neotoma"),
    ):
        collect_neotoma_data(
            output,
            country_boundaries={},
            bbox=(4.0, 54.0, 35.0, 72.0),
        )
    assert not list(output.rglob("*.json"))


def test_inventory_preserves_full_pages_until_successful_empty_page() -> None:
    with (
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.NEOTOMA_INVENTORY_QUERY_LIMIT",
            2,
        ),
        patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=[
                {
                    "status": "success",
                    "data": [{"site": {"siteid": 1}}, {"site": {"siteid": 2}}],
                },
                {"status": "success", "data": []},
            ],
        ),
    ):
        assert fetch_neotoma_api_rows("datasets") == [
            {"site": {"siteid": 1}},
            {"site": {"siteid": 2}},
        ]


def test_inventory_authenticates_https_server() -> None:
    def response(*_: object, context: ssl.SSLContext | None, **__: object) -> BytesIO:
        assert context is None or (
            context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
        )
        return BytesIO(b'{"status":"success","data":[]}')

    with patch("bijux_pollenomics.core.http.urlopen", side_effect=response):
        assert fetch_neotoma_api_rows("datasets") == []


@pytest.mark.parametrize("allow_fallback", [False, True])
def test_inventory_requires_explicit_opt_in_for_unverified_tls_fallback(
    monkeypatch: pytest.MonkeyPatch, *, allow_fallback: bool
) -> None:
    monkeypatch.setenv(
        "BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS", "1" if allow_fallback else "0"
    )

    def response(*_: object, context: ssl.SSLContext | None, **__: object) -> BytesIO:
        if context is None or context.verify_mode == ssl.CERT_REQUIRED:
            raise URLError(ssl.SSLCertVerificationError("untrusted certificate"))
        assert allow_fallback
        return BytesIO(b'{"status":"success","data":[]}')

    with (
        patch("bijux_pollenomics.core.http.urlopen", side_effect=response),
        patch("time.sleep"),
    ):
        if allow_fallback:
            assert fetch_neotoma_api_rows("datasets") == []
        else:
            with pytest.raises(URLError):
                fetch_neotoma_api_rows("datasets")
