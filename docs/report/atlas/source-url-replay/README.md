# Shared atlas URL replay

The atlas restores external URL changes through its complete document initialization path. Direct hash navigation and browser Back/Forward preserve the incoming address before the atlas parses its filters, temporal controls, source selection, and drawer tab. Internal controls publish URL state with `replaceState` and remain in the current document.

## Replay boundary

[The URL controller](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/url-state.js) tracks the last address published by the current document. A changed external address requests one reload. While that replay is pending, old map callbacks and drawer actions cannot publish their stale state. Duplicate `popstate` and `hashchange` events reuse the pending replay. The complete incoming URL is retained, including any native or modeled state keys; normal startup validation then applies the keys supported by the current atlas.

The implementation deliberately reloads on external navigation. It uses the same initialization boundary as opening a shared link, including native and modeled controllers, instead of maintaining a second partial parser. Browser controls that change the current selection or presentation do not reload the atlas. Table paging, search text, and other state without URL fields follow normal document initialization on external navigation.

## Retained source browser evidence

[The verification receipt](verification.json) records the producer and verifier identity, original source hashes, every served file hash, and actual browser outcomes. The current production renderer serves the same eight exact retained Neotoma and SEAD source records as the [Nordic source navigation result](../nordic-source/README.md). The producer authenticates the retained Nordic inventory and chunks, preserves complete selected graph/detail record equality, and rechecks every input digest after generation.

At widths 1440 and 390, the browser establishes 16 full-document canonical baselines and verifies:

- 16 direct same-document CDP hash navigations across DK/FI/NO/SE and both sources. All 16 navigation commands have no new-document loader ID; the atlas requests its own guarded reinitialization.
- 28 Back/Forward outcomes with the complete canonical state restored.
- Two internal tab and density control sequences that retain the document identity.
- Two stale drawer writer races: an external hash assignment is immediately followed by an old drawer tab action in the same JavaScript turn. The incoming record, country, and complete baseline state survive.
- Zero runtime errors and no repeated reload during the observed stability checks.

Comparison includes canonical URL, country set, active layer keys, time window, visible source/edge counts, classification posture, source chronology and modeled-context snapshot, focus title/tab, complete rendered chronology text, density, diameter, cross-border control, and panel state. The source classification and relation remain unapproved; zero accepted propagation edges are displayed. The unresolved Swedish SEAD record uses the full time extent, preserving its unavailable chronology reason; narrowed numeric windows continue to exclude unresolved context.

The current selection passed 139 map document and browser semantics tests and 12 atlas browser candidate producer regressions. The browser replay passed with zero runtime errors.

## Reproduction

From the repository root, use an absent destination below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.ci.atlas_browser.nordic_source_candidate \
  --repository . --destination artifacts/atlas-source-url-replay/replay-candidate
node packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source-url-replay.mjs \
  artifacts/atlas-source-url-replay/replay-candidate artifacts/atlas-source-url-replay/replay-browser \
  '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
```

The verification receipt records the current candidate and browser result byte identities; artifact output directories are disposable reproduction products. The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/nordic_source_candidate.py) and [verifier](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/source-url-replay.mjs) use existing local dependencies. Browser profiles are removed after the observed terminal result.

## Scope

This evidence covers URL replay for the retained source candidate and selected shared filter/presentation keys. It does not certify new source acquisition, scientific approval, eligible cross-border edges, native numerical replay, modeled-context frame selection in a populated modeled atlas, full accessibility, performance, provider modes, or deployment. The controller preserves all incoming URL fields; browser evidence for native and modeled scientific consumers remains a separate requirement.
