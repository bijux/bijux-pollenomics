"""Generated native frontier responses retain original detail field shapes."""

from copy import deepcopy
import json
from typing import Any

from .....resources.native_payloads import response


def native_response(products: dict[str, Any], url: str, **_: Any) -> Any:
    """Return source-shaped synthetic parents and publications without transport."""
    native_id = int(url.rsplit("/", 1)[-1])
    if "/taxa/" in url:
        payload = deepcopy(products["native"]["taxon-11"])
        payload["data"][0].update(
            taxonid=native_id,
            highertaxonid=native_id + 1,
            publicationid=19,
            publication=None,
        )
    else:
        assert "/publications/" in url
        payload = deepcopy(products["native"]["publication-13"])
        payload["data"][0]["publication"]["publicationid"] = native_id
    return response(url, json.dumps(payload).encode())
