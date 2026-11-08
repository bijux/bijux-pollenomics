"""Reconstruct source-owned native scripts without executing their producer."""

import ast
import base64
import re
from pathlib import PurePosixPath

from .contract import (
    AdmissionError,
    canonical,
    digest,
    json_data,
    read_owned,
    recipe_template,
    relative,
)

_FIELDS = {
    "producer",
    "loader_symbol",
    "helper_factory_symbol",
    "helper_markers",
    "controller_source",
}


def recipe_paths(recipe):
    """Include every selected literal and executable source in producer custody."""
    if not isinstance(recipe, dict) or set(recipe) not in (
        {"template", "expansions", "slots"},
        {"template", "expansions", "slots", "external_runtime"},
    ):
        raise AdmissionError("unknown renderer recipe fields")
    paths = {
        relative(recipe["template"]),
        *[relative(row["path"]) for row in recipe["expansions"] if row.get("path")],
    }
    if "external_runtime" in recipe:
        external = recipe["external_runtime"]
        if not isinstance(external, dict) or set(external) != _FIELDS:
            raise AdmissionError(
                "external runtime requires exact source-selected fields"
            )
        symbols = [external["loader_symbol"], external["helper_factory_symbol"]]
        markers = external["helper_markers"]
        if not isinstance(markers, list) or len(markers) != 2:
            raise AdmissionError("external runtime requires two ordered marker symbols")
        symbols += markers
        if (
            any(
                not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*", name)
                for name in symbols
            )
            or len(set(symbols)) != 4
        ):
            raise AdmissionError("external runtime source symbols are ambiguous")
        paths.update(
            relative(external[name]) for name in ("producer", "controller_source")
        )
    return paths


def _literals(repo, external):
    """Read only single direct string assignments; imports and expressions stay inert."""
    names = [
        external["loader_symbol"],
        external["helper_factory_symbol"],
        *external["helper_markers"],
    ]
    found = {name: [] for name in names}
    try:
        tree = ast.parse(read_owned(repo, external["producer"]).decode())
    except (SyntaxError, UnicodeError) as error:
        raise AdmissionError(
            "external runtime producer is not readable Python source"
        ) from error
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for child in ast.walk(target):
                    if isinstance(child, ast.Name) and child.id in found:
                        found[child.id].append(node)
    result = {}
    for name, nodes in found.items():
        if (
            len(nodes) != 1
            or nodes[0] not in tree.body
            or not isinstance(nodes[0], (ast.Assign, ast.AnnAssign))
            or isinstance(nodes[0], ast.Assign)
            and (
                len(nodes[0].targets) != 1
                or not isinstance(nodes[0].targets[0], ast.Name)
            )
            or not isinstance(nodes[0].value, ast.Constant)
            or not isinstance(nodes[0].value.value, str)
        ):
            raise AdmissionError(
                "external runtime requires one direct string literal: " + name
            )
        result[name] = nodes[0].value.value
    return [result[name] for name in names]


def _json_node(document, identity):
    nodes = [node for node in document.scripts if node["attrs"].get("id") == identity]
    if (
        len(nodes) != 1
        or nodes[0]["attrs"] != {"id": identity, "type": "application/json"}
        or sum(attrs.get("id") == identity for _, attrs in document.tags) != 1
    ):
        raise AdmissionError(
            "external runtime requires one exact JSON binding: " + identity
        )
    return nodes[0]["body"]


def _runtime_payloads(repo, document, report, product_base, output):
    """Authenticate immutable runtime references and the complete script graph."""
    bootstrap = json_data(_json_node(document, report["bootstrap_id"]))
    if not isinstance(bootstrap, dict) or not isinstance(
        bootstrap.get("runtime"), dict
    ):
        raise AdmissionError("external runtime bootstrap reference absent")
    runtime = bootstrap["runtime"]
    if (
        set(runtime) != {"path", "byte_count", "integrity", "optional_controllers"}
        or not isinstance(runtime["optional_controllers"], dict)
        or set(runtime["optional_controllers"]) != {"evidence_tools", "index_transport"}
    ):
        raise AdmissionError("external runtime/controller population differs")
    references = [
        (
            {key: runtime[key] for key in ("path", "byte_count", "integrity")},
            "atlas-runtime",
        ),
        (runtime["optional_controllers"]["evidence_tools"], "atlas-evidence-tools"),
        (runtime["optional_controllers"]["index_transport"], "atlas-index-transport"),
    ]
    payloads = []
    runtime_paths = set()
    runtime_identities = {}
    parent = PurePosixPath(output).parent
    stem = PurePosixPath(output).stem
    for reference, kind in references:
        if not isinstance(reference, dict) or set(reference) != {
            "path",
            "byte_count",
            "integrity",
        }:
            raise AdmissionError("external runtime reference fields differ")
        name = relative(reference["path"])
        if "/" in name or not re.fullmatch(
            re.escape(stem) + r"\." + kind + r"\.[a-f0-9]{16}\.js", name
        ):
            raise AdmissionError("external runtime reference path differs")
        target = (parent / name).as_posix()
        resource = report["resources"].get(target)
        if (
            resource is None
            or resource.get("kind") != "reviewed-script"
            or resource.get("source") != "docs/" + target
        ):
            raise AdmissionError(
                "external runtime lacks exact reviewed script resource"
            )
        payload = read_owned(repo, resource["source"])
        expected = {
            "path": name,
            "byte_count": len(payload),
            "integrity": "sha256-"
            + base64.b64encode(bytes.fromhex(digest(payload))).decode(),
        }
        if (
            reference != expected
            or type(reference["byte_count"]) is not int
            or not 0 < len(payload) <= 524288
            or digest(payload) != resource["sha256"]
            or len(payload) != resource["bytes"]
            or name != stem + "." + kind + "." + digest(payload)[:16] + ".js"
        ):
            raise AdmissionError("external runtime bytes/name/SRI differ")
        runtime_paths.add(target)
        runtime_identities[target] = digest(payload)
        payloads.append(payload)
    direct_scripts = set()
    from urllib.parse import urljoin, urlsplit

    for node in document.scripts:
        if node["attrs"].get("src"):
            target = urlsplit(urljoin(product_base + output, node["attrs"]["src"]))
            base = urlsplit(product_base)
            if (
                target.netloc != base.netloc
                or not target.path.startswith(base.path)
                or target.query
                or target.fragment
            ):
                raise AdmissionError("external runtime direct script escapes owner")
            direct_scripts.add(target.path[len(base.path) :])
    owned_scripts = {
        name
        for name, row in report["resources"].items()
        if row["kind"] == "reviewed-script"
    }
    if (
        owned_scripts != runtime_paths | direct_scripts
        or runtime_paths & direct_scripts
    ):
        raise AdmissionError(
            "external runtime executable graph has missing or extra members"
        )
    return bootstrap, payloads, runtime_identities


def verify_external_runtime(
    repo,
    document,
    report,
    product_base,
    output,
    *,
    source_sha=None,
    source_descriptor=None,
):
    """Bind loader, split source, JSON parameters and the complete executable graph."""
    from .html import Document, executable_scripts, match_recipe_pattern

    recipe = report["recipe"]
    recipe_paths(recipe)
    external = recipe["external_runtime"]
    loader, factory, begin, end = _literals(repo, external)
    original = recipe_template(
        repo, recipe["template"], source_sha=source_sha, descriptor=source_descriptor
    )
    source = original.decode()
    for row in recipe["expansions"]:
        if source.count(row["token"]) != 1:
            raise AdmissionError("reviewed expansion must occupy one slot")
        source = source.replace(
            row["token"], read_owned(repo, row["path"]).decode() if row["path"] else ""
        )
    template = Document(source)
    source_scripts = executable_scripts(template)
    loader_scripts = executable_scripts(Document(loader))
    actual_scripts = executable_scripts(document)
    if (
        len(source_scripts) != 1
        or len(loader_scripts) != 1
        or len(actual_scripts) != 1
        or actual_scripts[0] != loader_scripts[0]
    ):
        raise AdmissionError(
            "external runtime loader differs from selected source literal"
        )
    pattern = source_scripts[0]["body"]
    if (
        not begin
        or not end
        or begin == end
        or pattern.count(begin) != 1
        or pattern.count(end) != 1
    ):
        raise AdmissionError("external runtime helper markers are not unique")
    first, last = [
        re.search(r"(?m)^[ \t]*" + re.escape(marker) + r"[ \t]*$", pattern)
        for marker in (begin, end)
    ]
    opening = re.match(r"\s*\(async \(\) => \{", pattern)
    closing = re.search(r"(?m)^[ \t]*\}\)\(\)\.catch\(", pattern)
    if (
        first is None
        or last is None
        or opening is None
        or closing is None
        or not opening.end() <= first.start() < last.start() < closing.start()
    ):
        raise AdmissionError(
            "external runtime helper boundary is outside its safe IIFE"
        )
    helpers = pattern[first.end() : last.start()]
    if (
        not helpers.strip()
        or factory.count("%s") != 1
        or "%" in factory.replace("%s", "")
    ):
        raise AdmissionError(
            "external runtime helper factory requires one literal slot"
        )
    main_pattern = pattern[: first.start()] + pattern[last.end() :]
    helper_pattern = factory % helpers
    bootstrap, payloads, runtime_identities = _runtime_payloads(
        repo, document, report, product_base, output
    )
    values = {}
    count = 0

    def match(pattern, body):
        nonlocal count
        observed, total = match_recipe_pattern(
            pattern, body, recipe["slots"], product_base, output
        )
        count += total
        for name, value in observed.items():
            if name in values and values[name] != value:
                raise AdmissionError("inconsistent repeated external runtime binding")
            values[name] = value

    match(main_pattern, payloads[0].decode())
    match(helper_pattern, payloads[1].decode())
    if payloads[2] != read_owned(repo, external["controller_source"]):
        raise AdmissionError("external index controller differs from selected source")
    original_bootstrap = dict(bootstrap)
    del original_bootstrap["runtime"]
    for node in template.scripts:
        if node["attrs"].get("type") != "application/json":
            continue
        name = node["attrs"].get("id")
        if not name:
            raise AdmissionError("external runtime JSON binding has no exact identity")
        actual = _json_node(document, name)
        json_data(actual)
        tokens = re.findall(r"__[A-Z][A-Z0-9_]+__", node["body"])
        if not tokens or any(
            recipe["slots"].get(token) != {"kind": "json"} for token in tokens
        ):
            raise AdmissionError(
                "external runtime JSON binding lacks finite JSON slots"
            )
        if name == report["bootstrap_id"]:
            actual = canonical(original_bootstrap).decode()
        match(node["body"], actual)
    expected_bindings = {
        node["attrs"].get("id")
        for node in template.scripts
        if node["attrs"].get("type") == "application/json"
    }
    actual_bindings = {
        node["attrs"].get("id")
        for node in document.scripts
        if node["attrs"].get("type") == "application/json"
    }
    if actual_bindings != expected_bindings:
        raise AdmissionError("external runtime JSON binding graph differs")
    from .runtime_graph import verify_registration_graph

    binding_bytes = sum(
        len(_json_node(document, name).encode())
        for name in actual_bindings
        if name != report["bootstrap_id"]
    )
    graph = verify_registration_graph(
        bootstrap,
        report["resources"],
        output,
        payloads,
        binding_bytes,
        len(_json_node(document, report["bootstrap_id"]).encode()),
    )
    receipt = {
        "recipe_sha256": digest(original),
        "parameters_sha256": digest(canonical(values)),
        "slot_count": count,
        "external_runtime": runtime_identities,
        "transport_graph": graph,
    }
    return receipt, [{"body": payload.decode(), "attrs": {}} for payload in payloads]


def provider_bodies(repo, document, report, product_base, output, **context):
    """Provider inspection follows authenticated external code; inline CSP stays separate."""
    from .html import executable_scripts

    if "external_runtime" not in report["recipe"]:
        return executable_scripts(document)
    return verify_external_runtime(
        repo, document, report, product_base, output, **context
    )[1]
