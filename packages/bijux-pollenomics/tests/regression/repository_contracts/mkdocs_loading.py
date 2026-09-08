"""Load MkDocs YAML while tolerating its application-specific tags."""

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


MkDocsLoader.add_multi_constructor("", _construct_unknown)

__all__ = ["MkDocsLoader"]
