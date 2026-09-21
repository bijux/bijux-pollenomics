/** Focused runtime proof for the exact retained RAÄ degraded-context layer. */

export const RAA_RETAINED_CONTEXT_REQUIRED_ASSERTIONS = [
  'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
  'raa_contract_exact', 'raa_static_asset_exact', 'raa_default_enabled',
  'raa_degraded_warning_visible', 'raa_layer_toggle_exact',
  'raa_time_filter_non_effect', 'raa_analysis_refused', 'raa_no_edges',
  'no_basemap_zero_tile_requests', 'provider_failure_osm_terrain_none',
  'provider_failure_evidence_unchanged', 'runtime_console_clean',
  'receipt_inventory_complete',
];

const RAA_KEY = 'raa-archaeology';
const REASONS = ['missing_raw_inventory', 'missing_raw_summary', 'missing_scientific_review'];
const same = (left, right) => JSON.stringify(left) === JSON.stringify(right);

function raaLayer(contract) {
  const rows = Array.isArray(contract.layer_rows)
    ? contract.layer_rows.filter((row) => row?.key === RAA_KEY) : [];
  if (rows.length !== 1) throw new Error('publication contract must contain one RAÄ layer');
  return rows[0];
}

function raaAsset(manifest) {
  const fields = manifest.assets?.fields;
  const records = manifest.assets?.records;
  if (!Array.isArray(fields) || !Array.isArray(records)) throw new Error('static asset table is absent');
  const rows = records.filter((row) => Array.isArray(row) && row.length === fields.length)
    .map((row) => Object.fromEntries(fields.map((field, index) => [field, row[index]])))
    .filter((row) => row.layer_key === RAA_KEY);
  if (rows.length !== 1) throw new Error('static asset table must contain one RAÄ row');
  return rows[0];
}

function exactContract(status, layer) {
  const accounting = status.density_count_accounting;
  const geometry = status.geometry_publication;
  return status.schema_version === 'raa-atlas-input-status.v1'
    && status.status_namespace === 'raa_atlas_input_availability'
    && status.atlas_input_status === 'degraded' && same(status.reason_codes, REASONS)
    && status.evidence_role === 'archaeology_context_only' && status.propagation_eligible === false
    && geometry?.status === 'retained_context' && geometry?.default_map_state === 'enabled_degraded_context'
    && geometry?.default_enabled === true && geometry?.display_role === 'archaeology_context_only'
    && geometry?.retained_density_is_authoritative === false
    && same(geometry?.warning_codes, ['retained_density_metadata_count_mismatch'])
    && accounting?.density_feature_count === 106 && accounting?.density_cell_count_sum === 339412
    && accounting?.metadata_fornlamning_count === 318265 && accounting?.difference === 21147
    && accounting?.reconciled === false && layer.label === 'RAÄ archaeology density'
    && layer.count === 106 && layer.default_enabled === true && layer.applies_time_filter === false
    && layer.contribution_role === 'display_only' && layer.authority_status === 'degraded'
    && same(layer.authority_reason_codes, REASONS)
    && same(layer.display_warning_codes, ['retained_density_metadata_count_mismatch']);
}

function exactAsset(asset) {
  return asset.domain === 'nodes' && asset.layer_index === 19 && asset.layer_kind === 'polygon'
    && asset.sha256 === 'f9c34eccd0ca76ef5fc1e4a1a6b46d6678a9389044cbf3a6ce2d925fd30c353b'
    && asset.payload_sha256 === '9b37afcf73e93465fc255d8f6fd9e33b711b7c8d6dc6026db1af143f5ff577c1'
    && asset.record_count === 106 && same(asset.country_keys, ['Sweden'])
    && same(asset.bounds, [55, 11, 69, 25]) && asset.time_min_bp === null && asset.time_max_bp === null
    && asset.untimed_record_count === 106 && asset.chronology_absent_record_count === 106
    && asset.refused_chronology_record_count === 0 && asset.contextual_chronology_record_count === 0
    && same(asset.scientific_signal_ids, []);
}

function refusedAnalysis(status, layer) {
  return status.propagation_eligible === false && status.review?.accepted === false
    && layer.semantic_role === 'archaeology_context' && layer.contribution_role === 'display_only'
    && layer.candidate_ranking_eligible === false && layer.scientific_classification_eligible === false
    && layer.scientific_selection_enabled === false && layer.propagation_status === 'refused'
    && layer.propagation_reason_code === 'archaeology_context_only' && layer.edge_count === 0;
}

function raaEvidenceIdentity(snapshot, state) {
  return {
    build_id: snapshot?.build_id, scope_slug: snapshot?.scope_slug,
    capture_api_version: snapshot?.capture_api_version,
    active: snapshot?.capture_layers?.active_keys?.includes(RAA_KEY) === true,
    visible_polygon_feature_count: snapshot?.visible_polygon_feature_count,
    visible_governed_candidate_count: snapshot?.visible_governed_candidate_count,
    layer_checked: state?.checked, density_ramp_text: state?.density_ramp_text,
  };
}

async function browserRaaFacts(cdp, evaluate) {
  return evaluate(cdp, `(async () => {
    const responseJson = async (name) => {
      const response = await fetch('./' + name, { cache: 'no-store' });
      if (!response.ok) throw new Error(name + ' fetch failed: ' + response.status);
      return response.json();
    };
    const visible = (element) => {
      if (!element || element.hidden) return false;
      const style = getComputedStyle(element);
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0
        && element.getClientRects().length > 0;
    };
    const legendBody = document.getElementById('legend-body');
    if (legendBody?.classList.contains('is-collapsed')) document.getElementById('legend-toggle')?.click();
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const checkbox = document.querySelector('.layer-checkbox[value="raa-archaeology"]');
    const ramp = document.getElementById('density-ramp');
    const description = document.getElementById('density-ramp-description');
    const legend = document.querySelector('[data-legend-layer="raa-archaeology"]');
    return {
      status: await responseJson('raa_atlas_input_status.json'),
      contract: await responseJson('nordic_map_publication_contract.json'),
      manifest: await responseJson('nordic_map_assets.json'),
      state: {
        checkbox_present: Boolean(checkbox), checked: checkbox?.checked === true,
        // The layer dock is collapsed by default, so innerText is empty even
        // though the same label is present and becomes visible when opened.
        label_text: checkbox?.closest('label')?.textContent?.trim() || '',
        label_aria: checkbox?.getAttribute('aria-label') || '',
        legend_present: Boolean(legend), legend_text: legend?.innerText || '',
        density_ramp_visible: visible(ramp), density_ramp_text: description?.innerText || '',
      },
    };
  })()`);
}

async function toggleRaa(cdp, evaluate, checked) {
  return evaluate(cdp, `(async () => {
    const checkbox = document.querySelector('.layer-checkbox[value="raa-archaeology"]');
    if (!checkbox) throw new Error('RAÄ layer checkbox is absent');
    if (checkbox.checked !== ${checked}) checkbox.click();
    const snapshot = await globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    return {
      snapshot,
      checked: checkbox.checked,
      legend_present: Boolean(document.querySelector('[data-legend-layer="raa-archaeology"]')),
      density_ramp_hidden: document.getElementById('density-ramp')?.hidden,
      density_ramp_text: document.getElementById('density-ramp-description')?.innerText || '',
    };
  })()`);
}

async function narrowTimeWindow(cdp, evaluate) {
  return evaluate(cdp, `(async () => {
    const start = document.getElementById('time-start-slider');
    const interval = document.getElementById('time-interval-slider');
    if (!start || !interval) throw new Error('time controls are absent');
    start.value = '0';
    start.dispatchEvent(new Event('input', { bubbles: true }));
    interval.value = '100';
    interval.dispatchEvent(new Event('input', { bubbles: true }));
    return globalThis.BijuxPollenomicsAtlasCapture.awaitReady();
  })()`);
}

export async function verifyRaaRetainedContextScope(scope, debuggerOrigin, deps) {
  const {
    artifactRoot, candidate, openAtlas, closeAtlas, captureReady, evaluate,
    screenshot, writeScenario, pageFacts, waitForProviderRefusal, readFile, join,
  } = deps;
  const scenarios = [];
  const receipts = [];
  const normal = await openAtlas(scope, debuggerOrigin, { name: 'raa-retained-context' });
  const initial = await captureReady(normal.cdp);
  const dom = await pageFacts(normal.cdp);
  const facts = await browserRaaFacts(normal.cdp, evaluate);
  const layer = raaLayer(facts.contract);
  const asset = raaAsset(facts.manifest);
  const off = await toggleRaa(normal.cdp, evaluate, false);
  await screenshot(normal.cdp, `${scope.name}/raa-layer-off.png`);
  receipts.push(`${scope.name}/raa-layer-off.png`);
  const restored = await toggleRaa(normal.cdp, evaluate, true);
  await screenshot(normal.cdp, `${scope.name}/raa-default-enabled.png`);
  receipts.push(`${scope.name}/raa-default-enabled.png`);
  const narrowed = await narrowTimeWindow(normal.cdp, evaluate);
  const narrowOff = await toggleRaa(normal.cdp, evaluate, false);
  const narrowRestored = await toggleRaa(normal.cdp, evaluate, true);
  await screenshot(normal.cdp, `${scope.name}/raa-narrow-time.png`);
  receipts.push(`${scope.name}/raa-narrow-time.png`);
  const defaultDelta = initial.visible_polygon_feature_count - off.snapshot.visible_polygon_feature_count;
  const narrowDelta = narrowed.visible_polygon_feature_count - narrowOff.snapshot.visible_polygon_feature_count;
  const normalResult = {
    scope: scope.name, name: 'raa-retained-context', initial, dom, facts,
    toggle: { off, restored, default_feature_delta: defaultDelta },
    narrow_time: { active: narrowed, off: narrowOff, restored: narrowRestored, feature_delta: narrowDelta },
    runtime_failures: normal.runtimeFailures,
    assertions: {
      capture_api_ready: initial.capture_api_version === 'atlas-capture.v1' && initial.ready === true,
      candidate_identity: initial.build_id === candidate.build_id && initial.scope_slug === 'nordic',
      keyless_provider_policy: dom.api_key_sentinel_absent && dom.carto_absent && dom.osm_resource_present,
      raa_contract_exact: exactContract(facts.status, layer),
      raa_static_asset_exact: exactAsset(asset),
      raa_default_enabled: initial.capture_layers?.active_keys?.includes(RAA_KEY) === true
        && facts.state.checkbox_present && facts.state.checked && facts.state.label_text.includes('RAÄ archaeology density')
        && facts.state.label_aria === 'Toggle RAÄ archaeology density'
        && restored.checked && restored.snapshot.capture_layers?.active_keys?.includes(RAA_KEY) === true,
      raa_degraded_warning_visible: facts.state.legend_present && facts.state.legend_text.includes('RAÄ archaeology density')
        && facts.state.density_ramp_visible && facts.state.density_ramp_text.includes('339,412')
        && facts.state.density_ramp_text.includes('318,265') && /display only/i.test(facts.state.density_ramp_text)
        && /source authority refused/i.test(facts.state.density_ramp_text),
      raa_layer_toggle_exact: off.checked === false && !off.snapshot.capture_layers?.active_keys?.includes(RAA_KEY)
        && off.legend_present === false && off.density_ramp_hidden === true && defaultDelta === 106
        && restored.checked === true && restored.legend_present === true && restored.density_ramp_hidden === false
        && restored.snapshot.visible_polygon_feature_count === initial.visible_polygon_feature_count,
      raa_time_filter_non_effect: narrowed.time_window_bp?.younger_bp === 0
        && narrowed.time_window_bp?.older_bp === 100 && narrowed.capture_layers?.active_keys?.includes(RAA_KEY) === true
        && narrowDelta === 106 && narrowRestored.snapshot.visible_polygon_feature_count === narrowed.visible_polygon_feature_count,
      raa_analysis_refused: refusedAnalysis(facts.status, layer),
      raa_no_edges: facts.manifest.domains?.edges?.status === 'unavailable'
        && facts.manifest.domains?.edges?.record_count === 0 && initial.visible_governed_candidate_count === 0
        && restored.snapshot.visible_governed_candidate_count === 0 && narrowed.visible_governed_candidate_count === 0,
      runtime_console_clean: normal.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(normal, debuggerOrigin);
  await writeScenario(scope, normalResult, receipts);
  scenarios.push(normalResult);

  const withoutBasemap = await openAtlas(scope, debuggerOrigin, { name: 'raa-no-basemap', hash: '#basemap=none' });
  const noBasemapSnapshot = await captureReady(withoutBasemap.cdp);
  await screenshot(withoutBasemap.cdp, `${scope.name}/raa-no-basemap.png`);
  receipts.push(`${scope.name}/raa-no-basemap.png`);
  const noBasemapResult = {
    scope: scope.name, name: 'raa-no-basemap', snapshot: noBasemapSnapshot,
    provider_requests: withoutBasemap.providerRequests, runtime_failures: withoutBasemap.runtimeFailures,
    assertions: {
      no_basemap_zero_tile_requests: noBasemapSnapshot.basemap === 'none'
        && noBasemapSnapshot.capture_layers?.active_keys?.includes(RAA_KEY) === true
        && withoutBasemap.providerRequests.length === 0,
      runtime_console_clean: withoutBasemap.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(withoutBasemap, debuggerOrigin);
  await writeScenario(scope, noBasemapResult, receipts);
  scenarios.push(noBasemapResult);

  const failure = await openAtlas(scope, debuggerOrigin, { name: 'raa-provider-failure', blockProviders: true });
  const refusal = await waitForProviderRefusal(failure.cdp);
  const failureFacts = await browserRaaFacts(failure.cdp, evaluate);
  const failureDom = await pageFacts(failure.cdp);
  await screenshot(failure.cdp, `${scope.name}/raa-provider-failure.png`);
  receipts.push(`${scope.name}/raa-provider-failure.png`);
  await closeAtlas(failure, debuggerOrigin);
  const failureResult = {
    scope: scope.name, name: 'raa-provider-failure', snapshot: refusal.snapshot,
    dom: failureDom, raa_state: failureFacts.state, provider_requests: failure.providerRequests,
    refusal_observation: refusal, runtime_failures: failure.runtimeFailures,
    assertions: {
      provider_failure_osm_terrain_none: !refusal.timed_out && refusal.snapshot?.basemap === 'none'
        && failure.providerRequests.some((row) => row.url.includes('tile.openstreetmap.org'))
        && failure.providerRequests.some((row) => row.url.includes('tile.opentopomap.org'))
        && /unavailable|no basemap/i.test(failureDom.basemap_readout),
      provider_failure_evidence_unchanged: same(
        raaEvidenceIdentity(refusal.snapshot, failureFacts.state),
        raaEvidenceIdentity(initial, facts.state),
      ),
      runtime_console_clean: failure.runtimeFailures.length === 0,
    },
  };
  await writeScenario(scope, failureResult, receipts);
  scenarios.push(failureResult);

  const expected = [
    `${scope.name}/raa-retained-context.json`, `${scope.name}/raa-no-basemap.json`,
    `${scope.name}/raa-provider-failure.json`, ...receipts,
  ];
  const complete = await Promise.all(expected.map(async (path) => {
    try { return (await readFile(join(artifactRoot, path))).length > 0; } catch { return false; }
  }));
  scenarios.push({
    scope: scope.name, name: 'raa-receipt-inventory', expected_receipts: expected,
    assertions: { receipt_inventory_complete: complete.every(Boolean) },
  });
  return { scenarios, receipts: expected };
}
