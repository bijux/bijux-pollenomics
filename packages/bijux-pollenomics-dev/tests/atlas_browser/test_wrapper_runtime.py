"""Exercise wrapper authority and the actual maintained selection loader offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci import atlas_browser

MODULE = Path(atlas_browser.__file__).with_name("wrapper-runtime.mjs")
REPOSITORY = Path(__file__).resolve().parents[4]


def _node(script: str) -> Any:
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            f"import * as wrapper from {json.dumps(MODULE.as_uri())};\n" + script,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return json.loads(result.stdout)


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@pytest.fixture
def authority(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    repository, site = tmp_path / "repository", tmp_path / "site"
    source = b"# Nordic Evidence Atlas\n"
    parent = b'<iframe src="../../report/regions/nordic/nordic_map.html"></iframe>'
    child = b'<script id="atlas-static-bootstrap">{"build_id":"build","version":"source"}</script>'
    paths = {
        repository / "docs/public/nordic-atlas/index.md": source,
        repository / "docs/report/regions/nordic/nordic_map.html": child,
        site / "public/nordic-atlas/index.html": parent,
        site / "report/regions/nordic/nordic_map.html": child,
        site / "report/regions/nordic/chunk.js": b"original raw chunk",
    }
    for path, body in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    owner: dict[str, Any] = {
        "parents": [
            {
                "output": "public/nordic-atlas/index.html",
                "source": {
                    "path": "docs/public/nordic-atlas/index.md",
                    "sha256": _sha(source),
                },
                "reports": ["report/regions/nordic/nordic_map.html"],
                "built_html_sha256": _sha(parent),
            }
        ],
        "reports": [
            {
                "output": "report/regions/nordic/nordic_map.html",
                "source": {
                    "path": "docs/report/regions/nordic/nordic_map.html",
                    "sha256": _sha(child),
                },
                "resources": {
                    "report/regions/nordic/chunk.js": {
                        "source": "docs/report/regions/nordic/chunk.js",
                        "sha256": _sha(b"original raw chunk"),
                    }
                },
            }
        ],
    }
    (repository / "configs/docs/maps").mkdir(parents=True)
    (repository / "configs/docs/maps/report-owner.json").write_text(json.dumps(owner))
    return repository, site, owner


def _read_authority(repository: Path, site: Path) -> Any:
    return _node(f"""
      try {{const result=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
        console.log(JSON.stringify({{build:result.buildId,version:result.version,expected:[...result.expected.keys()]}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)


def test_real_parent_child_and_owned_resources_are_bound(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, _ = authority
    result = _read_authority(repository, site)
    assert result == {
        "build": "build",
        "version": "source",
        "expected": [
            "public/nordic-atlas/index.html",
            "report/regions/nordic/nordic_map.html",
            "report/regions/nordic/chunk.js",
        ],
    }


@pytest.mark.parametrize(
    "target,reason",
    [
        ("parent", "built wrapper differs"),
        ("child", "built child differs"),
        ("source", "wrapper source differs"),
        ("canonical", "built child differs"),
    ],
)
def test_stale_built_or_canonical_bytes_refuse(
    authority: tuple[Path, Path, dict[str, Any]], target: str, reason: str
) -> None:
    repository, site, _ = authority
    path = {
        "parent": site / "public/nordic-atlas/index.html",
        "child": site / "report/regions/nordic/nordic_map.html",
        "source": repository / "docs/public/nordic-atlas/index.md",
        "canonical": repository / "docs/report/regions/nordic/nordic_map.html",
    }[target]
    path.write_bytes(path.read_bytes() + b"changed")
    assert reason in _read_authority(repository, site)["error"]


def test_approved_parent_cannot_point_at_a_synthetic_child(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, owner = authority
    path = site / "public/nordic-atlas/index.html"
    path.write_bytes(b'<iframe src="../../fake.html"></iframe>')
    owner["parents"][0]["built_html_sha256"] = _sha(path.read_bytes())
    (repository / "configs/docs/maps/report-owner.json").write_text(json.dumps(owner))
    assert (
        "real wrapper iframe target differs"
        in _read_authority(repository, site)["error"]
    )


@pytest.mark.parametrize("tamper", [False, True])
def test_meaningful_resource_integrity_remains_enforced(
    authority: tuple[Path, Path, dict[str, Any]], tamper: bool
) -> None:
    repository, site, _ = authority
    if tamper:
        (site / "report/regions/nordic/chunk.js").write_bytes(b"foreign chunk")
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      try{{const result=await wrapper.readSiteMember({json.dumps(str(site))},'/report/regions/nordic/chunk.js',authority.expected);console.log(JSON.stringify({{bytes:result.bytes.toString()}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    if tamper:
        assert "owned site member differs" in result["error"]
    else:
        assert result == {"bytes": "original raw chunk"}


def test_site_path_and_symlink_escape_refuse(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (tmp_path / "outside").write_bytes(b"private")
    (site / "escape").symlink_to(tmp_path / "outside")
    result = _node(f"""
      const errors=[];
      for(const path of ['/../outside','/escape']){{try{{await wrapper.readSiteMember({json.dumps(str(site))},path,new Map());}}catch(error){{errors.push(String(error));}}}}
      console.log(JSON.stringify(errors));
    """)
    assert len(result) == 2
    assert all("site request escapes root" in error for error in result)


def test_candidate_guard_allows_only_disjoint_uncommitted_work(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    for name in ["consumed.js", "unrelated.py"]:
        (repository / name).write_text("original\n")
    for args in [
        ["init", "--quiet"],
        ["add", "consumed.js", "unrelated.py"],
        [
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--quiet",
            "-m",
            "fixture",
        ],
    ]:
        subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True)
    (repository / "unrelated.py").write_text("disjoint\n")
    script = f"""
      try{{console.log(JSON.stringify({{head:wrapper.requireScopedCandidate({json.dumps(str(repository))},['consumed.js'])}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """
    assert len(_node(script)["head"]) == 40
    (repository / "consumed.js").write_text("changed\n")
    assert "local edits" in _node(script)["error"]


def test_current_controller_delays_abort_stale_work_and_refuse_mismatched_data() -> (
    None
):
    module = MODULE.with_name("selection-runtime.mjs")
    result = subprocess.run(
        ["node", str(module), str(REPOSITORY)],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    report = json.loads(result.stdout)
    assert len(report["assertions"]) == 7
    assert all(report["assertions"].values())
    assert set(report["refusals"]) == {
        "build",
        "version",
        "transport-digest",
        "byte-count",
        "http",
    }
    assert all("Reload the page" in refusal for refusal in report["refusals"].values())
    assert "no retained-map" in report["scope"]


def test_child_context_routes_only_javascript_and_keeps_parent_page_commands() -> None:
    result = _node("""
      const calls=[],raw={send:async(method,params)=>{calls.push({method,params});return {result:{value:'child'}};}};
      const child=wrapper.childRuntime(raw,42);
      await child.send('Runtime.evaluate',{expression:'location.pathname'});
      await child.send('Page.captureScreenshot',{format:'png'});
      await child.send('Network.setBlockedURLs',{urls:['provider']});
      console.log(JSON.stringify(calls));
    """)
    assert result == [
        {
            "method": "Runtime.evaluate",
            "params": {"expression": "location.pathname", "contextId": 42},
        },
        {"method": "Page.captureScreenshot", "params": {"format": "png"}},
        {"method": "Network.setBlockedURLs", "params": {"urls": ["provider"]}},
    ]


def test_extracted_transport_preserves_protocol_success_error_and_events() -> None:
    module = MODULE.with_name("browser-transport.mjs")
    result = _node(f"""
      import {{EventEmitter}} from 'node:events';
      const transport=await import({json.dumps(module.as_uri())});
      class Socket extends EventEmitter {{
        constructor(){{super();queueMicrotask(()=>this.emit('open'));}}
        addEventListener(name,callback,options){{options?.once?this.once(name,callback):this.on(name,callback);}}
        send(text){{const request=JSON.parse(text);queueMicrotask(()=>{{
          const response=request.method==='Failure'?{{id:request.id,error:{{code:-1,message:'controlled'}}}}:{{id:request.id,result:{{result:{{value:request.params.expression??'ok'}}}}}};
          this.emit('message',{{data:JSON.stringify(response)}});
          this.emit('message',{{data:JSON.stringify({{method:'Page.loadEventFired',params:{{timestamp:1}}}})}});
        }});}}
        close(){{this.closed=true;}}
      }}
      globalThis.WebSocket=Socket;
      const cdp=await transport.connectCdp('ws://controlled');
      const events=[];cdp.onEvent(event=>events.push(event.method));
      const loaded=cdp.waitFor('Page.loadEventFired',1000);
      const value=await transport.evaluate(cdp,'controlled-expression');
      let refused=false;try{{await cdp.send('Failure');}}catch(error){{refused=/controlled/.test(String(error));}}
      console.log(JSON.stringify({{value,loaded:await loaded,refused,events}}));cdp.close();
    """)
    assert result["value"] == "controlled-expression"
    assert result["loaded"] == {"timestamp": 1}
    assert result["refused"] is True
    assert result["events"] == ["Page.loadEventFired", "Page.loadEventFired"]
