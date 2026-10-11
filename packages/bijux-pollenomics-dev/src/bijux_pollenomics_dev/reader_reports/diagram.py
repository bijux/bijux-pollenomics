"""Translate the reports' declared Mermaid flowchart subset into safe DOT."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import textwrap

NODE = re.compile(r'([A-Za-z][A-Za-z0-9_]*)(?:\["([^"\n]+)"\])?\Z')
EDGE = re.compile(r'(.+?)\s*(-->|-\.\s*"([^"\n]+)"\s*\.->)\s*(.+)\Z')


class DiagramError(ValueError):
    """A Mermaid diagram uses syntax outside the reviewed flowchart subset."""


@dataclass(frozen=True)
class EdgeSpec:
    """Represent one reviewed Mermaid edge and its optional label."""

    source: str
    target: str
    label: str | None


def _node(value: str) -> tuple[str, str | None]:
    match = NODE.fullmatch(value.strip())
    if not match:
        raise DiagramError(f"unsupported Mermaid node: {value!r}")
    return match.group(1), match.group(2)


def mermaid_to_dot(source: str) -> str:
    """Translate only the supported Mermaid flowchart grammar into escaped DOT."""
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    if not lines or lines[0] not in {"flowchart LR", "flowchart TB"}:
        raise DiagramError("only flowchart LR and flowchart TB are supported")
    if len(lines) < 2:
        raise DiagramError("flowchart has no edges")
    nodes: dict[str, str] = {}
    declared_labels: dict[str, str] = {}
    edges: list[EdgeSpec] = []
    for line in lines[1:]:
        match = EDGE.fullmatch(line)
        if not match:
            raise DiagramError(f"unsupported Mermaid edge: {line!r}")
        source_id, source_label = _node(match.group(1))
        target_id, target_label = _node(match.group(4))
        for identifier, label in ((source_id, source_label), (target_id, target_label)):
            if (
                identifier in declared_labels
                and label is not None
                and declared_labels[identifier] != label
            ):
                raise DiagramError(f"conflicting label for Mermaid node {identifier}")
            nodes.setdefault(identifier, label or identifier)
            if label is not None:
                declared_labels[identifier] = label
                nodes[identifier] = label
        edges.append(EdgeSpec(source_id, target_id, match.group(3)))
    result = [
        "digraph report {",
        "  graph [rankdir=TB, bgcolor=white, margin=0.08, nodesep=0.22, ranksep=0.28];",
        '  node [shape=box, style="rounded,filled", fillcolor="#F1F5F9", color="#64748B",',
        '        fontname="Arial", fontsize=12, margin="0.14,0.10"];',
        '  edge [color="#475569", fontname="Arial", fontsize=8, arrowsize=0.7];',
    ]
    for identifier, label in nodes.items():
        wrapped = "\n".join(textwrap.wrap(label, width=31, break_long_words=False))
        result.append(
            f"  {identifier} [label={json.dumps(wrapped, ensure_ascii=False)}];"
        )
    for edge in edges:
        options = ""
        if edge.label is not None:
            options = (
                " [style=dashed, label="
                + json.dumps(edge.label, ensure_ascii=False)
                + "]"
            )
        result.append(f"  {edge.source} -> {edge.target}{options};")
    result.append("}")
    return "\n".join(result) + "\n"
