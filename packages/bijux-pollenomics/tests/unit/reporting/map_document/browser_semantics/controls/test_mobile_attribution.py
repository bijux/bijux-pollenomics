from __future__ import annotations

from ..support import run_node_json, template_block


def test_attribution_uses_the_reader_footer_independent_of_map_overlays() -> None:
    footer = template_block('<footer class="map-reader-footer"', "</footer>")
    assert 'id="map-provider-credit"' in footer
    assert 'id="map-distance-scale"' in footer
    assert 'id="map-zoom-controls"' in footer
    observed = run_node_json(
        """
const attribution={id:'native-attribution'};
const parents={};
const document={getElementById(id){return {appendChild(node){parents[node.id]=id}}}};
const map={attributionControl:{getContainer(){return attribution}}};
"""
        + template_block(
            "document.getElementById('map-provider-credit').appendChild",
            "if (window.ResizeObserver)",
        )
        + "console.log(JSON.stringify(parents));"
    )
    assert observed == {"native-attribution": "map-provider-credit"}
