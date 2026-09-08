"""Build and validate complete SEAD source-key accountability."""

from .contract import (
    SOURCE_KEY_LEDGER_SCHEMA_VERSION,
    sead_source_key_table_plans,
    source_key_table_contract_rows,
    source_key_table_contract_sha256,
)
from .derivation import build_sead_source_key_ledger
from .ranges import (
    decode_positive_integer_ranges,
    encode_positive_integer_ranges,
)
from .validation import (
    validate_sead_source_key_ledger,
    validate_sead_source_key_ledger_against_acquisition,
)

__all__ = [
    "SOURCE_KEY_LEDGER_SCHEMA_VERSION",
    "build_sead_source_key_ledger",
    "decode_positive_integer_ranges",
    "encode_positive_integer_ranges",
    "sead_source_key_table_plans",
    "source_key_table_contract_rows",
    "source_key_table_contract_sha256",
    "validate_sead_source_key_ledger",
    "validate_sead_source_key_ledger_against_acquisition",
]
