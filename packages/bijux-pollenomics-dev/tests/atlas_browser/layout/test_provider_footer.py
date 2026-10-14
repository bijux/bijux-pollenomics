"""Footer geometry must reject hidden, overlapping and escaped scale controls."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

import pytest


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("desktop-footer", True),
        ("mobile-footer", True),
        ("status-overlap", False),
        ("outside-footer", False),
        ("footer-overlaps-map", False),
        ("offscreen-footer", False),
        ("obscured-center", False),
        ("hidden-scale", False),
        ("missing-footer-parent", False),
        ("zero-area-scale", False),
        ("nonfinite-geometry", False),
        ("horizontal-scroll", False),
        ("vertical-scroll", False),
    ],
)
def test_scale_footer_contract(scenario: str, expected: bool) -> None:
    source = (
        Path(__file__).parents[3]
        / "src/bijux_pollenomics_dev/ci/atlas_browser/provider-accessibility.mjs"
    ).read_text()
    match = re.search(
        r"function scaleLayoutReadable\(facts\).*?\n}\n\nasync function",
        source,
        re.DOTALL,
    )
    assert match is not None
    script = (
        match.group(0).removesuffix("\n\nasync function")
        + "\nconst scenario = "
        + json.dumps(scenario)
        + ";\n"
        + r"""
const width=scenario==='desktop-footer'?1440:390;
const facts={
  rect:{left:8,top:866,right:75,bottom:890},
  footer:{left:0,top:796,right:width,bottom:900},
  map:{left:0,top:0,right:width,bottom:796},
  status:{left:8,top:700,right:width-8,bottom:780},
  viewport:{left:0,top:0,right:width,bottom:900},
  document_width:width,document_height:900,
  footer_contains_scale:true,scale_visible:true,center_hit:true,
};
if(scenario==='status-overlap')facts.rect={left:8,top:720,right:75,bottom:744};
if(scenario==='outside-footer')facts.rect.left=-1;
if(scenario==='footer-overlaps-map')facts.footer.top=790;
if(scenario==='offscreen-footer')facts.footer.bottom=901;
if(scenario==='obscured-center')facts.center_hit=false;
if(scenario==='hidden-scale')facts.scale_visible=false;
if(scenario==='missing-footer-parent')facts.footer_contains_scale=false;
if(scenario==='zero-area-scale')facts.rect.right=facts.rect.left;
if(scenario==='nonfinite-geometry')facts.rect.top=NaN;
if(scenario==='horizontal-scroll')facts.document_width=width+1;
if(scenario==='vertical-scroll')facts.document_height=901;
process.stdout.write(JSON.stringify({readable:scaleLayoutReadable(facts)}));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["readable"] is expected
