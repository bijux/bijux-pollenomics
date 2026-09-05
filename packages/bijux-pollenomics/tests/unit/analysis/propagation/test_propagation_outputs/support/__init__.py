"""Intent-owned builders for propagation output contract tests."""

from .classification import (
    classification_bundle as _classification_bundle,
    rehash_classification_bundle as _rehash_classification_bundle,
)
from .events import event as _event
from .json_codec import (
    canonical_json_bytes as _canonical_json_bytes,
    read_json as _read_json,
)
from .materialization import materialize as _materialize
from .model import (
    MODEL as _MODEL,
    MODEL_BYTES as _MODEL_BYTES,
    PROPAGATION_CONTRACT_DIGEST as _PROPAGATION_CONTRACT_DIGEST,
    PROPAGATION_CONTRACT_VERSION as _PROPAGATION_CONTRACT_VERSION,
)
from .producer import (
    PROPAGATION_PRODUCER_DIGEST as _PROPAGATION_PRODUCER_DIGEST,
    PROPAGATION_PRODUCER_ID as _PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_VERSION as _PROPAGATION_PRODUCER_VERSION,
    REPOSITORY_ROOT as _REPOSITORY_ROOT,
    producer_digest as _producer_digest,
)

__all__ = [
    "_MODEL",
    "_MODEL_BYTES",
    "_PROPAGATION_CONTRACT_DIGEST",
    "_PROPAGATION_CONTRACT_VERSION",
    "_PROPAGATION_PRODUCER_DIGEST",
    "_PROPAGATION_PRODUCER_ID",
    "_PROPAGATION_PRODUCER_VERSION",
    "_REPOSITORY_ROOT",
    "_classification_bundle",
    "_canonical_json_bytes",
    "_event",
    "_materialize",
    "_producer_digest",
    "_read_json",
    "_rehash_classification_bundle",
]
