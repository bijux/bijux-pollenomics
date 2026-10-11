"""Load MkDocs YAML while tolerating its application-specific tags."""

from collections.abc import Callable
from typing import cast

import yaml


class MkDocsLoader(yaml.SafeLoader):
    """SafeLoader that tolerates MkDocs-specific tags in config files."""


def _construct_unknown(
    loader: MkDocsLoader, tag_suffix: str, node: yaml.Node
) -> object:
    del tag_suffix
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


register_constructor = cast(
    Callable[[str, Callable[[MkDocsLoader, str, yaml.Node], object]], None],
    MkDocsLoader.add_multi_constructor,
)
register_constructor("", _construct_unknown)

__all__ = ["MkDocsLoader"]
