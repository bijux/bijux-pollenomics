"""Authenticate complete chain closure and retained native child-pointer sources."""

from __future__ import annotations

from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
from typing import Any

from bijux_pollenomics.core.filesystem import BoundedInputTree

from .....ancillary_store.context import load_neotoma_ancillary_context
from .....resource_catalogue.archive.files import _digest
from ....receipts import _object, _safe_root, _validate_transport_failure
from ....resources.models import DEVELOPMENT_ROLES
from ...assessment import assess_http
from ...authority import authenticate_linked_root_metadata
from ...evidence import (
    iter_neotoma_linked_evidence_occurrences,
    read_neotoma_linked_evidence_metadata,
)
from ...profiles import _UnavailableLinkedSource, parse_neotoma_linked_source
from ...protocol import request_for
from ...replay import _control
from .. import publication as baseline_publication
from .. import storage
from .capture_inputs import (
    advance_metadata,
    check_capture,
    check_group,
    preflight_sources,
)
from .models import (
    COLLECTIONS,
    MAX_ENTITY_BYTES,
    MAX_SOURCE_BYTES,
    SCHEMA,
    AncestrySourceBudget,
    NeotomaTaxonAncestryChainLimits,
    NeotomaTaxonAncestryChainSources,
    baseline_limits,
    capture_population,
    entity_role,
    reconcile_roots,
    strongest_roles,
    validate_sources,
)
from .projection import delta, native_edges, project


class ChainOperation:
    """Own finite source seals and caches for one complete chain operation."""

    def __init__(self, sources: NeotomaTaxonAncestryChainSources) -> None:
        """Validate explicit resolvers without opening native source bodies."""
        validate_sources(sources)
        self.sources = sources
        self.stack = ExitStack()
        self.trees: dict[Path, BoundedInputTree] = {}
        self.budget = AncestrySourceBudget()
        self.epochs: dict[tuple[str, str], dict[str, Any]] = {}
        self.capture_pins: set[str] = set()
        self.history: dict[int, str] = {}
        self.controls: dict[
            tuple[str, str | None], tuple[dict[str, Any], dict[str, Any]]
        ] = {}

    def seal(
        self, directory: Path, *, bound: int = MAX_SOURCE_BYTES
    ) -> BoundedInputTree:
        """Inventory each literal namespace once and account unique physical bytes."""
        root = _safe_root(directory)
        if root not in self.trees:
            tree = self.stack.enter_context(
                BoundedInputTree(root, max_bytes=bound, max_files=self.budget.max_files)
            )
            self.budget.include(tree.files)
            self.trees[root] = tree
        return self.trees[root]

    def read(self, root: Path, relative: str, bound: int) -> bytes:
        """Read one selected source buffer under its original operation seal."""
        if (
            not isinstance(relative, str)
            or relative.startswith("/")
            or any(part in {"", ".", ".."} for part in relative.split("/"))
        ):
            raise ValueError("Ancestry source member is not a literal safe path")
        tree = self.seal(root)
        return tree.read(tree.root / relative, max_bytes=bound)

    def epoch(self, context_pin: str, native_pin: str) -> dict[str, Any]:
        """Authenticate a recorded epoch without substituting the fresh current epoch."""
        key = context_pin, native_pin
        if key in self.epochs:
            return self.epochs[key]
        sources = self.sources
        original = sources.recorded_baseline_sources
        contexts = {
            original.expected_context_sha256: original.context_directory,
            **sources.context_sources,
            sources.expected_current_context_sha256: sources.current_context_directory,
        }
        natives = {
            original.expected_native_archive_sha256: original.native_archive_directory,
            **sources.native_archive_sources,
            sources.expected_current_native_archive_sha256: sources.current_native_archive_directory,
        }
        if (
            not _digest(context_pin)
            or not _digest(native_pin)
            or context_pin not in contexts
            or native_pin not in natives
        ):
            raise ValueError("Ancestry historical source epoch resolver is missing")
        self.seal(contexts[context_pin], bound=512 * 1024 * 1024)
        self.seal(natives[native_pin], bound=512 * 1024 * 1024)
        context = load_neotoma_ancillary_context(
            contexts[context_pin],
            expected_manifest_sha256=context_pin,
            native_archive_directory=natives[native_pin],
        )
        if context.manifest["native_archive"]["manifest_sha256"] != native_pin:
            raise ValueError(
                "Ancestry context independently pinned native epoch differs"
            )
        header = read_neotoma_linked_evidence_metadata(
            original.evidence.directory,
            expected_manifest_sha256=original.evidence.manifest_sha256,
        )
        roster = context.manifest["native_archive"]["current_roster_sha256"]
        if roster not in context.current_scope_inputs:
            raise ValueError("Ancestry complete current roster binding is missing")
        current = authenticate_linked_root_metadata(
            expected_roster_sha256=roster, scope=context.current_scope_inputs[roster]
        )
        current = reconcile_roots(header["authority"]["root_identities"], current)
        self.epochs[key] = current
        return current

    def baseline(
        self, limits: NeotomaTaxonAncestryChainLimits, *, native_replay: bool = True
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Replay the externally pinned baseline once, preserving its frozen seeds."""
        sources, original = self.sources, self.sources.recorded_baseline_sources
        if not _digest(sources.expected_baseline_projection_sha256):
            raise ValueError("Ancestry baseline projection anchor is invalid")
        self.seal(original.context_directory, bound=512 * 1024 * 1024)
        self.seal(original.native_archive_directory, bound=512 * 1024 * 1024)
        self.seal(sources.baseline_projection_directory)
        self.seal(original.evidence.directory)
        for root in [
            *original.capture_sources.values(),
            *original.source_facets.values(),
        ]:
            self.seal(root)
        self.epoch(
            sources.expected_current_context_sha256,
            sources.expected_current_native_archive_sha256,
        )
        recorded_epoch = self.epoch(
            original.expected_context_sha256, original.expected_native_archive_sha256
        )
        self.history = dict(recorded_epoch["roles"])
        duties = strongest_roles(*(epoch["roles"] for epoch in self.epochs.values()))
        recorded = baseline_publication._readback(
            sources.baseline_projection_directory,
            sources.expected_baseline_projection_sha256,
        )
        direct: dict[str, set[int]] = {}
        for proof, _ in iter_neotoma_linked_evidence_occurrences(
            original.evidence.directory,
            expected_manifest_sha256=original.evidence.manifest_sha256,
        ):
            direct.setdefault(
                f"{proof['target_kind']}-{proof['native_id']}", set()
            ).add(proof["root_dataset_id"])
        results = {}
        for pin, root in sorted(original.capture_sources.items()):
            manifest, _, _, _, _ = _control(root, pin)
            for entry in manifest["resources"]:
                key = entry["target_key"]
                if key in results or key not in direct:
                    raise ValueError(
                        "Ancestry baseline result identity is foreign or duplicated"
                    )
                target = entry["identity"]
                role = entity_role(target, direct[key], duties, self.epochs.values())
                if entry["attempts"] and role not in DEVELOPMENT_ROLES:
                    raise ValueError(
                        "Ancestry protected current baseline duties forbid body access"
                    )
                results[key] = {
                    "source_capture_manifest_sha256": pin,
                    "source_terminal_status": entry["terminal_status"],
                    "qualification_status": "retained_direct_result",
                    "recorded_hop": 0 if target["kind"] == "taxon" else None,
                    "attempted": bool(entry["attempts"]),
                }
        state = {
            "seed_ids": recorded["authority"]["declared_seed_taxon_ids"],
            "edges": {row["edge_id"]: row for row in recorded["edges"]},
            "direct_roots": direct,
            "results": results,
            "baseline_sha256": sources.expected_baseline_projection_sha256,
            "evidence_sha256": original.evidence.manifest_sha256,
            "new_request_count": 0,
        }
        # Inherited restrictions travel through the complete pinned graph before replay.
        first = project(state, duties, limits)
        if any(
            row["current_use_role"] not in DEVELOPMENT_ROLES
            and row["source_result"] is not None
            and row["source_result"]["source_terminal_status"]
            == "received_complete_unqualified_linked_resource"
            for row in first["nodes"].values()
        ):
            raise ValueError(
                "Ancestry protected incoming root forbids baseline body access"
            )
        if native_replay:
            verified = baseline_publication.load_neotoma_taxon_ancestry(
                sources.baseline_projection_directory,
                expected_manifest_sha256=sources.expected_baseline_projection_sha256,
                sources=original,
            )
            if recorded != verified:
                raise ValueError("Ancestry baseline changed during source replay")
        return state, project(
            state, recorded_epoch["roles"], baseline_limits(recorded["limits"])
        )

    def captures(
        self,
        state: dict[str, Any],
        parent: str | None,
        pins: tuple[str, ...],
        limits: NeotomaTaxonAncestryChainLimits,
    ) -> None:
        """Apply only closed, witnessed actual native captures from the parent frontier."""
        check_group(self, state, parent, pins, limits)
        current = self.epoch(
            self.sources.expected_current_context_sha256,
            self.sources.expected_current_native_archive_sha256,
        )
        allowed = {
            row["target_key"]
            for row in project(state, current["roles"], limits)["frontier"]
        }
        for pin in pins:
            if (
                pin in self.capture_pins
                or pin not in self.sources.ancestry_capture_sources
            ):
                raise ValueError("Ancestry capture source is missing or reused")
            self.capture_pins.add(pin)
            self.capture(state, parent, pin, limits, allowed)

    def preflight(
        self,
        pins: tuple[str, ...],
        parent: str | None,
        limits: NeotomaTaxonAncestryChainLimits,
    ) -> None:
        """Resolve every capture control and epoch before baseline native replay."""
        preflight_sources(self, pins, parent, limits)

    def capture(
        self,
        state: dict[str, Any],
        parent: str | None,
        pin: str,
        limits: NeotomaTaxonAncestryChainLimits,
        allowed: set[str],
    ) -> None:
        """Validate wire ownership before decoding any new native entity buffer."""
        root = self.sources.ancestry_capture_sources[pin]
        check_capture(self, state, parent, pin, limits, allowed)
        manifest, plan = self.controls[pin, parent]
        epoch = self.epoch(
            plan["current_context_manifest_sha256"],
            plan["current_native_archive_manifest_sha256"],
        )
        entries, _ = capture_population(manifest, plan)
        requests = response_bytes = 0
        for entry in entries:
            result, count = self.entity(root, pin, entry)
            requests += bool(entry["attempts"])
            response_bytes += count
            state["results"][entry["target_key"]] = result
            for edge in result.pop("_edges", []):
                if edge["edge_id"] in state["edges"]:
                    raise ValueError("Ancestry literal edge is duplicated")
                state["edges"][edge["edge_id"]] = edge
        if (
            type(manifest["request_count"]) is not int
            or type(manifest["response_bytes"]) is not int
            or manifest["request_count"] != requests
            or manifest["response_bytes"] != response_bytes
        ):
            raise ValueError("Ancestry actual request/body accounting differs")
        self.history = strongest_roles(self.history, epoch["roles"])
        state["new_request_count"] += requests
        if state["new_request_count"] > limits.max_new_requests:
            raise ValueError("Ancestry cumulative request bound exceeded")

    def entity(
        self, root: Path, pin: str, entry: dict[str, Any]
    ) -> tuple[dict[str, Any], int]:
        """Qualify the same receipt-authenticated immutable body buffer once."""
        result = {
            "source_capture_manifest_sha256": pin,
            "source_terminal_status": entry["terminal_status"],
            "qualification_status": "unavailable_source_result",
            "recorded_hop": entry["recorded_hop"],
            "attempted": bool(entry["attempts"]),
        }
        if not entry["attempts"]:
            if (
                entry["terminal_status"] != "not_attempted_protected_scope"
                or entry["recorded_role"] in DEVELOPMENT_ROLES
            ):
                raise ValueError(
                    "Ancestry closed capture contains an untouched eligible slot"
                )
            return result, 0
        identity = {
            "target_key": entry["target_key"],
            "kind": entry["kind"],
            "native_id": entry["native_id"],
            "exposure_role": entry["recorded_role"],
        }
        request = request_for(identity, 1)
        attempt = entry["attempts"][0]
        raw = self.read(root, attempt["receipt_file"], 1024 * 1024)
        if sha256(raw).hexdigest() != attempt["receipt_sha256"]:
            raise ValueError("Ancestry exact source receipt differs")
        receipt = _object(raw)
        if "body_file" not in attempt:
            _validate_transport_failure(receipt, request)
            if entry["terminal_status"] != "unavailable_transport":
                raise ValueError("Ancestry transport terminal status differs")
            return result, 0
        body = self.read(root, attempt["body_file"], MAX_ENTITY_BYTES + 1)
        assessed = assess_http(receipt, request, body, MAX_ENTITY_BYTES)
        if assessed["terminal_status"] != entry["terminal_status"]:
            raise ValueError("Ancestry source HTTP status differs")
        source = {
            "body_file": attempt["body_file"],
            "body_sha256": sha256(body).hexdigest(),
            "receipt_file": attempt["receipt_file"],
            "receipt_sha256": attempt["receipt_sha256"],
            "utc_start": receipt["utc_start"],
            "utc_end": receipt["utc_end"],
        }
        result["source"] = source
        if entry["terminal_status"] != "received_complete_unqualified_linked_resource":
            return result, len(body)
        try:
            parsed = parse_neotoma_linked_source(
                identity, body, expected_body_sha256=source["body_sha256"]
            )
        except _UnavailableLinkedSource:
            result["qualification_status"] = "successful_empty_not_absence"
        except ValueError:
            result["qualification_status"] = "refused_source_profile"
        else:
            result["qualification_status"] = "qualified_native_detail"
            result["_edges"] = native_edges(parsed.payload["data"], entry, pin, source)
        return result, len(body)

    def resolve(
        self,
        parent: str | None,
        limits: NeotomaTaxonAncestryChainLimits,
        *,
        native_replay: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Replay the finite parent chain in order, with exact declared resolvers."""
        limits.validate()
        layers: list[tuple[str, dict[str, Any]]] = []
        seen: set[str] = set()
        cursor = parent
        while cursor is not None:
            if (
                not _digest(cursor)
                or cursor in seen
                or cursor not in self.sources.chain_sources
                or len(seen) >= 10000
            ):
                raise ValueError("Ancestry parent chain closure is unknown or cyclic")
            seen.add(cursor)
            root = self.sources.chain_sources[cursor]
            self.seal(root)
            document = storage._readback(
                root, cursor, collections=COLLECTIONS, schema=SCHEMA
            )
            self.epoch(
                document["current_context_manifest_sha256"],
                document["current_native_archive_manifest_sha256"],
            )
            self.preflight(
                tuple(document["new_capture_manifest_sha256s"]),
                document.get("parent_chain_manifest_sha256"),
                limits,
            )
            layers.append((cursor, document))
            cursor = document.get("parent_chain_manifest_sha256")
        state, projected = self.baseline(limits, native_replay=native_replay)
        self.capture_pins.clear()
        projected["results"] = dict(state["results"])
        prior = None
        for pin, document in reversed(layers):
            recorded_limits = NeotomaTaxonAncestryChainLimits(**document["limits"])
            recorded_limits.validate()
            previous = {**projected, "results": dict(state["results"])}
            captures = tuple(document["new_capture_manifest_sha256s"])
            if native_replay:
                self.captures(state, prior, captures, recorded_limits)
            else:
                advance_metadata(self, state, document, prior, recorded_limits)
            epoch = self.epoch(
                document["current_context_manifest_sha256"],
                document["current_native_archive_manifest_sha256"],
            )
            self.history = strongest_roles(self.history, epoch["roles"])
            projected = project(state, self.history, recorded_limits)
            expected = delta(
                state,
                projected,
                previous,
                parent=prior,
                captures=captures,
                context=document["current_context_manifest_sha256"],
                native=document["current_native_archive_manifest_sha256"],
                limits=recorded_limits,
            )
            if document != expected:
                raise ValueError(
                    "Ancestry recorded chain differs from complete source projection"
                )
            projected["results"] = dict(state["results"])
            prior = pin
        return state, projected

    def validate(self) -> None:
        """Recheck every consumed physical source namespace without native rereads."""
        for tree in self.trees.values():
            tree.check()

    def __enter__(self) -> ChainOperation:
        """Enter a fresh source session; never reuse another operation's cache."""
        return self

    def __exit__(self, kind: Any, value: Any, traceback: Any) -> None:
        """Recheck all source namespaces on success and always close descriptors."""
        try:
            if kind is None:
                self.validate()
        finally:
            self.stack.close()
