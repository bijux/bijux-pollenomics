"""Reader geometry rejects the short-screen clipping and obscured controls."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (None, True),
        ("offscreen-footer", False),
        ("clipped-status", False),
        ("obscured-zoom", False),
    ],
)
def test_reader_surface_geometry(mutation: str | None, expected: bool) -> None:
    owner = (
        Path(__file__).parents[3]
        / "src/bijux_pollenomics_dev/ci/atlas_browser/layout/reader-surface.mjs"
    )
    script = (
        f"import {{readerSurfaceReadable}} from {json.dumps(owner.as_uri())};\n"
        "const mutation = "
        + json.dumps(mutation)
        + ";\n"
        + """
const rect=(left,top,right,bottom)=>({left,top,right,bottom});
const facts={
  viewport:rect(0,0,320,568),document_width:320,document_height:568,
  toolbar:rect(8,8,312,164),map:rect(0,172,320,376),
  status:rect(8,384,312,495),footer:rect(0,503,320,568),
  reader:rect(8,180,312,368),reader_scrollable:true,
  targets:[
    {owner:'toolbar',rect:rect(16,16,106,60),touch:true},
    {owner:'status',rect:rect(18,432,106,488)},
    {owner:'footer',rect:rect(222,516,266,560),touch:true},
  ].map(target=>({...target,visible:true,center_hit:true})),
};
if(mutation==='offscreen-footer')facts.footer.bottom=651;
if(mutation==='clipped-status')facts.targets[1].rect.bottom=508;
if(mutation==='obscured-zoom')facts.targets[2].center_hit=false;
process.stdout.write(JSON.stringify(readerSurfaceReadable(facts)));
"""
    )
    result = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) is expected
