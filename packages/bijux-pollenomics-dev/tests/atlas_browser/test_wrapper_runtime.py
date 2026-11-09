"""Exercise wrapper authority and the actual maintained selection loader offline."""

from __future__ import annotations

import base64
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
    repository = tmp_path / "repository"
    site = repository / "artifacts/docs/site"
    source = b"# Nordic Evidence Atlas\n"
    parent = b'<iframe src="../../report/regions/nordic/nordic_map.html"></iframe>'
    child = b'<script id="atlas-static-bootstrap">{"build_id":"build","version":"source"}</script>'
    paths = {
        repository / "docs/public/nordic-atlas/index.md": source,
        repository / "docs/report/regions/nordic/nordic_map.html": child,
        site / "public/nordic-atlas/index.html": parent,
        site / "report/regions/nordic/nordic_map.html": child,
        repository / "docs/report/regions/nordic/chunk.js": b"original raw chunk",
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
    pin = repository / ".github/standards/bijux-docs.sha"
    pin.parent.mkdir(parents=True)
    pin.write_text("a" * 40 + "\n")
    for args in [
        ["init", "--quiet"],
        ["add", "configs", "docs", ".github"],
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
    _publication(repository, site)
    return repository, site, owner


def _publication(repository: Path, site: Path) -> None:
    """Model only the existing publication inventory's source/physical binding."""

    def git(ref: str) -> str:
        return subprocess.check_output(
            ["git", "rev-parse", ref], cwd=repository, text=True
        ).strip()

    checkpoint = {
        "repository_source": {"sha": git("HEAD"), "tree": git("HEAD^{tree}")},
        "standard": {"sha": "a" * 40},
        "site_url": "https://bijux.io/bijux-pollenomics/",
        "site_dir": "artifacts/docs/site",
    }
    raw = json.dumps(checkpoint).encode()
    evidence = repository / "artifacts/website-security"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "source-identity.json").write_bytes(raw)
    owner = json.loads((repository / "configs/docs/maps/report-owner.json").read_text())
    publication = {
        "schema": 2,
        "repository_source_sha": git("HEAD"),
        "standard_sha": "a" * 40,
        "site_url": checkpoint["site_url"],
        "site_dir": checkpoint["site_dir"],
        "qualification": {
            "source": {"sha256": _sha(raw), "receipt": checkpoint},
            "csp": {
                "receipt": {
                    "embedded": {
                        "records": [
                            {
                                "kind": "owned-parent-frame",
                                "path": row["output"],
                                "source": row["source"],
                                "input_sha256": row["built_html_sha256"],
                            }
                            for row in owner["parents"]
                        ]
                        + [
                            {
                                "kind": "owned-report",
                                "path": row["output"],
                                "source": row["source"],
                                "input_sha256": row["source"]["sha256"],
                            }
                            for row in owner["reports"]
                        ]
                    }
                }
            },
        },
        "files": [
            {
                "path": path.relative_to(site).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": _sha(path.read_bytes()),
            }
            for path in sorted(site.rglob("*"))
            if path.is_file()
        ],
    }
    (evidence / "publication.json").write_text(json.dumps(publication))


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
            "report/regions/nordic/chunk.js",
            "report/regions/nordic/nordic_map.html",
        ],
    }


def test_normalized_child_is_bound_separately_from_unchanged_raw_source(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, owner = authority
    child = site / owner["reports"][0]["output"]
    child.write_bytes(
        b'<head><meta name="reader-return" content="science"></head>'
        + child.read_bytes()
    )
    assert _sha(child.read_bytes()) != owner["reports"][0]["source"]["sha256"]
    _publication(repository, site)
    assert _read_authority(repository, site)["build"] == "build"


def test_normalized_parent_and_child_bind_final_bytes_separately_from_raw_inputs(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, owner = authority
    for row in [owner["parents"][0], owner["reports"][0]]:
        path = site / row["output"]
        path.write_bytes(
            b'<head><meta http-equiv="Content-Security-Policy" content="default-src \'none\'"></head>'
            + path.read_bytes()
            + b'<nav><a href="/bijux-pollenomics/science/">Science</a></nav>'
        )
    assert (
        _sha((site / owner["parents"][0]["output"]).read_bytes())
        != owner["parents"][0]["built_html_sha256"]
    )
    _publication(repository, site)
    assert _read_authority(repository, site)["build"] == "build"


@pytest.mark.parametrize(
    "tamper", ["parent-input", "child-input", "source", "kind", "duplicate", "missing"]
)
def test_raw_composition_bindings_remain_required_after_normalization(
    authority: tuple[Path, Path, dict[str, Any]], tamper: str
) -> None:
    repository, site, _ = authority
    path = repository / "artifacts/website-security/publication.json"
    publication = json.loads(path.read_text())
    records = publication["qualification"]["csp"]["receipt"]["embedded"]["records"]
    if tamper in {"parent-input", "child-input"}:
        index = 1 if tamper == "child-input" else 0
        records[index]["input_sha256"] = "b" * 64
    elif tamper == "source":
        records[0]["source"]["sha256"] = "b" * 64
    elif tamper == "kind":
        records[0]["kind"] = "owned-report"
    elif tamper == "duplicate":
        records.append(records[0])
    else:
        records.pop(0)
    path.write_text(json.dumps(publication))
    assert "raw embedded source differs" in _read_authority(repository, site)["error"]


@pytest.mark.parametrize(
    "tamper", ["source", "standard", "checkpoint", "duplicate", "resource"]
)
def test_stale_or_ambiguous_publication_inventory_refuses(
    authority: tuple[Path, Path, dict[str, Any]], tamper: str
) -> None:
    repository, site, _ = authority
    path = repository / "artifacts/website-security/publication.json"
    publication = json.loads(path.read_text())
    if tamper == "source":
        publication["repository_source_sha"] = "b" * 40
    elif tamper == "standard":
        publication["standard_sha"] = "b" * 40
    elif tamper == "checkpoint":
        publication["qualification"]["source"]["sha256"] = "b" * 64
    elif tamper == "duplicate":
        publication["files"].append(publication["files"][0])
    else:
        next(row for row in publication["files"] if row["path"].endswith("chunk.js"))[
            "sha256"
        ] = "b" * 64
    path.write_text(json.dumps(publication))
    assert "error" in _read_authority(repository, site)


def test_unlisted_resource_cannot_be_served(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, _ = authority
    (site / "foreign.js").write_bytes(b"unowned executable")
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      try{{await wrapper.readSiteMember({json.dumps(str(site))},'/foreign.js',authority.expected);console.log(JSON.stringify({{accepted:true}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    assert "owned site member differs" in result["error"]


def test_unlisted_alias_to_owned_bytes_cannot_be_served(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, _ = authority
    (site / "unlisted.js").symlink_to(site / "report/regions/nordic/chunk.js")
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      try{{await wrapper.readSiteMember({json.dumps(str(site))},'/unlisted.js',authority.expected);console.log(JSON.stringify({{accepted:true}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    assert "site member alias is forbidden" in result["error"]


@pytest.mark.parametrize(
    "target,reason",
    [
        ("parent", "built wrapper differs"),
        ("child", "built child differs"),
        ("source", "wrapper source differs"),
        ("canonical", "canonical map differs"),
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
    _publication(repository, site)
    assert (
        "real wrapper iframe target differs"
        in _read_authority(repository, site)["error"]
    )


def test_parent_cannot_use_a_foreign_origin_with_the_same_child_path(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, owner = authority
    path = site / "public/nordic-atlas/index.html"
    path.write_bytes(
        b'<iframe src="https://elsewhere.invalid/bijux-pollenomics/report/regions/nordic/nordic_map.html"></iframe>'
    )
    owner["parents"][0]["built_html_sha256"] = _sha(path.read_bytes())
    (repository / "configs/docs/maps/report-owner.json").write_text(json.dumps(owner))
    _publication(repository, site)
    assert (
        "real wrapper iframe target differs"
        in _read_authority(repository, site)["error"]
    )


def test_production_origin_reply_keeps_the_qualified_csp_bytes_unmodified(
    authority: tuple[Path, Path, dict[str, Any]],
) -> None:
    repository, site, _ = authority
    path = site / "public/nordic-atlas/index.html"
    content = (
        b'<head><meta http-equiv="Content-Security-Policy" content="frame-src https://bijux.io/bijux-pollenomics/report/regions/nordic/nordic_map.html"></head>'
        + path.read_bytes()
    )
    path.write_bytes(content)
    _publication(repository, site)
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      const calls=[],cdp={{send:async(method,params)=>{{calls.push({{method,params}});}}}};
      const reply=await wrapper.fulfillPublicationRequest(cdp,{json.dumps(str(site))},{{requestId:'owned',request:{{url:authority.parentUrl,method:'GET'}}}},authority);
      console.log(JSON.stringify({{parent:authority.parentUrl,child:authority.childUrl,reply,calls}}));
    """)
    assert (
        result["parent"]
        == "https://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html"
    )
    assert (
        result["child"]
        == "https://bijux.io/bijux-pollenomics/report/regions/nordic/nordic_map.html"
    )
    assert len(result["calls"]) == 1
    assert result["calls"][0]["method"] == "Fetch.fulfillRequest"
    assert result["calls"][0]["params"]["requestId"] == "owned"
    assert result["calls"][0]["params"]["responseCode"] == 200
    assert base64.b64decode(result["calls"][0]["params"]["body"]) == content
    assert result["reply"]["bytes"] == len(content)


@pytest.mark.parametrize(
    ("url", "method"),
    [
        ("http://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html", "GET"),
        (
            "https://elsewhere.invalid/bijux-pollenomics/public/nordic-atlas/index.html",
            "GET",
        ),
        (
            "https://bijux.io/bijux-pollenomics-other/public/nordic-atlas/index.html",
            "GET",
        ),
        (
            "https://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html?changed=1",
            "GET",
        ),
        (
            "https://user@bijux.io/bijux-pollenomics/public/nordic-atlas/index.html",
            "GET",
        ),
        ("https://bijux.io/bijux-pollenomics/public%2Fnordic-atlas/index.html", "GET"),
        (
            "https://bijux.io/bijux-pollenomics/public/../public/nordic-atlas/index.html",
            "GET",
        ),
        ("https://bijux.io/bijux-pollenomics/foreign.js", "GET"),
        ("https://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html", "POST"),
    ],
)
def test_production_reply_refuses_origin_prefix_alias_and_unowned_requests(
    authority: tuple[Path, Path, dict[str, Any]], url: str, method: str
) -> None:
    repository, site, _ = authority
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      const calls=[],cdp={{send:async(method,params)=>{{calls.push({{method,params}});}}}};
      try{{await wrapper.fulfillPublicationRequest(cdp,{json.dumps(str(site))},{{requestId:'refused',request:{{url:{json.dumps(url)},method:{json.dumps(method)}}}}},authority);console.log(JSON.stringify({{accepted:true,calls}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error),calls}}));}}
    """)
    assert "error" in result
    assert result["calls"] == []


@pytest.mark.parametrize("header", ["Authorization", "Cookie", "X-Api-Key"])
def test_owned_publication_reply_refuses_credential_headers(
    authority: tuple[Path, Path, dict[str, Any]], header: str
) -> None:
    repository, site, _ = authority
    result = _node(f"""
      const authority=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});
      const calls=[],cdp={{send:async(method,params)=>{{calls.push({{method,params}});}}}};
      try{{await wrapper.fulfillPublicationRequest(cdp,{json.dumps(str(site))},{{requestId:'refused',request:{{url:authority.parentUrl,method:'GET',headers:{{{json.dumps(header)}:'constructed'}}}}}},authority);console.log(JSON.stringify({{accepted:true,calls}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error),calls}}));}}
    """)
    assert "outside the exact production publication" in result["error"]
    assert result["calls"] == []


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


@pytest.mark.parametrize("size", [20_182_989, 32 * 1024 * 1024 + 1])
def test_wrapper_receipt_metadata_budget_covers_the_qualified_manifest(
    authority: tuple[Path, Path, dict[str, Any]], size: int
) -> None:
    repository, site, _ = authority
    path = repository / "artifacts/website-security/publication.json"
    original = path.read_bytes()
    path.write_bytes(original + b" " * (size - len(original)))
    result = _node(f"""
      try{{const value=await wrapper.readWrapperAuthority({json.dumps(str(repository))},{json.dumps(str(site))});console.log(JSON.stringify({{publication:value.publication}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    if size > 32 * 1024 * 1024:
        assert "publication receipt exceeds byte budget" in result["error"]
    else:
        assert result["publication"]["sha256"] == _sha(path.read_bytes())


def test_wrapper_public_resource_budget_stays_at_sixteen_mebibytes(
    tmp_path: Path,
) -> None:
    site = tmp_path / "site"
    site.mkdir()
    path = site / "public.json"
    with path.open("wb") as stream:
        stream.truncate(16 * 1024 * 1024 + 1)
    result = _node(f"""
      try{{await wrapper.readSiteMember({json.dumps(str(site))},'/public.json',new Map());console.log(JSON.stringify({{accepted:true}}));}}
      catch(error){{console.log(JSON.stringify({{error:String(error)}}));}}
    """)
    assert "oversized" in result["error"]


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


@pytest.mark.parametrize(
    "damage",
    [
        "load-timeout",
        "navigate-error",
        "connect-error",
        "close-error",
        "event-overflow",
    ],
)
def test_provider_open_failure_retains_case_and_closes_only_owned_targets(
    damage: str,
) -> None:
    # Controlled CDP replies exercise the real owner and provider-case loop;
    # they are not browser, publication or scientific qualification evidence.
    provider = MODULE.with_name("provider-failures.mjs").as_uri()
    result = _node(
        f"""
      const provider=await import({json.dumps(provider)});
      const damage={json.dumps(damage)}, trace=[], records=[], sockets=[], targets=[];
      const authority={{parentUrl:'https://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html',childUrl:'https://bijux.io/bijux-pollenomics/report/regions/nordic/nordic_map.html'}};
      const facts={{title:'Nordic atlas',iframe_visible:true,navigation_available:true}};
      let active, captureCalls=0, evaluates=0;
      const closeCounts={{}}, socketCounts={{}}, waits=[];
      const fetchTarget=async(url,options)=>{{
        if(url.includes('/json/new')){{
          const target={{id:`target-${{targets.length+1}}`,webSocketDebuggerUrl:`ws://target-${{targets.length+1}}`}};
          targets.push(target);trace.push(['create',target.id]);
          return {{ok:true,json:async()=>target}};
        }}
        const id=url.split('/').at(-1);trace.push(['close-target',id]);
        closeCounts[id]=(closeCounts[id]??0)+1;
        return {{ok:!(damage==='close-error'&&id==='target-2'),status:500,text:async()=>'Target is closing'}};
      }};
      const connect=async(url)=>{{
        const id=url.slice(5);if(damage==='connect-error'&&id==='target-2')throw Error('controlled connection failure');
        const listeners=[];let rejectLoad;
        const raw={{
          onEvent(listener){{listeners.push(listener)}},
          emit(event){{for(const listener of listeners)listener(event)}},
          waitFor(method,timeout){{
            trace.push(['wait',id]);waits.push(timeout);
            return new Promise((resolve,reject)=>{{
              rejectLoad=reject;
              if(id==='target-1')resolve({{timestamp:1}});
              else if(damage!=='navigate-error')queueMicrotask(()=>reject(Error('Page.loadEventFired timed out')));
            }});
          }},
          async send(method,params={{}}){{
            if(method==='Runtime.enable')raw.emit({{method:'Runtime.executionContextCreated',params:{{context:{{id:42,auxData:{{isDefault:true,frameId:'child'}}}}}}}});
            if(method==='Page.navigate'){{
              trace.push(['navigate',id]);
              if(id==='target-2'&&damage==='navigate-error')throw Error('controlled navigation refusal');
              if(id==='target-2'&&damage==='event-overflow')for(let i=0;i<300;i++){{
                raw.emit({{method:'Page.frameNavigated',params:{{frame:{{id:'x'.repeat(2000),loaderId:`loader-${{i}}`}}}}}});
                if(i<80)raw.emit({{method:'Runtime.consoleAPICalled',params:{{type:'error',args:[{{value:'y'.repeat(20000)}}]}}}});
              }}
              return {{frameId:'parent',loaderId:`loader-${{id}}`}};
            }}
            if(method==='Page.getFrameTree')return {{frameTree:{{frame:{{id:'parent'}},childFrames:[{{frame:{{id:'child',loaderId:'child-loader',url:authority.childUrl}}}}]}}}};
            if(method==='Runtime.evaluate')return {{result:{{value:facts}}}};
            return {{}};
          }},
          close(){{
            trace.push(['close-socket',id]);socketCounts[id]=(socketCounts[id]??0)+1;
            rejectLoad?.(Error('controlled transport closed'));
          }},
        }};
        sockets.push(raw);return raw;
      }};
      const owner=wrapper.createWrapperAtlasOwner({{site:'/unused',authority,debuggerOrigin:new URL('http://debugger.invalid'),requests:[],serverErrors:[],externalRefusals:[],timeoutMs:15000,fetchTarget,connect}});
      const controls=Object.fromEntries(['legend_toggles_and_restores','country_filter_changes','country_filter_restores','time_control_changes','time_control_restores','counts_restore','popup_opens_and_closes','evidence_rendered'].map(key=>[key,true]));
      const evaluate=async()=>{{
        evaluates++;
        if(evaluates===1||evaluates===6)return 'payload-identity';
        if(evaluates===3){{
          for(const [i,host]of ['tile.openstreetmap.org','tile.openstreetmap.org','tile.openstreetmap.org','tile.opentopomap.org'].entries())active.raw.emit({{method:'Fetch.requestPaused',params:{{requestId:`request-${{i}}`,networkId:`network-${{i}}`,request:{{url:`https://${{host}}/4/${{i}}/1.png`,headers:{{}}}}}}}});
        }}
        if(evaluates===4)return {{snapshot:{{build_id:'build',basemap:'terrain'}},readout:'terrain available',transitions:[{{readout:'street unavailable'}}],failure_counts:[{{provider:'street',count:3,threshold:3}}],elapsed_ms:1,timed_out:false}};
        if(evaluates===5)return controls;
        if(evaluates===7)return true;
      }};
      let error;
      try{{await provider.verifyProviderFailureMatrix({{name:'nordic-wrapper'}},'http://debugger.invalid',{{
        candidate:{{build_id:'build'}},timeoutMs:15000,evidenceIdentity:row=>row.build_id,
        openAtlas:async(...args)=>{{active=await owner.openAtlas(...args);return active}},
        closeAtlas:owner.closeAtlas,
        captureReady:async()=>{{captureCalls++;return {{build_id:'build'}}}},
        evaluate,screenshot:async()=>{{}},writeScenario:async(_scope,row)=>records.push(structuredClone(row)),
      }})}}catch(value){{error=String(value)}}
      // Cleanup is idempotent after both successful and failed acquisitions.
      await owner.closeAtlas(active);
      console.log(JSON.stringify({{error,records,lifecycle:owner.lifecycle,closeCounts,socketCounts,targets,trace,waits,captureCalls,assertionKeys:provider.PROVIDER_MATRIX_ASSERTIONS}}));
    """
    )
    assert result["error"]
    assert [row["name"] for row in result["records"]] == [
        "provider-http-401",
        "provider-http-403",
    ]
    first, failed = result["records"]
    assert all(first["assertions"].values())
    assert all(first["ui"].values())
    lifecycle = first["lifecycle"]
    assert lifecycle["navigation"]["frame_id"] == "parent"
    assert lifecycle["navigation"]["loader_id"] == "loader-target-1"
    assert lifecycle["child_frame_id"] == "child"
    assert lifecycle["child_loader_id"] == "child-loader"
    phases = [row["phase"] for row in lifecycle["events"]]
    assert phases.index("load_wait_registered") < phases.index("navigate_requested")
    assert phases.index("navigate_requested") < phases.index("navigate_response")
    assert "load_event_received" in phases
    times = [row["elapsed_ms"] for row in lifecycle["events"]]
    assert times == sorted(times) and times[0] >= 0
    assert not any(failed["assertions"].values())
    assert set(failed["assertions"]) == set(result["assertionKeys"])
    assert failed["status"] == "open_failed"
    assert failed["lifecycle"]["case"] == "provider-http-403"
    assert failed["lifecycle"]["target_id"] == "target-2"
    assert result["captureCalls"] == 1
    assert result["closeCounts"] == {"target-1": 1, "target-2": 1}
    assert result["socketCounts"] == (
        {"target-1": 1} if damage == "connect-error" else {"target-1": 1, "target-2": 1}
    )
    assert [row["id"] for row in result["targets"]] == ["target-1", "target-2"]
    assert result["waits"] == ([15000] if damage == "connect-error" else [15000, 15000])
    assert failed["lifecycle"]["failure_phase"] == (
        "connect_target" if damage == "connect-error" else "navigate"
    )
    assert failed["lifecycle"]["teardown"]["target_close_acknowledged"] is (
        damage != "close-error"
    )
    if damage == "close-error":
        assert "owned target close failed" in failed["lifecycle"]["cleanup_error"]
        assert "Page.loadEventFired timed out" in result["error"]
    if damage == "event-overflow":
        events = failed["lifecycle"]["events"]
        assert len(events) == 128
        assert failed["lifecycle"]["omitted_events"] > 0
        assert all(len(str(row.get("frame_id", ""))) <= 512 for row in events)
        assert len(failed["runtime_failures"]) == 32
        assert failed["omitted_runtime_failures"] == 48
        assert all(len(row["detail"]) <= 2048 for row in failed["runtime_failures"])
        assert len(json.dumps(failed).encode()) < 200_000


@pytest.mark.parametrize("receipt_store", ["missing-directory", "blocked-directory"])
def test_first_failed_open_persists_without_a_screenshot_and_keeps_original_error(
    tmp_path: Path, receipt_store: str
) -> None:
    output = tmp_path / "browser"
    output.mkdir()
    if receipt_store == "blocked-directory":
        (output / "nordic-wrapper").write_text("not a directory\n")
    provider = MODULE.with_name("provider-failures.mjs").as_uri()
    result = _node(
        f"""
      import {{readFile}} from 'node:fs/promises';
      const provider=await import({json.dumps(provider)}),output={json.dumps(str(output))};
      const navigationError=Error('Page.loadEventFired timed out');
      let targets=0,targetCloses=0,socketCloses=0,captureCalls=0,screenshots=0;
      let receipts=[];
      const raw={{onEvent(){{}},waitFor(method,timeout){{
        if(method!=='Page.loadEventFired'||timeout!==15000)throw Error('wrong load gate');
        return Promise.reject(navigationError);
      }},async send(method){{
        return method==='Page.navigate'?{{frameId:'parent',loaderId:'loader-first'}}:{{}};
      }},close(){{socketCloses++}}}};
      const fetchTarget=async url=>{{
        if(url.includes('/json/new')){{targets++;return {{ok:true,json:async()=>({{id:'first-target',webSocketDebuggerUrl:'ws://controlled'}})}}}}
        targetCloses++;return {{ok:true,text:async()=>'Target is closing'}};
      }};
      const owner=wrapper.createWrapperAtlasOwner({{site:'/unused',authority:{{
        parentUrl:'https://bijux.io/bijux-pollenomics/public/nordic-atlas/index.html',
        childUrl:'https://bijux.io/bijux-pollenomics/report/regions/nordic/nordic_map.html',
      }},debuggerOrigin:new URL('http://debugger.invalid'),requests:[],serverErrors:[],
        externalRefusals:[],timeoutMs:15000,fetchTarget,connect:async()=>raw}});
      let caught;
      try{{await provider.verifyProviderFailureMatrix({{name:'nordic-wrapper'}},'http://debugger.invalid',{{
        candidate:{{build_id:'unused'}},timeoutMs:15000,evidenceIdentity:row=>row,
        openAtlas:owner.openAtlas,closeAtlas:owner.closeAtlas,
        captureReady:async()=>{{captureCalls++;throw Error('unexpected capture')}},
        evaluate:async()=>{{throw Error('unexpected evaluation')}},
        screenshot:async()=>{{screenshots++;throw Error('unexpected screenshot')}},
        writeScenario:(_scope,scenario,paths)=>{{receipts=paths;return wrapper.writeWrapperScenario(output,scenario,paths)}},
      }})}}catch(error){{caught=error}}
      let persisted=null;
      try{{persisted=JSON.parse(await readFile(output+'/nordic-wrapper/provider-http-401.json','utf8'))}}catch{{}}
      console.log(JSON.stringify({{error:String(caught),sameOriginalError:caught===navigationError,
        persisted,receipts,lifecycle:owner.lifecycle,targets,targetCloses,socketCloses,captureCalls,screenshots}}));
    """
    )
    assert result["sameOriginalError"] is True
    assert result["error"] == "Error: Page.loadEventFired timed out"
    assert result["targets"] == result["targetCloses"] == result["socketCloses"] == 1
    assert result["captureCalls"] == result["screenshots"] == 0
    lifecycle = result["lifecycle"][0]
    assert lifecycle["case"] == "provider-http-401"
    assert lifecycle["status"] == "open_failed"
    assert lifecycle["failure_phase"] == "navigate"
    assert lifecycle["target_id"] == "first-target"
    assert lifecycle["teardown"]["target_close_acknowledged"] is True
    if receipt_store == "missing-directory":
        persisted = result["persisted"]
        assert persisted["status"] == "open_failed"
        assert persisted["lifecycle"] == lifecycle
        assert "Page.loadEventFired timed out" in persisted["error"]
        assert len(persisted["assertions"]) == 10
        assert not any(persisted["assertions"].values())
        assert result["receipts"] == ["nordic-wrapper/provider-http-401.json"]
        assert "receipt_error" not in lifecycle
    else:
        assert result["persisted"] is None
        assert result["receipts"] == []
        assert "EEXIST" in lifecycle["receipt_error"]
        assert len(lifecycle["receipt_error"]) <= 4096


def test_successful_scenario_receipt_write_failure_still_refuses(
    tmp_path: Path,
) -> None:
    output = tmp_path / "browser"
    output.mkdir()
    (output / "nordic-wrapper").write_text("not a directory\n")
    result = _node(
        f"""
      const scenario={{name:'provider-http-401'}},receipts=[];let error;
      try{{await wrapper.writeWrapperScenario({json.dumps(str(output))},scenario,receipts)}}
      catch(value){{error=String(value)}}
      console.log(JSON.stringify({{error,receipts}}));
    """
    )
    assert "EEXIST" in result["error"]
    assert result["receipts"] == []
