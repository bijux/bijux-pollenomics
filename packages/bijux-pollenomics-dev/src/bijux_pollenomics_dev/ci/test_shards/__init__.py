"""Deterministic test partitions with complete-universe reconciliation."""

import hashlib


def shard_for(node_id: str, count: int) -> int:
    """Assign each exact test identity to one stable partition."""
    if count < 1:
        raise ValueError("shard count must be positive")
    return int.from_bytes(hashlib.sha256(node_id.encode()).digest()[:8], "big") % count
