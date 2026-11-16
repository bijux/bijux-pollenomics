"""Descriptor-bound writes and closed ordinary file namespaces."""

from .anchors import DirectoryAnchor
from .namespaces import validate_regular_namespace
from .owned_writes import OwnedTreeWriter
from .regular_inputs import BoundedInputTree, read_regular_file
from .replacement import publish_owned_replacement

__all__ = [
    "OwnedTreeWriter",
    "DirectoryAnchor",
    "BoundedInputTree",
    "read_regular_file",
    "publish_owned_replacement",
    "validate_regular_namespace",
]
