import { execFileSync, spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { createWriteStream } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { extname, join, normalize, relative, resolve } from 'node:path';

const plan = JSON.parse(await readFile(resolve(process.argv[2]), 'utf8'));
if (plan.schema_version !== 'atlas-browser-verification-plan.v2') throw new Error('unsupported plan schema');
const repositoryRoot = resolve(plan.repository_root);
const artifactRoot = resolve(plan.artifact_root);
const timeoutMs = Number(plan.timeout_seconds) * 1000;
const candidate = plan.candidate;
const scopes = plan.scopes;
const verificationProfile = plan.verification_profile;
if (!['nordic-source-chronology-v1', 'generic-time-aware-atlas-v1'].includes(verificationProfile)) {
  throw new Error('unsupported verification profile');
}
const providerHosts = ['tile.openstreetmap.org', 'tile.opentopomap.org'];
const expectedNordic = Object.freeze({
  sample: { level: 'source_sample_presence', code: null, taxon: null, nodes: 9988, observations: 215903, younger: 21911, older: 22911 },
  TRSH: { level: 'source_ecological_code', code: 'TRSH', taxon: null, nodes: 9978, observations: 114225, younger: 21911, older: 22911 },
  UPHE: { level: 'source_ecological_code', code: 'UPHE', taxon: null, nodes: 9928, observations: 91739, younger: 21911, older: 22911 },
  AQVP: { level: 'source_ecological_code', code: 'AQVP', taxon: null, nodes: 4991, observations: 9666, younger: 18190, older: 19190 },
  secale: { level: 'source_taxon', code: null, taxon: 'source:neotoma:taxon:967', nodes: 469, observations: 469, younger: 3961, older: 4461 },
  cereal: { level: 'source_taxon', code: null, taxon: 'source:neotoma:taxon:3924', nodes: 2, observations: 2, younger: 1651, older: 1751 },
});
const requests = [];
let activeScenario = 'server-startup';

await mkdir(artifactRoot, { recursive: true });
assertCandidate();
const server = createServer(async (request, response) => {
  const requestUrl = new URL(request.url, 'http://127.0.0.1');
  const pathname = decodeURIComponent(requestUrl.pathname);
  const requestedPath = resolve(repositoryRoot, `.${normalize(pathname)}`);
  const receipt = { scenario: activeScenario, path: requestUrl.pathname, status: 0, byte_count: 0 };
  requests.push(receipt);
  if (relative(repositoryRoot, requestedPath).startsWith('..')) {
    receipt.status = 403;
    response.writeHead(403).end('forbidden');
    return;
  }
  try {
    const payload = await readFile(requestedPath);
    receipt.status = 200;
    receipt.byte_count = payload.length;
    response.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': 'no-store',
      'Content-Length': payload.length,
      'Content-Type': {
        '.css': 'text/css; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.js': 'text/javascript; charset=utf-8',
        '.json': 'application/json',
        '.png': 'image/png',
      }[extname(requestedPath)] || 'application/octet-stream',
    });
    response.end(payload);
  } catch {
    receipt.status = 404;
    response.writeHead(404).end('not found');
  }
});
await new Promise((accept, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', accept);
});
const serverPort = server.address().port;

const profileRoot = await mkdtemp(join(artifactRoot, 'brave-profile-'));
const browserLogPath = join(artifactRoot, 'brave-browser.log');
const browserLog = createWriteStream(browserLogPath, { flags: 'wx' });
const browser = spawn(plan.browser_binary, [
  '--headless=new',
  '--disable-gpu',
  '--disable-background-networking',
  '--disable-component-update',
  '--disable-default-apps',
  '--no-default-browser-check',
  '--no-first-run',
  '--remote-allow-origins=*',
  '--remote-debugging-port=0',
  `--user-data-dir=${profileRoot}`,
  'about:blank',
], { stdio: ['ignore', 'pipe', 'pipe'] });
browser.stdout.pipe(browserLog, { end: false });
browser.stderr.pipe(browserLog, { end: false });

const scenarios = [];
const receipts = ['brave-browser.log'];
try {
  const browserWebSocket = await debuggerEndpoint(browser, timeoutMs);
  const debuggerOrigin = new URL(browserWebSocket);
  debuggerOrigin.protocol = 'http:';
  debuggerOrigin.pathname = '';
  debuggerOrigin.search = '';
  debuggerOrigin.hash = '';
  for (const scope of scopes) {
    const scopeResult = verificationProfile === 'nordic-source-chronology-v1'
      ? await verifyNordicSourceChronologyScope(scope, debuggerOrigin.origin)
      : await verifyGenericTimeAwareScope(scope, debuggerOrigin.origin);
    scenarios.push(...scopeResult.scenarios);
    receipts.push(...scopeResult.receipts);
  }
  assertCandidate();
  const assertionRows = scenarios.flatMap((scenario) => Object.entries(scenario.assertions || {}));
  const assertions = Object.fromEntries([...new Set(assertionRows.map(([name]) => name))].map((name) => [
    name,
    assertionRows.filter(([candidateName]) => candidateName === name).every(([, passed]) => passed === true),
  ]));
  const requiredAssertionsByProfile = {
    'nordic-source-chronology-v1': [
      'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
      'default_sample_window', 'default_denominators', 'trsh_exact_state',
      'uphe_exact_state', 'aqvp_exact_state', 'secale_exact_state',
      'cereal_finder_exact_state', 'capture_frames_uncluttered',
      'chronology_buttons_navigate', 'chronology_controls_persistent',
      'chronology_status_action', 'basemap_discoverability', 'help_dialog_accessible',
      'comparison_refusal', 'capture_null_inputs_refused', 'responsive_1440',
      'responsive_1024', 'responsive_768', 'responsive_390',
      'reduced_motion_manual_navigation', 'no_basemap_zero_tile_requests',
      'provider_failure_osm_terrain_none', 'provider_failure_evidence_unchanged',
      'runtime_console_clean', 'source_slider_changes_visibility', 'receipt_inventory_complete',
    ],
    'generic-time-aware-atlas-v1': [
      'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
      'default_time_domain_matches_manifest', 'time_controls_persistent', 'time_status_action',
      'time_slider_changes_visibility', 'time_buttons_navigate', 'basemap_discoverability', 'help_dialog_accessible',
      'scientific_posture_matches_manifest', 'capture_invalid_inputs_refused',
      'responsive_1440', 'responsive_1024', 'responsive_768', 'responsive_390',
      'reduced_motion_manual_navigation', 'no_basemap_zero_tile_requests',
      'provider_failure_osm_terrain_none', 'provider_failure_evidence_unchanged',
      'runtime_console_clean', 'receipt_inventory_complete',
    ],
  };
  const required = requiredAssertionsByProfile[verificationProfile];
  if (!required) throw new Error('unsupported verification profile');
  for (const name of required) if (!(name in assertions)) assertions[name] = false;
  const report = {
    schema_version: 'atlas-browser-runtime-report.v2',
    verification_profile: verificationProfile,
    candidate,
    browser: { product: 'Brave Browser', binary: plan.browser_binary },
    assertions: Object.fromEntries(required.map((name) => [name, assertions[name] === true])),
    scenarios,
    receipts: [...new Set(receipts)].sort(),
  };
  await writeFile(join(artifactRoot, 'server-requests.json'), `${JSON.stringify(requests, null, 2)}\n`);
  receipts.push('server-requests.json');
  report.receipts = [...new Set(receipts)].sort();
  await writeFile(join(artifactRoot, 'browser-runtime-report.json'), `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({ assertions: report.assertions, scenario_count: scenarios.length }, null, 2));
  if (Object.values(report.assertions).some((passed) => !passed)) process.exitCode = 1;
} finally {
  browser.kill('SIGTERM');
  await Promise.race([
    new Promise((accept) => browser.once('exit', accept)),
    new Promise((accept) => setTimeout(accept, 4000)),
  ]);
  if (browser.exitCode === null) browser.kill('SIGKILL');
  await new Promise((accept) => server.close(accept));
  browserLog.end();
  await rm(profileRoot, { recursive: true, force: true });
}

async function verifyNordicSourceChronologyScope(scope, debuggerOrigin) {
  const scopeReceipts = [];
  const scopeScenarios = [];
  const normal = await openAtlas(scope, debuggerOrigin, { name: 'normal' });
  const defaultSnapshot = await captureReady(normal.cdp);
  const defaultDom = await pageFacts(normal.cdp);
  const defaultEvidence = evidenceIdentity(defaultSnapshot);
  const responsive = {};
  for (const { width, height } of [
    { width: 1440, height: 900 }, { width: 1024, height: 1000 },
    { width: 768, height: 1000 }, { width: 390, height: 844 },
  ]) {
    await normal.cdp.send('Emulation.setDeviceMetricsOverride', {
      width, height, deviceScaleFactor: 1, mobile: width === 390,
    });
    responsive[width] = await responsiveFacts(normal.cdp, width);
    responsive[width].discoverability = await discoverabilityFacts(normal.cdp, width);
    responsive[width].help_dialog = await helpDialogFacts(normal.cdp, width);
    const path = `${scope.name}/responsive-${width}.png`;
    await screenshot(normal.cdp, path);
    scopeReceipts.push(path);
  }
  await normal.cdp.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const chronologyJourneys = {};
  await shortcutFrame(normal.cdp, 'sample');
  chronologyJourneys.sample = await sliderChronologyJourney(normal.cdp);
  const sourceStates = {};
  for (const code of ['TRSH', 'UPHE', 'AQVP']) {
    sourceStates[code] = await shortcutFrame(normal.cdp, code);
    chronologyJourneys[code] = await sliderChronologyJourney(normal.cdp);
    const path = `${scope.name}/${code.toLowerCase()}.png`;
    await screenshot(normal.cdp, path);
    scopeReceipts.push(path);
  }
  const secale = await exactTaxonFrame(normal.cdp, expectedNordic.secale);
  chronologyJourneys.secale = await sliderChronologyJourney(normal.cdp);
  await screenshot(normal.cdp, `${scope.name}/secale.png`);
  scopeReceipts.push(`${scope.name}/secale.png`);
  const cereal = await cerealFinderFrame(normal.cdp);
  await screenshot(normal.cdp, `${scope.name}/cereal-finder.png`);
  scopeReceipts.push(`${scope.name}/cereal-finder.png`);
  const captureNullRefusals = await captureNullInputs(normal.cdp);
  const signedCaptureView = await captureSignedView(normal.cdp);
  const noBasemap = await applyCurrentFrame(normal.cdp, 'none');
  const normalResult = {
    scope: scope.name,
    name: 'source-and-responsive',
    default_snapshot: defaultSnapshot,
    default_dom: defaultDom,
    source_states: sourceStates,
    secale,
    cereal_finder: cereal,
    chronology_journeys: chronologyJourneys,
    capture_null_refusals: captureNullRefusals,
    signed_capture_view: signedCaptureView,
    no_basemap: noBasemap,
    responsive,
    runtime_failures: normal.runtimeFailures,
    assertions: {
      capture_api_ready: defaultSnapshot.capture_api_version === 'atlas-capture.v1' && defaultSnapshot.ready === true,
      candidate_identity: defaultSnapshot.build_id === candidate.build_id,
      keyless_provider_policy: defaultDom.api_key_sentinel_absent && defaultDom.carto_absent && defaultDom.osm_resource_present,
      default_sample_window: exactSourceState(defaultSnapshot, expectedNordic.sample),
      default_denominators: defaultSnapshot.source_chronology?.facet_node_count === 9988
        && defaultSnapshot.source_chronology?.facet_observation_denominator === 215903,
      trsh_exact_state: exactSourceState(sourceStates.TRSH, expectedNordic.TRSH),
      uphe_exact_state: exactSourceState(sourceStates.UPHE, expectedNordic.UPHE),
      aqvp_exact_state: exactSourceState(sourceStates.AQVP, expectedNordic.AQVP),
      secale_exact_state: exactTaxonState(secale, expectedNordic.secale, /^Secale\b/i),
      cereal_finder_exact_state: exactTaxonState(cereal, expectedNordic.cereal, /Hordeum\/Secale/i)
        && cereal.query_before_capture === 'cereal|secale',
      capture_frames_uncluttered: [sourceStates.TRSH, sourceStates.UPHE, sourceStates.AQVP, secale.snapshot, cereal.snapshot]
        .every((snapshot) => captureFrameIsClear(snapshot, 'observation_chronology')),
      chronology_controls_persistent: [responsive[1440], responsive[390]].every((layout) => layout.chronology_controls_visible
        && layout.chronology_controls_bounded && layout.chronology_controls_uncovered
        && layout.chronology_controls_non_overlapping && layout.body_scroll_width <= layout.viewport.width + 1),
      chronology_status_action: [responsive[1440], responsive[390]].every((layout) => layout.discoverability.chronology_status_visible
        && layout.discoverability.chronology_status_bounded
        && layout.discoverability.chronology_status_uncovered
        && layout.discoverability.chronology_status_has_denominators
        && layout.discoverability.chronology_status_has_bp_interval
        && layout.discoverability.chronology_status_has_active_facet
        && layout.discoverability.chronology_status_visible_values_valid
        && layout.discoverability.chronology_controls_opened
        && layout.discoverability.chronology_controls_focused
        && (layout.viewport.width > 900 || layout.discoverability.chronology_close_restored_focus)),
      basemap_discoverability: [responsive[1440], responsive[1024], responsive[768], responsive[390]].every((layout) => layout.discoverability.basemap_status_visible
        && layout.discoverability.basemap_status_bounded
        && layout.discoverability.basemap_status_uncovered
        && layout.discoverability.basemap_controls_opened
        && layout.discoverability.active_basemap_focused
        && (layout.viewport.width > 900 || layout.discoverability.basemap_close_restored_focus)
        && layout.discoverability.visible_provider_disclosure),
      help_dialog_accessible: [responsive[1440], responsive[390]].every((layout) =>
        helpDialogPasses(layout.help_dialog)),
      source_slider_changes_visibility: Object.values(chronologyJourneys).every((journey) => journey.slider_values_applied
        && journey.visible_counts_within_denominator && journey.distinct_positive_visible_counts >= 2
        && journey.time_readouts_match
        && renderedEvidenceChangesWithCounts(journey.frames, 'visible_source_chronology_point_count')),
      chronology_buttons_navigate: Object.values(chronologyJourneys).every((journey) => journey.newer_moves_toward_present
        && journey.older_restores_window) && chronologyJourneys.sample.playback_started_at_oldest
        && chronologyJourneys.sample.playback_stopped,
      comparison_refusal: defaultSnapshot.scientific_posture.classifications_status === 'unavailable'
        && defaultSnapshot.scientific_posture.classifications_reason_code === 'accepted_scientific_classifications_not_available'
        && defaultSnapshot.scientific_posture.observation_chronology_is_propagation === false
        && defaultSnapshot.visible_governed_candidate_count === 0,
      capture_null_inputs_refused: JSON.stringify(captureNullRefusals.map((row) => row.field))
        === JSON.stringify(['time_start_bp', 'time_end_bp', 'time_start_bp.negative', 'time_end_bp.negative', 'view', 'view.latitude', 'view.longitude', 'view.zoom'])
        && captureNullRefusals.every((row) => row.refused && row.evidence_unchanged),
      signed_capture_view_preserved: signedCaptureViewPreserved(signedCaptureView),
      responsive_1440: desktopLayoutPasses(responsive[1440]),
      responsive_1024: desktopLayoutPasses(responsive[1024]),
      responsive_768: mobileLayoutPasses(responsive[768]),
      responsive_390: mobileLayoutPasses(responsive[390]),
      runtime_console_clean: normal.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(normal, debuggerOrigin);
  await writeScenario(scope, normalResult, scopeReceipts);
  scopeScenarios.push(normalResult);

  const reduced = await openAtlas(scope, debuggerOrigin, { name: 'reduced-motion', reducedMotion: true });
  const reducedDefault = await captureReady(reduced.cdp);
  const reducedManual = await shortcutFrame(reduced.cdp, 'TRSH');
  const reducedPosture = await evaluate(reduced.cdp, `({
    preference_matches: matchMedia('(prefers-reduced-motion: reduce)').matches,
    automatic_playback_disclosure: document.body.innerText.includes('disabled by the reduced-motion preference'),
  })`);
  await screenshot(reduced.cdp, `${scope.name}/reduced-motion-manual.png`);
  scopeReceipts.push(`${scope.name}/reduced-motion-manual.png`);
  const reducedResult = {
    scope: scope.name,
    name: 'reduced-motion',
    before: reducedDefault,
    after_manual_navigation: reducedManual,
    reduced_motion_posture: reducedPosture,
    runtime_failures: reduced.runtimeFailures,
    assertions: {
      reduced_motion_manual_navigation: exactSourceState(reducedManual, expectedNordic.TRSH)
        && reducedPosture.preference_matches
        && reducedManual.time_window_bp.younger_bp < reducedManual.time_window_bp.older_bp,
      runtime_console_clean: reduced.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(reduced, debuggerOrigin);
  await writeScenario(scope, reducedResult, scopeReceipts);
  scopeScenarios.push(reducedResult);

  const withoutBasemap = await openAtlas(scope, debuggerOrigin, { name: 'no-basemap', hash: '#basemap=none' });
  const withoutBasemapSnapshot = await captureReady(withoutBasemap.cdp);
  await screenshot(withoutBasemap.cdp, `${scope.name}/no-basemap.png`);
  scopeReceipts.push(`${scope.name}/no-basemap.png`);
  const withoutBasemapResult = {
    scope: scope.name,
    name: 'no-basemap',
    snapshot: withoutBasemapSnapshot,
    provider_requests: withoutBasemap.providerRequests,
    runtime_failures: withoutBasemap.runtimeFailures,
    assertions: {
      no_basemap_zero_tile_requests: withoutBasemapSnapshot.basemap === 'none' && withoutBasemap.providerRequests.length === 0,
      runtime_console_clean: withoutBasemap.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(withoutBasemap, debuggerOrigin);
  await writeScenario(scope, withoutBasemapResult, scopeReceipts);
  scopeScenarios.push(withoutBasemapResult);

  const failure = await openAtlas(scope, debuggerOrigin, { name: 'provider-failure', blockProviders: true });
  const failureObservation = await waitForProviderRefusal(failure.cdp);
  const failureSnapshot = failureObservation.snapshot;
  const failureDom = await pageFacts(failure.cdp);
  await screenshot(failure.cdp, `${scope.name}/provider-failure.png`);
  scopeReceipts.push(`${scope.name}/provider-failure.png`);
  const failureResult = {
    scope: scope.name,
    name: 'provider-failure',
    snapshot: failureSnapshot,
    dom: failureDom,
    provider_requests: failure.providerRequests,
    refusal_observation: failureObservation,
    runtime_failures: failure.runtimeFailures,
    assertions: {
      provider_failure_osm_terrain_none: !failureObservation.timed_out
        && failureSnapshot?.basemap === 'none'
        && failure.providerRequests.some((row) => row.url.includes('tile.openstreetmap.org'))
        && failure.providerRequests.some((row) => row.url.includes('tile.opentopomap.org'))
        && failure.providerRequests.findIndex((row) => row.url.includes('tile.openstreetmap.org'))
          < failure.providerRequests.findIndex((row) => row.url.includes('tile.opentopomap.org'))
        && /unavailable|no basemap/i.test(failureDom.basemap_readout),
      provider_failure_evidence_unchanged: failureSnapshot !== null
        && JSON.stringify(evidenceIdentity(failureSnapshot)) === JSON.stringify(defaultEvidence),
      runtime_console_clean: failure.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(failure, debuggerOrigin);
  await writeScenario(scope, failureResult, scopeReceipts);
  scopeScenarios.push(failureResult);

  const expectedReceipts = [
    `${scope.name}/source-and-responsive.json`, `${scope.name}/reduced-motion.json`, `${scope.name}/no-basemap.json`,
    `${scope.name}/provider-failure.json`, ...scopeReceipts,
  ];
  const complete = await Promise.all(expectedReceipts.map(async (path) => {
    try { return (await readFile(join(artifactRoot, path))).length > 0; } catch { return false; }
  }));
  scopeScenarios.push({
    scope: scope.name,
    name: 'receipt-inventory',
    expected_receipts: expectedReceipts,
    assertions: { receipt_inventory_complete: complete.every(Boolean) },
  });
  return { scenarios: scopeScenarios, receipts: expectedReceipts };
}

async function verifyGenericTimeAwareScope(scope, debuggerOrigin) {
  const scopeReceipts = [];
  const scopeScenarios = [];
  const manifest = JSON.parse(await readFile(join(repositoryRoot, scope.manifest), 'utf8'));
  const manifestFacts = genericManifestFacts(manifest);
  const normal = await openAtlas(scope, debuggerOrigin, { name: 'normal' });
  const defaultSnapshot = await captureReady(normal.cdp);
  const defaultDom = await pageFacts(normal.cdp);
  const defaultEvidence = evidenceIdentity(defaultSnapshot);
  const responsive = {};
  for (const { width, height } of [
    { width: 1440, height: 900 }, { width: 1024, height: 1000 },
    { width: 768, height: 1000 }, { width: 390, height: 844 },
  ]) {
    await normal.cdp.send('Emulation.setDeviceMetricsOverride', {
      width, height, deviceScaleFactor: 1, mobile: width === 390,
    });
    responsive[width] = await responsiveFacts(normal.cdp, width);
    responsive[width].time_discoverability = await genericTimeDiscoverabilityFacts(normal.cdp, width);
    responsive[width].basemap_discoverability = await basemapDiscoverabilityFacts(normal.cdp, width);
    responsive[width].help_dialog = await helpDialogFacts(normal.cdp, width);
    const path = `${scope.name}/responsive-${width}.png`;
    await screenshot(normal.cdp, path);
    scopeReceipts.push(path);
  }
  await normal.cdp.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const timeJourney = await genericTimeJourney(normal.cdp, manifestFacts.point_record_count);
  const invalidCaptureInputs = await captureInvalidCommonInputs(normal.cdp);
  const normalResult = {
    scope: scope.name,
    name: 'generic-time-and-responsive',
    default_snapshot: defaultSnapshot,
    default_dom: defaultDom,
    manifest_facts: manifestFacts,
    time_journey: timeJourney,
    invalid_capture_inputs: invalidCaptureInputs,
    responsive,
    runtime_failures: normal.runtimeFailures,
    assertions: {
      capture_api_ready: defaultSnapshot.capture_api_version === 'atlas-capture.v1' && defaultSnapshot.ready === true,
      candidate_identity: defaultSnapshot.build_id === candidate.build_id && defaultSnapshot.scope_slug === scope.name,
      keyless_provider_policy: defaultDom.api_key_sentinel_absent && defaultDom.carto_absent && defaultDom.osm_resource_present,
      default_time_domain_matches_manifest: defaultSnapshot.time_window_bp?.younger_bp === manifestFacts.time_min_bp
        && defaultSnapshot.time_window_bp?.older_bp === manifestFacts.time_max_bp,
      time_controls_persistent: [responsive[1440], responsive[390]].every((layout) => layout.chronology_controls_visible
        && layout.chronology_controls_bounded && layout.chronology_controls_uncovered
        && layout.chronology_controls_non_overlapping && layout.body_scroll_width <= layout.viewport.width + 1),
      time_status_action: [responsive[1440], responsive[390]].every((layout) => layout.time_discoverability.status_visible
        && layout.time_discoverability.status_bounded && layout.time_discoverability.status_uncovered
        && layout.time_discoverability.status_enabled && layout.time_discoverability.status_controls_time_panel
        && layout.time_discoverability.status_describes_current_bp_window
        && layout.time_discoverability.controls_opened && layout.time_discoverability.interval_preset_focused
        && (layout.viewport.width > 900 || layout.time_discoverability.close_restored_focus)),
      time_slider_changes_visibility: timeJourney.interval_is_1000_years
        && timeJourney.slider_values_applied && timeJourney.visible_counts_within_denominator
        && timeJourney.distinct_visible_counts >= 2 && timeJourney.time_readouts_match
        && renderedEvidenceChangesWithCounts(timeJourney.frames, 'visible_point_count'),
      time_buttons_navigate: timeJourney.newer_moves_toward_present
        && timeJourney.older_restores_window && timeJourney.playback_started_at_oldest
        && timeJourney.playback_stopped,
      basemap_discoverability: [responsive[1440], responsive[1024], responsive[768], responsive[390]].every((layout) => layout.basemap_discoverability.status_visible
        && layout.basemap_discoverability.status_bounded && layout.basemap_discoverability.status_uncovered
        && layout.basemap_discoverability.controls_opened && layout.basemap_discoverability.active_provider_focused
        && (layout.viewport.width > 900 || layout.basemap_discoverability.close_restored_focus)
        && layout.basemap_discoverability.visible_provider_disclosure),
      help_dialog_accessible: [responsive[1440], responsive[390]].every((layout) =>
        helpDialogPasses(layout.help_dialog)),
      scientific_posture_matches_manifest: defaultSnapshot.scientific_posture?.classifications_status === manifestFacts.classifications_status
        && defaultSnapshot.scientific_posture?.classifications_reason_code === manifestFacts.classifications_reason_code
        && defaultSnapshot.scientific_posture?.observation_chronology_is_propagation === false
        && defaultSnapshot.visible_governed_candidate_count === manifestFacts.edge_record_count,
      capture_invalid_inputs_refused: JSON.stringify(invalidCaptureInputs.map((row) => row.field))
        === JSON.stringify(['frame', 'story_kind', 'basemap', 'view', 'view.latitude', 'view.longitude', 'view.zoom'])
        && invalidCaptureInputs.every((row) => row.refused && row.evidence_unchanged),
      responsive_1440: desktopLayoutPasses(responsive[1440]),
      responsive_1024: desktopLayoutPasses(responsive[1024]),
      responsive_768: mobileLayoutPasses(responsive[768]),
      responsive_390: mobileLayoutPasses(responsive[390]),
      runtime_console_clean: normal.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(normal, debuggerOrigin);
  await writeScenario(scope, normalResult, scopeReceipts);
  scopeScenarios.push(normalResult);

  const reduced = await openAtlas(scope, debuggerOrigin, { name: 'reduced-motion', reducedMotion: true });
  await captureReady(reduced.cdp);
  const reducedManual = await genericReducedMotionJourney(reduced.cdp);
  await screenshot(reduced.cdp, `${scope.name}/reduced-motion-manual.png`);
  scopeReceipts.push(`${scope.name}/reduced-motion-manual.png`);
  const reducedResult = {
    scope: scope.name,
    name: 'reduced-motion',
    journey: reducedManual,
    runtime_failures: reduced.runtimeFailures,
    assertions: {
      reduced_motion_manual_navigation: reducedManual.preference_matches
        && reducedManual.automatic_playback_disabled && reducedManual.manual_window_changed,
      runtime_console_clean: reduced.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(reduced, debuggerOrigin);
  await writeScenario(scope, reducedResult, scopeReceipts);
  scopeScenarios.push(reducedResult);

  const withoutBasemap = await openAtlas(scope, debuggerOrigin, { name: 'no-basemap', hash: '#basemap=none' });
  const withoutBasemapSnapshot = await captureReady(withoutBasemap.cdp);
  await screenshot(withoutBasemap.cdp, `${scope.name}/no-basemap.png`);
  scopeReceipts.push(`${scope.name}/no-basemap.png`);
  const withoutBasemapResult = {
    scope: scope.name,
    name: 'no-basemap',
    snapshot: withoutBasemapSnapshot,
    provider_requests: withoutBasemap.providerRequests,
    runtime_failures: withoutBasemap.runtimeFailures,
    assertions: {
      no_basemap_zero_tile_requests: withoutBasemapSnapshot.basemap === 'none' && withoutBasemap.providerRequests.length === 0,
      runtime_console_clean: withoutBasemap.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(withoutBasemap, debuggerOrigin);
  await writeScenario(scope, withoutBasemapResult, scopeReceipts);
  scopeScenarios.push(withoutBasemapResult);

  const failure = await openAtlas(scope, debuggerOrigin, { name: 'provider-failure', blockProviders: true });
  const failureObservation = await waitForProviderRefusal(failure.cdp);
  const failureSnapshot = failureObservation.snapshot;
  const failureDom = await pageFacts(failure.cdp);
  await screenshot(failure.cdp, `${scope.name}/provider-failure.png`);
  scopeReceipts.push(`${scope.name}/provider-failure.png`);
  const failureResult = {
    scope: scope.name,
    name: 'provider-failure',
    snapshot: failureSnapshot,
    dom: failureDom,
    provider_requests: failure.providerRequests,
    refusal_observation: failureObservation,
    runtime_failures: failure.runtimeFailures,
    assertions: {
      provider_failure_osm_terrain_none: !failureObservation.timed_out
        && failureSnapshot?.basemap === 'none'
        && failure.providerRequests.some((row) => row.url.includes('tile.openstreetmap.org'))
        && failure.providerRequests.some((row) => row.url.includes('tile.opentopomap.org'))
        && failure.providerRequests.findIndex((row) => row.url.includes('tile.openstreetmap.org'))
          < failure.providerRequests.findIndex((row) => row.url.includes('tile.opentopomap.org'))
        && /unavailable|no basemap/i.test(failureDom.basemap_readout),
      provider_failure_evidence_unchanged: failureSnapshot !== null
        && JSON.stringify(evidenceIdentity(failureSnapshot)) === JSON.stringify(defaultEvidence),
      runtime_console_clean: failure.runtimeFailures.length === 0,
    },
  };
  await closeAtlas(failure, debuggerOrigin);
  await writeScenario(scope, failureResult, scopeReceipts);
  scopeScenarios.push(failureResult);

  const expectedReceipts = [
    `${scope.name}/generic-time-and-responsive.json`, `${scope.name}/reduced-motion.json`,
    `${scope.name}/no-basemap.json`, `${scope.name}/provider-failure.json`, ...scopeReceipts,
  ];
  const complete = await Promise.all(expectedReceipts.map(async (path) => {
    try { return (await readFile(join(artifactRoot, path))).length > 0; } catch { return false; }
  }));
  scopeScenarios.push({
    scope: scope.name,
    name: 'receipt-inventory',
    expected_receipts: expectedReceipts,
    assertions: { receipt_inventory_complete: complete.every(Boolean) },
  });
  return { scenarios: scopeScenarios, receipts: expectedReceipts };
}

function genericManifestFacts(manifest) {
  const fields = manifest.assets?.fields || [];
  const rows = manifest.assets?.records || [];
  const index = Object.fromEntries(fields.map((field, position) => [field, position]));
  const pointRows = rows.filter((row) => row[index.domain] === 'nodes' && row[index.layer_kind] === 'point');
  const requireCount = (value, label) => {
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new Error(`${label} must be a non-negative safe integer`);
    }
    return value;
  };
  let pointRecordCount = 0;
  const finiteMinimums = [];
  const finiteMaximums = [];
  pointRows.forEach((row, position) => {
    const recordCount = requireCount(row[index.record_count], `point row ${position} record_count`);
    const untimedCount = requireCount(row[index.untimed_record_count], `point row ${position} untimed_record_count`);
    if (untimedCount > recordCount) {
      throw new Error(`point row ${position} untimed_record_count exceeds record_count`);
    }
    pointRecordCount = requireCount(pointRecordCount + recordCount, 'aggregate point record_count');
    const minimum = row[index.time_min_bp];
    const maximum = row[index.time_max_bp];
    if ((minimum === null) !== (maximum === null)) {
      throw new Error(`point row ${position} has asymmetric BP bounds`);
    }
    if ((minimum === null) !== (untimedCount === recordCount)) {
      throw new Error(`point row ${position} BP bounds contradict untimed_record_count`);
    }
    if (minimum === null) return;
    if (!Number.isFinite(minimum) || !Number.isFinite(maximum)
      || minimum < 0 || minimum > Number.MAX_SAFE_INTEGER
      || maximum < 0 || maximum > Number.MAX_SAFE_INTEGER) {
      throw new Error(`point row ${position} BP bounds must be finite safe numbers and be non-negative`);
    }
    if (minimum > maximum) {
      throw new Error(`point row ${position} BP bounds are reversed`);
    }
    finiteMinimums.push(minimum);
    finiteMaximums.push(maximum);
  });
  if (!pointRows.length || !finiteMinimums.length) {
    throw new Error('generic time-aware manifest has no timed point domain');
  }
  return {
    point_record_count: pointRecordCount,
    time_min_bp: Math.min(...finiteMinimums),
    time_max_bp: Math.max(...finiteMaximums),
    classifications_status: manifest.domains?.classifications?.status,
    classifications_reason_code: manifest.domains?.classifications?.reason_code,
    edge_record_count: requireCount(manifest.domains?.edges?.record_count, 'edge record_count'),
  };
}

async function genericTimeJourney(cdp, pointDenominator) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const renderedMapEvidenceSignature = async () => {
      const markerDom = [...document.querySelectorAll([
        '.leaflet-point-pane path',
        '.leaflet-point-pane .leaflet-marker-icon',
        '.leaflet-marker-pane .leaflet-marker-icon',
      ].join(', '))]
        .map((element) => [
          element.tagName.toLowerCase(),
          element.getAttribute('class') || '',
          element.getAttribute('d') || '',
          element.getAttribute('style') || '',
          element.getAttribute('transform') || '',
          (element.textContent || '').trim(),
        ])
        .sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right)));
      const canvasDigests = await Promise.all(
        [...document.querySelectorAll('.leaflet-point-pane canvas')].map(async (canvas) => {
          const context = canvas.getContext('2d', { willReadFrequently: true });
          if (!context) throw new Error('point evidence canvas has no 2d context');
          const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
          const digest = await crypto.subtle.digest('SHA-256', pixels);
          const sha256 = [...new Uint8Array(digest)]
            .map((byte) => byte.toString(16).padStart(2, '0')).join('');
          return { width: canvas.width, height: canvas.height, sha256 };
        }),
      );
      return JSON.stringify({ marker_dom: markerDom, point_canvas_digests: canvasDigests });
    };
    const intervalPreset = [...document.querySelectorAll('[data-time-interval]')]
      .find((button) => button.dataset.timeInterval === '1000');
    if (!intervalPreset) throw new Error('1000-year interval preset is unavailable');
    intervalPreset.click();
    await api.awaitReady();
    const slider = document.getElementById('time-start-slider');
    const older = document.getElementById('time-step-older');
    const newer = document.getElementById('time-step-newer');
    const playback = document.getElementById('time-playback-toggle');
    const minimum = Number(slider.min);
    const maximum = Number(slider.max);
    const requestedStarts = [...new Set([maximum, Math.round((minimum + maximum) / 2), minimum])];
    const frames = [];
    for (const requestedStart of requestedStarts) {
      slider.value = String(requestedStart);
      slider.dispatchEvent(new Event('input', { bubbles: true }));
      const snapshot = await api.awaitReady();
      frames.push({
        requested_start_bp: requestedStart,
        snapshot,
        time_readout: document.getElementById('time-start-value')?.textContent || '',
        rendered_evidence_signature: await renderedMapEvidenceSignature(),
      });
    }
    slider.value = String(maximum);
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    const oldest = await api.awaitReady();
    newer.click();
    const afterNewer = await api.awaitReady();
    older.click();
    const afterOlder = await api.awaitReady();
    let playbackStartedAtOldest = false;
    let playbackStopped = false;
    if (!playback.disabled) {
      playback.click();
      const playbackSnapshot = await api.awaitReady();
      playbackStartedAtOldest = playback.getAttribute('aria-pressed') === 'true'
        && playbackSnapshot.time_window_bp.younger_bp === maximum;
      playback.click();
      playbackStopped = playback.getAttribute('aria-pressed') === 'false';
    }
    const visibleCounts = new Set(frames.map((row) => row.snapshot.visible_point_count));
    return {
      frames,
      interval_is_1000_years: oldest.time_window_bp.older_bp - oldest.time_window_bp.younger_bp === 1000,
      slider_values_applied: frames.every((row) => row.snapshot.time_window_bp.younger_bp === row.requested_start_bp),
      visible_counts_within_denominator: frames.every((row) => Number.isInteger(row.snapshot.visible_point_count)
        && row.snapshot.visible_point_count >= 0 && row.snapshot.visible_point_count <= ${pointDenominator}),
      distinct_visible_counts: visibleCounts.size,
      time_readouts_match: frames.every((row) => row.time_readout.includes(String(row.snapshot.time_window_bp.younger_bp))
        && row.time_readout.includes(String(row.snapshot.time_window_bp.older_bp))),
      newer_moves_toward_present: afterNewer.time_window_bp.younger_bp < oldest.time_window_bp.younger_bp,
      older_restores_window: JSON.stringify(afterOlder.time_window_bp) === JSON.stringify(oldest.time_window_bp),
      playback_started_at_oldest: playbackStartedAtOldest,
      playback_stopped: playbackStopped,
    };
  })()`);
}

async function genericReducedMotionJourney(cdp) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const intervalPreset = [...document.querySelectorAll('[data-time-interval]')]
      .find((button) => button.dataset.timeInterval === '1000');
    intervalPreset.click();
    await api.awaitReady();
    const slider = document.getElementById('time-start-slider');
    const playback = document.getElementById('time-playback-toggle');
    const before = api.snapshot();
    slider.value = slider.max;
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    const after = await api.awaitReady();
    return {
      preference_matches: matchMedia('(prefers-reduced-motion: reduce)').matches,
      automatic_playback_disabled: playback.disabled
        && playback.textContent.includes('Reduced motion · manual only'),
      manual_window_changed: after.time_window_bp.younger_bp > before.time_window_bp.younger_bp,
      before: before.time_window_bp,
      after: after.time_window_bp,
    };
  })()`);
}

async function genericTimeDiscoverabilityFacts(cdp, width) {
  return evaluate(cdp, `(async () => {
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const visible = (element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0
        && box.width > 0 && box.height > 0 && box.right > 0 && box.left < innerWidth
        && box.bottom > 0 && box.top < innerHeight;
    };
    const bounded = (element) => {
      const box = element.getBoundingClientRect();
      return box.left >= -1 && box.right <= innerWidth + 1 && box.top >= -1 && box.bottom <= innerHeight + 1;
    };
    const uncovered = (element) => {
      const box = element.getBoundingClientRect();
      const hit = document.elementFromPoint(box.left + (box.width / 2), box.top + (box.height / 2));
      return hit === element || element.contains(hit);
    };
    const sidebar = document.getElementById('sidebar');
    const close = document.getElementById('mobile-panel-close');
    if (${width} <= 900 && !sidebar.classList.contains('is-collapsed')) {
      close.click();
      await settle();
    }
    const status = document.getElementById('time-stepper-status');
    const controls = document.getElementById('time-controls');
    const preset = controls.querySelector('[data-time-interval="1000"]');
    const snapshot = globalThis.BijuxPollenomicsAtlasCapture.snapshot();
    const statusText = status.textContent || '';
    const statusVisible = visible(status);
    const statusBounded = bounded(status);
    const statusUncovered = uncovered(status);
    status.focus();
    status.click();
    await settle();
    const result = {
      status_visible: statusVisible,
      status_bounded: statusBounded,
      status_uncovered: statusUncovered,
      status_enabled: !status.disabled,
      status_controls_time_panel: status.getAttribute('aria-controls') === 'time-controls',
      status_describes_current_bp_window: statusText.startsWith('Complete atlas chronology · ')
        && statusText.includes('[' + snapshot.time_window_bp.younger_bp + ', ' + snapshot.time_window_bp.older_bp + '] BP'),
      controls_opened: controls.open && !sidebar.classList.contains('is-collapsed'),
      interval_preset_focused: document.activeElement === preset,
      close_restored_focus: null,
    };
    if (${width} <= 900) {
      close.click();
      await settle();
      result.close_restored_focus = document.activeElement === status;
    }
    return result;
  })()`);
}

async function captureInvalidCommonInputs(cdp) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    const base = { story_kind: 'source_chronology', basemap: 'none', countries: state.countries };
    const invalid = [
      ['frame', null],
      ['story_kind', { ...base, story_kind: 'candidate_succession' }],
      ['basemap', { ...base, basemap: 'requires-api-key' }],
      ['view', { ...base, view: null }],
      ['view.latitude', { ...base, view: { latitude: null, longitude: 18, zoom: 5 } }],
      ['view.longitude', { ...base, view: { latitude: 60, longitude: null, zoom: 5 } }],
      ['view.zoom', { ...base, view: { latitude: 60, longitude: 18, zoom: null } }],
    ];
    const evidenceBefore = JSON.stringify(api.snapshot());
    const results = [];
    for (const [field, frame] of invalid) {
      try {
        await api.applyFrame(frame);
        results.push({ field, refused: false, message: '', evidence_unchanged: false });
      } catch (error) {
        results.push({
          field,
          refused: true,
          message: String(error && error.message ? error.message : error),
          evidence_unchanged: JSON.stringify(api.snapshot()) === evidenceBefore,
        });
      }
    }
    return results;
  })()`);
}

async function captureSignedView(cdp) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    const source = state.source_chronology || {};
    const requestedView = { latitude: -33.9, longitude: -70.7, zoom: 4 };
    const frame = {
      story_kind: 'source_chronology', basemap: 'none', countries: state.countries,
      source_level: source.level,
      source_code: source.source_code || undefined,
      source_taxon: source.source_taxon || undefined,
      time_start_bp: state.time_window_bp.younger_bp,
      time_end_bp: state.time_window_bp.older_bp,
      view: requestedView,
    };
    const snapshot = await api.applyFrame(frame);
    return { accepted: true, requested_view: requestedView, view: snapshot.view };
  })()`);
}

async function basemapDiscoverabilityFacts(cdp, width) {
  return evaluate(cdp, `(async () => {
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const visible = (element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0
        && box.width > 0 && box.height > 0 && box.right > 0 && box.left < innerWidth
        && box.bottom > 0 && box.top < innerHeight;
    };
    const bounded = (element) => {
      const box = element.getBoundingClientRect();
      return box.left >= -1 && box.right <= innerWidth + 1 && box.top >= -1 && box.bottom <= innerHeight + 1;
    };
    const uncovered = (element) => {
      const box = element.getBoundingClientRect();
      const hit = document.elementFromPoint(box.left + (box.width / 2), box.top + (box.height / 2));
      return hit === element || element.contains(hit);
    };
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('panel-toggle');
    if (${width} <= 900 && sidebar.classList.contains('is-collapsed')) {
      toggle.click();
      await settle();
    }
    const status = document.getElementById('basemap-readout');
    const controls = document.getElementById('view-controls');
    status.focus();
    status.click();
    await settle();
    const providerButtons = [...document.querySelectorAll('.basemap-button')];
    const activeProvider = providerButtons.find((button) => button.classList.contains('is-active'));
    const controlsOpened = controls.open && visible(controls);
    const activeProviderFocused = document.activeElement === activeProvider;
    const providerDisclosure = providerButtons.map((button) => button.innerText.trim());
    const providerVisibility = [];
    for (const button of providerButtons) {
      button.focus();
      await settle();
      const box = button.getBoundingClientRect();
      const hit = document.elementFromPoint(box.left + (box.width / 2), box.top + (box.height / 2));
      providerVisibility.push({
        provider: button.dataset.basemap,
        focused: document.activeElement === button,
        visible: visible(button),
        bounded: bounded(button),
        uncovered: uncovered(button),
        bounds: { left: box.left, right: box.right, top: box.top, bottom: box.bottom },
        hit: hit ? hit.tagName.toLowerCase() + '#' + hit.id + '.' + [...hit.classList].join('.') : null,
      });
    }
    const visibleProviderDisclosure = providerVisibility.every((row) => row.focused && row.visible && row.bounded && row.uncovered)
      && providerDisclosure.some((text) => text.includes('OpenStreetMap · no key'))
      && providerDisclosure.some((text) => text.includes('OpenTopoMap · no key'))
      && providerDisclosure.some((text) => text.includes('Offline · no tiles'));
    let closeRestoredFocus = null;
    if (${width} <= 900 && !sidebar.classList.contains('is-collapsed')) {
      document.getElementById('mobile-panel-close').click();
      await settle();
      closeRestoredFocus = document.activeElement === status;
    }
    return {
      status_visible: visible(status),
      status_bounded: bounded(status),
      status_uncovered: uncovered(status),
      controls_opened: controlsOpened,
      active_provider_focused: activeProviderFocused,
      close_restored_focus: closeRestoredFocus,
      visible_provider_disclosure: visibleProviderDisclosure,
      provider_visibility: providerVisibility,
    };
  })()`);
}

async function openAtlas(scope, debuggerOrigin, options) {
  activeScenario = `${scope.name}:${options.name}`;
  const response = await fetch(`${debuggerOrigin}/json/new?about:blank`, { method: 'PUT' });
  if (!response.ok) throw new Error(`cannot create browser target: ${response.status}`);
  const target = await response.json();
  const cdp = await connectCdp(target.webSocketDebuggerUrl);
  const runtimeFailures = [];
  const providerRequests = [];
  cdp.onEvent((event) => {
    if (event.method === 'Runtime.exceptionThrown') runtimeFailures.push({ kind: 'exception', detail: event.params.exceptionDetails?.text || '' });
    if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') runtimeFailures.push({
      kind: 'console-error', detail: (event.params.args || []).map((arg) => arg.description || arg.value || '').join(' '),
    });
    if (event.method === 'Network.requestWillBeSent' && providerHosts.some((host) => event.params.request.url.includes(host))) {
      providerRequests.push({ url: event.params.request.url, request_id: event.params.requestId });
    }
    if (event.method === 'Fetch.requestPaused') {
      const url = event.params.request.url;
      providerRequests.push({ url, request_id: event.params.requestId, intercepted: true });
      void cdp.send('Fetch.failRequest', {
        requestId: event.params.requestId,
        errorReason: 'Failed',
      }).catch((error) => runtimeFailures.push({ kind: 'provider-interception', detail: String(error) }));
    }
  });
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  if (options.reducedMotion) await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  if (options.blockProviders) await cdp.send('Fetch.enable', {
    patterns: providerHosts.map((host) => ({ urlPattern: `*${host}/*`, requestStage: 'Request' })),
  });
  const loaded = cdp.waitFor('Page.loadEventFired', timeoutMs);
  const url = `http://127.0.0.1:${serverPort}/${scope.document}${options.hash || ''}`;
  await cdp.send('Page.navigate', { url });
  await loaded;
  return { cdp, target, runtimeFailures, providerRequests };
}

async function closeAtlas(atlas, debuggerOrigin) {
  atlas.cdp.close();
  await fetch(`${debuggerOrigin}/json/close/${atlas.target.id}`);
}

async function captureReady(cdp) {
  return evaluate(cdp, `(() => new Promise((resolve, reject) => {
    const finish = () => {
      const api = globalThis.BijuxPollenomicsAtlasCapture;
      if (!api || api.version !== 'atlas-capture.v1') return false;
      observer.disconnect();
      clearTimeout(timeout);
      resolve(api.awaitReady());
      return true;
    };
    const observer = new MutationObserver(finish);
    const timeout = setTimeout(() => {
      observer.disconnect();
      reject(new Error('atlas capture API readiness timed out'));
    }, ${timeoutMs});
    observer.observe(document.documentElement, { childList: true, subtree: true });
    finish();
  }))()`);
}

async function shortcutFrame(cdp, shortcut) {
  return evaluate(cdp, `(async () => {
    const button = [...document.querySelectorAll('[data-source-shortcut]')].find((row) => row.dataset.sourceShortcut === ${JSON.stringify(shortcut)});
    if (!button) throw new Error('source shortcut unavailable: ${shortcut}');
    button.click();
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    const source = state.source_chronology;
    return api.applyFrame({
      story_kind: 'source_chronology', basemap: 'none', countries: state.countries,
      source_level: source.level, source_code: source.source_code || undefined,
      source_taxon: source.source_taxon || undefined,
      time_start_bp: state.time_window_bp.younger_bp,
      time_end_bp: state.time_window_bp.older_bp,
    });
  })()`);
}

async function exactTaxonFrame(cdp, expected) {
  return evaluate(cdp, `(async () => {
    const button = [...document.querySelectorAll('[data-source-shortcut]')].find((row) => row.dataset.sourceShortcut === 'taxa');
    button.click();
    const select = document.getElementById('source-chronology-taxon');
    const option = await new Promise((resolve, reject) => {
      const findOption = () => [...select.options].find((row) => row.value === ${JSON.stringify(expected.taxon)});
      const finish = () => {
        const match = findOption();
        if (!match) return false;
        observer.disconnect();
        clearTimeout(timeout);
        resolve(match);
        return true;
      };
      const observer = new MutationObserver(finish);
      const timeout = setTimeout(() => {
        observer.disconnect();
        reject(new Error('exact source taxon readiness timed out: ${expected.taxon}'));
      }, ${timeoutMs});
      observer.observe(select, { childList: true });
      finish();
    });
    select.value = option.value;
    select.dispatchEvent(new Event('change', { bubbles: true }));
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    const snapshot = await api.applyFrame({
      story_kind: 'source_chronology', basemap: 'none', countries: state.countries,
      source_level: state.source_chronology.level,
      source_taxon: state.source_chronology.source_taxon,
      time_start_bp: state.time_window_bp.younger_bp,
      time_end_bp: state.time_window_bp.older_bp,
    });
    return { snapshot, selected_label: select.selectedOptions[0]?.textContent || '', selected_value: select.value };
  })()`);
}

async function cerealFinderFrame(cdp) {
  return evaluate(cdp, `(async () => {
    const button = [...document.querySelectorAll('[data-source-shortcut]')].find((row) => row.dataset.sourceShortcut === 'cereals');
    if (!button) throw new Error('cereal finder is unavailable');
    button.click();
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const queryBeforeCapture = document.getElementById('source-chronology-taxon-query')?.value || '';
    const select = document.getElementById('source-chronology-taxon');
    const requested = [...select.options].find((row) => row.value === 'source:neotoma:taxon:3924');
    if (!requested) throw new Error('expected Hordeum/Secale source taxon is unavailable after cereal search');
    select.value = requested.value;
    select.dispatchEvent(new Event('change', { bubbles: true }));
    const selected = api.snapshot();
    const snapshot = await api.applyFrame({
      story_kind: 'source_chronology', basemap: 'none', countries: selected.countries,
      source_level: selected.source_chronology.level,
      source_taxon: selected.source_chronology.source_taxon,
      time_start_bp: selected.time_window_bp.younger_bp,
      time_end_bp: selected.time_window_bp.older_bp,
    });
    return { snapshot, selected_label: select.selectedOptions[0]?.textContent || '', selected_value: select.value, query_before_capture: queryBeforeCapture };
  })()`);
}

async function sliderChronologyJourney(cdp) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const renderedMapEvidenceSignature = async () => {
      const markerDom = [...document.querySelectorAll([
        '.leaflet-point-pane path',
        '.leaflet-point-pane .leaflet-marker-icon',
        '.leaflet-marker-pane .leaflet-marker-icon',
      ].join(', '))]
        .map((element) => [
          element.tagName.toLowerCase(),
          element.getAttribute('class') || '',
          element.getAttribute('d') || '',
          element.getAttribute('style') || '',
          element.getAttribute('transform') || '',
          (element.textContent || '').trim(),
        ])
        .sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right)));
      const canvasDigests = await Promise.all(
        [...document.querySelectorAll('.leaflet-point-pane canvas')].map(async (canvas) => {
          const context = canvas.getContext('2d', { willReadFrequently: true });
          if (!context) throw new Error('point evidence canvas has no 2d context');
          const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
          const digest = await crypto.subtle.digest('SHA-256', pixels);
          const sha256 = [...new Uint8Array(digest)]
            .map((byte) => byte.toString(16).padStart(2, '0')).join('');
          return { width: canvas.width, height: canvas.height, sha256 };
        }),
      );
      return JSON.stringify({ marker_dom: markerDom, point_canvas_digests: canvasDigests });
    };
    const slider = document.getElementById('time-start-slider');
    const older = document.getElementById('time-step-older');
    const newer = document.getElementById('time-step-newer');
    const playback = document.getElementById('time-playback-toggle');
    const minimum = Number(slider.min);
    const maximum = Number(slider.max);
    const requestedStarts = [...new Set([
      maximum,
      Math.round(minimum + ((maximum - minimum) * 0.75)),
      Math.round(minimum + ((maximum - minimum) * 0.5)),
      Math.round(minimum + ((maximum - minimum) * 0.25)),
      minimum,
    ])];
    const frames = [];
    for (const requestedStart of requestedStarts) {
      slider.value = String(requestedStart);
      slider.dispatchEvent(new Event('input', { bubbles: true }));
      const snapshot = await api.awaitReady();
      frames.push({
        requested_start_bp: requestedStart,
        snapshot,
        time_readout: document.getElementById('time-start-value')?.textContent || '',
        rendered_evidence_signature: await renderedMapEvidenceSignature(),
      });
    }
    slider.value = String(maximum);
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    const oldest = await api.awaitReady();
    newer.click();
    const afterNewer = await api.awaitReady();
    older.click();
    const afterOlder = await api.awaitReady();
    let playbackStartedAtOldest = false;
    let playbackStopped = false;
    if (!playback.disabled) {
      playback.click();
      const playbackSnapshot = await api.awaitReady();
      playbackStartedAtOldest = playback.getAttribute('aria-pressed') === 'true'
        && playbackSnapshot.time_window_bp.younger_bp === maximum;
      playback.click();
      playbackStopped = playback.getAttribute('aria-pressed') === 'false';
    }
    const denominator = oldest.source_chronology.facet_node_count;
    const positiveCounts = new Set(frames
      .map((row) => row.snapshot.visible_source_chronology_point_count)
      .filter((count) => count > 0));
    return {
      frames,
      slider_values_applied: frames.every((row) => row.snapshot.time_window_bp.younger_bp === row.requested_start_bp),
      visible_counts_within_denominator: frames.every((row) => Number.isInteger(row.snapshot.visible_source_chronology_point_count)
        && row.snapshot.visible_source_chronology_point_count >= 0
        && row.snapshot.visible_source_chronology_point_count <= denominator),
      distinct_positive_visible_counts: positiveCounts.size,
      time_readouts_match: frames.every((row) => row.time_readout.includes(String(row.snapshot.time_window_bp.younger_bp))
        && row.time_readout.includes(String(row.snapshot.time_window_bp.older_bp))),
      newer_moves_toward_present: afterNewer.time_window_bp.younger_bp < oldest.time_window_bp.younger_bp,
      older_restores_window: JSON.stringify(afterOlder.time_window_bp) === JSON.stringify(oldest.time_window_bp),
      playback_started_at_oldest: playbackStartedAtOldest,
      playback_stopped: playbackStopped,
    };
  })()`);
}

async function captureNullInputs(cdp) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    const valid = {
        story_kind: 'source_chronology', basemap: 'none', countries: state.countries,
        source_level: state.source_chronology.level,
        source_code: state.source_chronology.source_code || undefined,
        source_taxon: state.source_chronology.source_taxon || undefined,
        time_start_bp: state.time_window_bp.younger_bp,
        time_end_bp: state.time_window_bp.older_bp,
    };
    const invalid = [
      ['time_start_bp', { ...valid, time_start_bp: null }],
      ['time_end_bp', { ...valid, time_end_bp: null }],
      ['time_start_bp.negative', { ...valid, time_start_bp: -1 }],
      ['time_end_bp.negative', { ...valid, time_end_bp: -1 }],
      ['view', { ...valid, view: null }],
      ['view.latitude', { ...valid, view: { latitude: null, longitude: 18, zoom: 5 } }],
      ['view.longitude', { ...valid, view: { latitude: 60, longitude: null, zoom: 5 } }],
      ['view.zoom', { ...valid, view: { latitude: 60, longitude: 18, zoom: null } }],
    ];
    const evidenceBefore = JSON.stringify(api.snapshot());
    const results = [];
    for (const [field, frame] of invalid) {
      try {
        await api.applyFrame(frame);
        results.push({ field, refused: false, message: '', evidence_unchanged: false });
      } catch (error) {
        results.push({
          field,
          refused: true,
          message: String(error && error.message ? error.message : error),
          evidence_unchanged: JSON.stringify(api.snapshot()) === evidenceBefore,
        });
      }
    }
    return results;
  })()`);
}

async function responsiveFacts(cdp, width) {
  return evaluate(cdp, `(async () => {
    document.documentElement.classList.add('atlas-probe-motion-mode');
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('panel-toggle');
    const scrim = document.getElementById('mobile-scrim');
    const close = document.getElementById('mobile-panel-close');
    const visible = (element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0 && box.width > 0 && box.height > 0
        && box.right > 0 && box.left < innerWidth && box.bottom > 0 && box.top < innerHeight;
    };
    const uncovered = (element) => {
      const value = element.getBoundingClientRect();
      const hit = document.elementFromPoint(value.left + (value.width / 2), value.top + (value.height / 2));
      return hit === element || element.contains(hit);
    };
    const box = (element) => {
      const value = element.getBoundingClientRect();
      return { left: value.left, right: value.right, top: value.top, bottom: value.bottom, width: value.width, height: value.height };
    };
    const boxesOverlap = (first, second) => first.left < second.right && first.right > second.left
      && first.top < second.bottom && first.bottom > second.top;
    const topbar = document.querySelector('.map-topbar');
    const mapElement = document.getElementById('map');
    const legendBody = document.getElementById('legend-body');
    const legendToggle = document.getElementById('legend-toggle');
    const legendPanel = document.getElementById('floating-legend');
    const topbarSearch = document.getElementById('topbar-search');
    const searchToggle = document.getElementById('search-toggle');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const focusCard = document.getElementById('focus-card');
    const focusClose = document.getElementById('focus-close');
    const fitActive = document.getElementById('fit-active');
    const chronologyElements = {
      chronology: document.querySelector('.topbar-time-stepper'),
      older: document.getElementById('time-step-older'),
      newer: document.getElementById('time-step-newer'),
      status: document.getElementById('time-stepper-status'),
      playback: document.getElementById('time-playback-toggle'),
    };
    if (!sidebar.classList.contains('is-collapsed')) toggle.click();
    if (!legendBody.classList.contains('is-collapsed')) legendToggle.click();
    if (!topbarSearch.hidden) searchToggle.click();
    await settle();
    const sampleMapVisibility = () => {
      const mapBox = mapElement.getBoundingClientRect();
      const samplePoints = [];
      const ratios = Array.from({ length: 9 }, (_value, index) => (index + 1) / 10);
      for (const xRatio of ratios) {
        for (const yRatio of ratios) {
          const hit = document.elementFromPoint(
            mapBox.left + (mapBox.width * xRatio),
            mapBox.top + (mapBox.height * yRatio),
          );
          samplePoints.push(Boolean(hit && mapElement.contains(hit)));
        }
      }
      const mapCenterHit = document.elementFromPoint(
        mapBox.left + (mapBox.width / 2),
        mapBox.top + (mapBox.height / 2),
      );
      return {
        center_uncovered: Boolean(mapCenterHit && mapElement.contains(mapCenterHit)),
        uncovered_sample_count: samplePoints.filter(Boolean).length,
        sample_count: samplePoints.length,
      };
    };
    const sampleVisualDensity = () => {
      const numericStyle = (value) => {
        const numeric = Number.parseFloat(value);
        return Number.isFinite(numeric) ? numeric : null;
      };
      const boundaries = [...document.querySelectorAll('.leaflet-boundary-pane path')].map((path) => {
        const style = getComputedStyle(path);
        return {
          stroke_width_px: numericStyle(style.strokeWidth),
          opacity: numericStyle(style.strokeOpacity),
          fill_opacity: numericStyle(style.fillOpacity),
        };
      });
      const clusters = [...document.querySelectorAll('.leaflet-marker-pane .cluster-pill')].map((pill) => {
        const bounds = pill.getBoundingClientRect();
        const style = getComputedStyle(pill);
        const countText = pill.textContent.trim();
        const borderWidths = [
          style.borderTopWidth,
          style.borderRightWidth,
          style.borderBottomWidth,
          style.borderLeftWidth,
        ].map(numericStyle);
        return {
          width_px: bounds.width,
          height_px: bounds.height,
          diameter_px: Math.max(bounds.width, bounds.height),
          border_width_px: borderWidths.every((value) => value !== null)
            ? Math.max(...borderWidths)
            : null,
          count_text: countText,
          count: /^[1-9]\\d*$/.test(countText) ? Number(countText) : null,
        };
      });
      const mapBounds = mapElement.getBoundingClientRect();
      const mapArea = mapBounds.width * mapBounds.height;
      const clusterArea = clusters.reduce(
        (total, cluster) => total + (Math.PI * cluster.width_px * cluster.height_px / 4),
        0,
      );
      return {
        boundary_count: boundaries.length,
        boundaries,
        cluster_count: clusters.length,
        clusters,
        aggregate_cluster_footprint_ratio: mapArea > 0 ? clusterArea / mapArea : null,
      };
    };
    const clearMap = {
      panel_collapsed: sidebar.classList.contains('is-collapsed'),
      legend_collapsed: legendBody.classList.contains('is-collapsed'),
      search_collapsed: topbarSearch.hidden && searchToggle.getAttribute('aria-expanded') === 'false',
      ...sampleMapVisibility(),
    };
    const visualDensity = sampleVisualDensity();
    legendToggle.focus();
    legendToggle.click();
    await settle();
    const legendPanelBox = box(legendPanel);
    const legendBodyBox = box(legendBody);
    const legendBodyStyle = getComputedStyle(legendBody);
    const legendPanelStyle = getComputedStyle(legendPanel);
    const expandedLegend = {
      expanded: !legendBody.classList.contains('is-collapsed'),
      toggle_expanded: legendToggle.getAttribute('aria-expanded') === 'true',
      toggle_uncovered: uncovered(legendToggle),
      body_visible: visible(legendBody),
      panel_center_uncovered: uncovered(legendPanel),
      panel_bounded: legendPanelBox.left >= -1 && legendPanelBox.right <= innerWidth + 1
        && legendPanelBox.top >= -1 && legendPanelBox.bottom <= innerHeight + 1,
      body_horizontally_contained: legendBodyBox.left >= legendPanelBox.left - 1
        && legendBodyBox.right <= legendPanelBox.right + 1
        && legendBodyBox.width <= legendPanelBox.width + 2,
      body_top_contained: legendBodyBox.top >= legendPanelBox.top - 1
        && legendBodyBox.top <= legendPanelBox.bottom + 1,
      content_accessible: legendBody.scrollHeight <= legendBody.clientHeight + 1
        || ['auto', 'scroll'].includes(legendBodyStyle.overflowY)
        || ['auto', 'scroll'].includes(legendPanelStyle.overflowY),
      topbar_non_overlapping: !boxesOverlap(legendPanelBox, box(topbar)),
      map_visibility: sampleMapVisibility(),
      collapsed_after_journey: false,
    };
    legendToggle.click();
    await settle();
    expandedLegend.collapsed_after_journey = legendBody.classList.contains('is-collapsed')
      && legendToggle.getAttribute('aria-expanded') === 'false';
    searchToggle.focus();
    searchToggle.click();
    await settle();
    searchInput.value = 'a';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    await settle();
    const searchRegionBox = box(topbarSearch);
    const searchInputBox = box(searchInput);
    const searchResultsBox = box(searchResults);
    const searchResultsStyle = getComputedStyle(searchResults);
    const populatedSearch = {
      query: searchInput.value,
      results_visible: visible(searchResults),
      results_bounded: searchResultsBox.left >= -1 && searchResultsBox.right <= innerWidth + 1
        && searchResultsBox.top >= -1 && searchResultsBox.bottom <= innerHeight + 1,
      results_uncovered: uncovered(searchResults),
      result_count: searchResults.querySelectorAll('[data-search-index]').length,
      content_accessible: searchResults.scrollHeight <= searchResults.clientHeight + 1
        || ['auto', 'scroll'].includes(searchResultsStyle.overflowY),
      chronology_controls_uncovered: Object.values(chronologyElements).every(visible)
        && Object.entries(chronologyElements).filter(([name]) => name !== 'chronology')
          .every(([, element]) => uncovered(element)),
      map_visibility: sampleMapVisibility(),
    };
    const searchControl = {
      region_visible: visible(topbarSearch),
      region_bounded: searchRegionBox.left >= -1 && searchRegionBox.right <= innerWidth + 1
        && searchRegionBox.top >= -1 && searchRegionBox.bottom <= innerHeight + 1,
      region_uncovered: uncovered(topbarSearch),
      input_visible: visible(searchInput),
      input_bounded: searchInputBox.left >= -1 && searchInputBox.right <= innerWidth + 1
        && searchInputBox.top >= -1 && searchInputBox.bottom <= innerHeight + 1,
      input_uncovered: uncovered(searchInput),
      input_focused: document.activeElement === searchInput,
      toggle_expanded: searchToggle.getAttribute('aria-expanded') === 'true',
      map_visibility: sampleMapVisibility(),
      populated: populatedSearch,
      escape_hides_region: false,
      escape_collapses_toggle: false,
      escape_restores_focus: false,
    };
    searchInput.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Escape', code: 'Escape', bubbles: true, cancelable: true,
    }));
    await settle();
    searchControl.escape_hides_region = topbarSearch.hidden && !visible(topbarSearch);
    searchControl.escape_collapses_toggle = searchToggle.getAttribute('aria-expanded') === 'false';
    searchControl.escape_restores_focus = document.activeElement === searchToggle;
    let mobile = null;
    let expandedPanel = null;
    if (${width} <= 900) {
      const collapsed = {
        sidebar_collapsed: sidebar.classList.contains('is-collapsed'),
        toggle_visible: visible(toggle),
        scrim_hidden: !scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'true' && !visible(scrim),
        close_display: getComputedStyle(close).display,
      };
      toggle.click();
      await settle();
      const sidebarBox = sidebar.getBoundingClientRect();
      const outsidePanelHit = document.elementFromPoint(innerWidth / 2, Math.max(1, sidebarBox.top - 8));
      const expanded = {
        sidebar_expanded: !sidebar.classList.contains('is-collapsed') && visible(sidebar),
        sidebar_center_uncovered: uncovered(sidebar),
        sidebar_bounded: sidebarBox.left >= -1 && sidebarBox.right <= innerWidth + 1
          && sidebarBox.top >= -1 && sidebarBox.bottom <= innerHeight + 1,
        sidebar_height_px: sidebarBox.height,
        content_accessible: sidebar.scrollHeight <= sidebar.clientHeight + 1
          || ['auto', 'scroll'].includes(getComputedStyle(sidebar).overflowY)
          || ['auto', 'scroll'].includes(getComputedStyle(sidebar.querySelector('.control-panel-body')).overflowY),
        body_open: document.body.classList.contains('has-mobile-panel-open'),
        scrim_visible: scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'false' && visible(scrim),
        close_visible: visible(close),
        close_uncovered: uncovered(close),
        scrim_catches_outside_panel: outsidePanelHit === scrim,
        topbar_non_overlapping: !boxesOverlap(box(sidebar), box(topbar)),
      };
      expandedPanel = expanded;
      close.click();
      await settle();
      const closed = {
        sidebar_collapsed: sidebar.classList.contains('is-collapsed'),
        body_closed: !document.body.classList.contains('has-mobile-panel-open'),
        scrim_hidden: !scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'true' && !visible(scrim),
      };
      mobile = { collapsed, expanded, closed };
    } else if (sidebar.classList.contains('is-collapsed')) {
      toggle.click();
      await settle();
    }
    if (${width} > 900) {
      const sidebarBox = box(sidebar);
      expandedPanel = {
        sidebar_expanded: !sidebar.classList.contains('is-collapsed') && visible(sidebar),
        sidebar_center_uncovered: uncovered(sidebar),
        sidebar_bounded: sidebarBox.left >= -1 && sidebarBox.right <= innerWidth + 1
          && sidebarBox.top >= -1 && sidebarBox.bottom <= innerHeight + 1,
        content_accessible: sidebar.scrollHeight <= sidebar.clientHeight + 1
          || ['auto', 'scroll'].includes(getComputedStyle(sidebar.querySelector('.control-panel-body')).overflowY),
        topbar_non_overlapping: !boxesOverlap(sidebarBox, box(topbar)),
        map_visibility: sampleMapVisibility(),
      };
    }
    const elements = { topbar: box(topbar), sidebar: box(sidebar), map: box(mapElement) };
    const horizontallyBounded = Object.values(elements).every((value) => value.left >= -1 && value.right <= innerWidth + 1);
    const chronologyBoxes = Object.fromEntries(Object.entries(chronologyElements).map(([name, element]) => [name, box(element)]));
    const chronologyControlsVisible = Object.values(chronologyElements).every(visible);
    const chronologyControlsBounded = Object.values(chronologyBoxes).every((value) => value.left >= -1
      && value.right <= innerWidth + 1 && value.top >= -1 && value.bottom <= innerHeight + 1);
    const directChronologyControls = Object.entries(chronologyElements).filter(([name]) => name !== 'chronology');
    const chronologyControlsUncovered = directChronologyControls.every(([, element]) => {
      const value = element.getBoundingClientRect();
      const hit = document.elementFromPoint(value.left + (value.width / 2), value.top + (value.height / 2));
      return hit === element || element.contains(hit);
    });
    const chronologyControlsNonOverlapping = directChronologyControls.every(([, element], index) => {
      const first = element.getBoundingClientRect();
      return directChronologyControls.slice(index + 1).every(([, other]) => {
        const second = other.getBoundingClientRect();
        return first.right <= second.left || second.right <= first.left || first.bottom <= second.top || second.bottom <= first.top;
      });
    });
    let focusedRecord = {
      result_available: false,
      card_visible: false,
      card_center_uncovered: false,
      card_bounded: false,
      content_accessible: false,
      panel_collapsed: false,
      panel_hidden: false,
      legend_collapsed: false,
      search_collapsed: false,
      topbar_non_overlapping: false,
      map_visibility: null,
      closed_after_journey: false,
    };
    if (sidebar.classList.contains('is-collapsed')) {
      toggle.click();
      await settle();
    }
    if (topbarSearch.hidden) {
      searchToggle.click();
      await settle();
    }
    searchInput.value = 'a';
    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
    await settle();
    const focusSearchResult = searchResults.querySelector('[data-search-index]');
    if (focusSearchResult?.isConnected) {
      focusSearchResult.click();
      await settle();
      const focusBox = box(focusCard);
      const focusStyle = getComputedStyle(focusCard);
      focusedRecord = {
        result_available: true,
        card_visible: visible(focusCard),
        card_center_uncovered: uncovered(focusCard),
        card_bounded: focusBox.left >= -1 && focusBox.right <= innerWidth + 1
          && focusBox.top >= -1 && focusBox.bottom <= innerHeight + 1,
        content_accessible: focusCard.scrollHeight <= focusCard.clientHeight + 1
          || ['auto', 'scroll'].includes(focusStyle.overflowY),
        panel_collapsed: sidebar.classList.contains('is-collapsed'),
        panel_hidden: !visible(sidebar),
        legend_collapsed: legendBody.classList.contains('is-collapsed'),
        search_collapsed: topbarSearch.hidden,
        topbar_non_overlapping: !boxesOverlap(focusBox, box(topbar)),
        map_visibility: sampleMapVisibility(),
        closed_after_journey: false,
      };
      focusClose.click();
      await settle();
      focusedRecord.closed_after_journey = focusCard.hidden && !visible(focusCard);
      await new Promise((resolve) => setTimeout(resolve, 300));
      document.querySelector('.leaflet-popup-close-button')?.click();
      fitActive.click();
      await settle();
    } else if (!sidebar.classList.contains('is-collapsed')) {
      toggle.click();
      await settle();
    }
    return {
      viewport: { width: innerWidth, height: innerHeight }, elements, mobile, clear_map: clearMap,
      expanded_legend: expandedLegend,
      search_control: searchControl,
      expanded_panel: expandedPanel,
      focused_record: focusedRecord,
      visual_density: visualDensity,
      chronology: chronologyBoxes,
      chronology_controls_visible: chronologyControlsVisible,
      chronology_controls_bounded: chronologyControlsBounded,
      chronology_controls_uncovered: chronologyControlsUncovered,
      chronology_controls_non_overlapping: chronologyControlsNonOverlapping,
      document_scroll_width: document.documentElement.scrollWidth,
      body_scroll_width: document.body.scrollWidth,
      horizontally_bounded: horizontallyBounded && document.documentElement.scrollWidth <= innerWidth + 1
        && document.body.scrollWidth <= innerWidth + 1,
      desktop_non_overlap: ${width} >= 901 ? elements.topbar.right <= elements.sidebar.left - 1 : null,
    };
  })()`);
}

async function helpDialogFacts(cdp, width) {
  const opened = await evaluate(cdp, `(async () => {
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const visible = (element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0
        && box.width > 0 && box.height > 0 && box.right > 0 && box.left < innerWidth
        && box.bottom > 0 && box.top < innerHeight;
    };
    const bounded = (element) => {
      const box = element.getBoundingClientRect();
      return box.left >= -1 && box.right <= innerWidth + 1 && box.top >= -1 && box.bottom <= innerHeight + 1;
    };
    const uncovered = (element) => {
      const box = element.getBoundingClientRect();
      const hit = document.elementFromPoint(box.left + (box.width / 2), box.top + (box.height / 2));
      return hit === element || element.contains(hit);
    };
    const sidebar = document.getElementById('sidebar');
    const panelToggle = document.getElementById('panel-toggle');
    const viewControls = document.getElementById('view-controls');
    const opener = document.getElementById('help-toggle');
    const dialog = document.getElementById('help-dialog');
    const card = dialog.querySelector('[role="dialog"]');
    const close = document.getElementById('help-close');
    const appShell = document.querySelector('.app-shell');
    if (${width} <= 900 && sidebar.classList.contains('is-collapsed')) {
      panelToggle.click();
      await settle();
    }
    viewControls.open = true;
    opener.scrollIntoView({ block: 'nearest', behavior: 'auto' });
    opener.focus();
    await settle();
    const openerVisible = visible(opener);
    const openerUncovered = uncovered(opener);
    opener.click();
    await settle();
    return {
      opener_visible: openerVisible,
      opener_uncovered: openerUncovered,
      visible: visible(dialog),
      card_bounded: bounded(card),
      close_uncovered: uncovered(close),
      close_focused: document.activeElement === close,
      background_inert: appShell.inert === true,
      modal_semantics: card.getAttribute('aria-modal') === 'true' && card.getAttribute('aria-labelledby') === 'help-title',
      opener_semantics: opener.getAttribute('aria-controls') === 'help-dialog' && opener.getAttribute('aria-expanded') === 'true',
    };
  })()`);
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab', modifiers: 8 });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', modifiers: 8 });
  const reverseWrapsToLast = await evaluate(cdp, `document.activeElement?.id === 'help-return'`);
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab' });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab' });
  const forwardWrapsToFirst = await evaluate(cdp, `document.activeElement?.id === 'help-close'`);
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape' });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape' });
  const closed = await evaluate(cdp, `(async () => {
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const sidebar = document.getElementById('sidebar');
    const panelClose = document.getElementById('mobile-panel-close');
    const opener = document.getElementById('help-toggle');
    const dialog = document.getElementById('help-dialog');
    const appShell = document.querySelector('.app-shell');
    await settle();
    const result = {
      hidden: dialog.hidden,
      background_interactive: appShell.inert === false,
      opener_collapsed: opener.getAttribute('aria-expanded') === 'false',
      focus_restored: document.activeElement === opener,
    };
    if (${width} <= 900 && !sidebar.classList.contains('is-collapsed')) {
      panelClose.click();
      await settle();
    }
    return result;
  })()`);
  return { ...opened, reverse_wraps_to_last: reverseWrapsToLast, forward_wraps_to_first: forwardWrapsToFirst, closed };
}

async function discoverabilityFacts(cdp, width) {
  return evaluate(cdp, `(async () => {
    const settle = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const visible = (element) => {
      const style = getComputedStyle(element);
      const box = element.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) > 0
        && box.width > 0 && box.height > 0 && box.right > 0 && box.left < innerWidth
        && box.bottom > 0 && box.top < innerHeight;
    };
    const bounded = (element) => {
      const box = element.getBoundingClientRect();
      return box.left >= -1 && box.right <= innerWidth + 1 && box.top >= -1 && box.bottom <= innerHeight + 1;
    };
    const uncovered = (element) => {
      const box = element.getBoundingClientRect();
      const hit = document.elementFromPoint(box.left + (box.width / 2), box.top + (box.height / 2));
      return hit === element || element.contains(hit);
    };
    const sidebar = document.getElementById('sidebar');
    const close = document.getElementById('mobile-panel-close');
    const chronologyStatus = document.getElementById('time-stepper-status');
    const sourceControls = document.getElementById('source-chronology-controls');
    const basemapStatus = document.getElementById('basemap-readout');
    const viewControls = document.getElementById('view-controls');
    const basemapSwitch = document.getElementById('basemap-switch');
    const sourceChronologyLevel = document.getElementById('source-chronology-level');
    const sourceChronologyTaxon = document.getElementById('source-chronology-taxon');
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const snapshot = api.snapshot();
    const sourceState = snapshot.source_chronology;
    const selectedTaxonLabel = (sourceChronologyTaxon.selectedOptions[0]?.textContent || '').split(' · source taxon ')[0];
    const facetLabel = sourceState.level === 'source_ecological_code'
      ? 'literal source code ' + sourceState.source_code
      : sourceState.level === 'source_taxon'
        ? 'exact source label ' + selectedTaxonLabel + ' (' + String(sourceState.source_taxon).split(':').at(-1) + ')'
        : 'source sample pollen presence';
    const chronologyStatusText = chronologyStatus.textContent || '';
    const chronologySegments = chronologyStatusText.split(' · ');
    const nodeParts = (chronologySegments[1] || '').replace(' nodes', '').split('/');
    const observationParts = (chronologySegments[2] || '').replace(' observations', '').split('/');
    const visibleNodeCount = nodeParts.length === 2 ? Number(nodeParts[0]) : null;
    const visibleObservationValue = observationParts.length === 2 ? observationParts[0] : null;
    const visibleObservationCount = visibleObservationValue !== null && visibleObservationValue !== 'unavailable'
      ? Number(visibleObservationValue)
      : null;
    const chronologyMatch = chronologySegments.length === 4
      && chronologySegments[0] === facetLabel
      && nodeParts[1] === String(sourceState.facet_node_count)
      && observationParts[1] === String(sourceState.facet_observation_denominator)
      && chronologySegments[3] === '[' + snapshot.time_window_bp.younger_bp + ', ' + snapshot.time_window_bp.older_bp + '] BP';
    const visibleObservationValueValid = chronologyMatch && (
      visibleObservationValue === 'unavailable'
      || (Number.isInteger(visibleObservationCount)
        && visibleObservationCount >= 0
        && visibleObservationCount <= sourceState.facet_observation_denominator)
    );
    sourceControls.open = false;
    viewControls.open = false;
    if (${width} <= 900 && !sidebar.classList.contains('is-collapsed')) {
      close.click();
      await settle();
    }
    const result = {
      chronology_status_visible: visible(chronologyStatus),
      chronology_status_bounded: bounded(chronologyStatus),
      chronology_status_uncovered: uncovered(chronologyStatus),
      chronology_status_has_denominators: chronologyMatch,
      chronology_status_has_bp_interval: chronologyStatusText.includes(
        '[' + snapshot.time_window_bp.younger_bp + ', ' + snapshot.time_window_bp.older_bp + '] BP'
      ),
      chronology_status_has_active_facet: chronologyStatusText.startsWith(facetLabel + ' · '),
      chronology_status_visible_values_valid: Number.isInteger(visibleNodeCount)
        && visibleNodeCount >= 0 && visibleNodeCount <= sourceState.facet_node_count
        && visibleObservationValueValid,
      chronology_controls_opened: false,
      chronology_controls_focused: false,
      chronology_close_restored_focus: null,
      basemap_status_visible: false,
      basemap_status_bounded: false,
      basemap_status_uncovered: false,
      basemap_controls_opened: false,
      active_basemap_focused: false,
      basemap_close_restored_focus: null,
      visible_provider_disclosure: false,
    };
    chronologyStatus.focus();
    chronologyStatus.click();
    await settle();
    result.chronology_controls_opened = sourceControls.open && !sidebar.classList.contains('is-collapsed');
    result.chronology_controls_focused = document.activeElement === sourceChronologyLevel;
    if (${width} <= 900) {
      close.click();
      await settle();
      result.chronology_close_restored_focus = document.activeElement === chronologyStatus;
    }
    result.basemap_status_visible = visible(basemapStatus);
    result.basemap_status_bounded = bounded(basemapStatus);
    result.basemap_status_uncovered = uncovered(basemapStatus);
    viewControls.open = false;
    basemapStatus.focus();
    basemapStatus.click();
    await settle();
    const activeBasemap = basemapSwitch.querySelector('.basemap-button.is-active');
    const providerButtons = [...basemapSwitch.querySelectorAll('.basemap-button')];
    result.basemap_controls_opened = viewControls.open && !sidebar.classList.contains('is-collapsed');
    result.active_basemap_focused = document.activeElement === activeBasemap;
    const providerText = basemapSwitch.innerText;
    result.visible_provider_disclosure = visible(basemapSwitch) && bounded(basemapSwitch) && uncovered(basemapSwitch)
      && providerButtons.length === 3
      && providerButtons.every((button) => visible(button) && bounded(button) && uncovered(button))
      && providerText.includes('OpenStreetMap · no key')
      && providerText.includes('OpenTopoMap · no key') && providerText.includes('Offline · no tiles');
    if (${width} <= 900) {
      close.click();
      await settle();
      result.basemap_close_restored_focus = document.activeElement === basemapStatus;
    }
    return result;
  })()`);
}

async function applyCurrentFrame(cdp, basemap) {
  return evaluate(cdp, `(async () => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const state = api.snapshot();
    return api.applyFrame({
      story_kind: 'source_chronology', basemap: ${JSON.stringify(basemap)}, countries: state.countries,
      source_level: state.source_chronology.level,
      source_code: state.source_chronology.source_code || undefined,
      source_taxon: state.source_chronology.source_taxon || undefined,
      time_start_bp: state.time_window_bp.younger_bp,
      time_end_bp: state.time_window_bp.older_bp,
    });
  })()`);
}

async function waitForProviderRefusal(cdp) {
  return evaluate(cdp, `(() => new Promise((resolve) => {
    const finish = () => {
      const api = globalThis.BijuxPollenomicsAtlasCapture;
      if (!api || typeof api.snapshot !== 'function') return false;
      const state = api.snapshot();
      if (state.basemap !== 'none') return false;
      observer.disconnect();
      clearTimeout(timeout);
      resolve({ snapshot: state, timed_out: false });
      return true;
    };
    const observer = new MutationObserver(finish);
    const timeout = setTimeout(() => {
      observer.disconnect();
      const api = globalThis.BijuxPollenomicsAtlasCapture;
      resolve({
        snapshot: api && typeof api.snapshot === 'function' ? api.snapshot() : null,
        timed_out: true,
        basemap_readout: document.getElementById('basemap-readout')?.textContent || '',
      });
    }, ${timeoutMs});
    observer.observe(document.documentElement, { childList: true, characterData: true, subtree: true });
    finish();
  }))()`);
}

async function pageFacts(cdp) {
  return evaluate(cdp, `(() => {
    const text = document.body.innerText;
    const resources = performance.getEntriesByType('resource').map((row) => row.name);
    return {
      basemap_readout: document.getElementById('basemap-readout')?.textContent || '',
      api_key_sentinel_absent: !/API KEY REQUIRED/i.test(text),
      carto_absent: !resources.some((url) => /cartocdn/i.test(url)) && !/cartocdn/i.test(document.documentElement.innerHTML),
      osm_resource_present: resources.some((url) => /tile\.openstreetmap\.org/i.test(url)) || /tile\.openstreetmap\.org/i.test(document.documentElement.innerHTML),
    };
  })()`);
}

function exactSourceState(snapshot, expected) {
  const source = snapshot?.source_chronology;
  return source?.level === expected.level
    && source.source_code === expected.code
    && source.source_taxon === expected.taxon
    && source.facet_node_count === expected.nodes
    && source.facet_observation_denominator === expected.observations
    && snapshot.time_window_bp.younger_bp === expected.younger
    && snapshot.time_window_bp.older_bp === expected.older;
}

function exactTaxonState(result, expected, labelPattern) {
  return exactSourceState(result?.snapshot, expected)
    && labelPattern.test(result.selected_label || '')
    && result.selected_value === expected.taxon;
}

function webMercatorPixelPoint(view) {
  const worldPixelSpan = 256 * (2 ** view.zoom);
  const latitudeRadians = view.latitude * Math.PI / 180;
  const latitudeSine = Math.sin(latitudeRadians);
  return {
    x: ((view.longitude + 180) / 360) * worldPixelSpan,
    y: (0.5 - Math.log((1 + latitudeSine) / (1 - latitudeSine)) / (4 * Math.PI)) * worldPixelSpan,
  };
}

function signedCaptureViewPreserved(result) {
  const requested = result?.requested_view;
  const observed = result?.view;
  const validView = (view) => view
    && typeof view.latitude === 'number' && Number.isFinite(view.latitude)
    && view.latitude >= -85.0511287798 && view.latitude <= 85.0511287798
    && typeof view.longitude === 'number' && Number.isFinite(view.longitude)
    && view.longitude >= -180 && view.longitude <= 180
    && typeof view.zoom === 'number' && Number.isFinite(view.zoom)
    && view.zoom >= 0 && view.zoom <= 20;
  if (result?.accepted !== true || !validView(requested) || !validView(observed)
    || observed.zoom !== requested.zoom
    || Math.sign(observed.latitude) !== Math.sign(requested.latitude)
    || Math.sign(observed.longitude) !== Math.sign(requested.longitude)) return false;
  const requestedPixel = webMercatorPixelPoint(requested);
  const observedPixel = webMercatorPixelPoint(observed);
  const halfPixelTolerance = 0.5 + 1e-9;
  return Math.abs(observedPixel.x - requestedPixel.x) <= halfPixelTolerance
    && Math.abs(observedPixel.y - requestedPixel.y) <= halfPixelTolerance;
}

function renderedEvidenceChangesWithCounts(frames, countField) {
  if (!Array.isArray(frames) || frames.length < 2 || typeof countField !== 'string' || !countField) return false;
  if (frames.some((frame) => typeof frame?.rendered_evidence_signature !== 'string'
    || frame.rendered_evidence_signature.length === 0
    || !Number.isInteger(frame?.snapshot?.[countField]))) return false;
  return frames.every((frame, index) => frames.slice(index + 1).every((other) => (
    frame.snapshot[countField] === other.snapshot[countField]
      || frame.rendered_evidence_signature !== other.rendered_evidence_signature
  )));
}

function captureColorIsVisible(value) {
  if (typeof value !== 'string') return false;
  const normalized = value.trim().toLowerCase().replace(/\s+/g, '');
  return normalized.length > 0
    && normalized !== 'transparent'
    && !/^#[0-9a-f]{3}0$/.test(normalized)
    && !/^#[0-9a-f]{6}00$/.test(normalized)
    && !/^(?:rgba?|hsla?)\([^)]*(?:,|\/)0(?:\.0+)?%?\)$/.test(normalized)
    && !/^color\([^/]+\/0(?:\.0+)?%?\)$/.test(normalized);
}

function captureKeyIsClear(presentation, evidenceRole) {
  const expected = evidenceRole === 'observation_chronology'
    ? [
        ['source record', 'point'],
        ['records grouped at current zoom', 'cluster-count'],
        ['country boundary', 'line'],
      ]
    : evidenceRole === 'modeled_context'
      ? [
          ['0–20%', 'area'],
          ['>20–40%', 'area'],
          ['>40–60%', 'area'],
          ['>60–80%', 'area'],
          ['>80–100%', 'area'],
          ['no pollen data · N/A, not 0', 'area'],
          ['country boundary', 'line'],
        ]
      : null;
  const items = presentation?.key_items;
  if (!expected || !Array.isArray(items) || items.length !== expected.length) return false;
  if (JSON.stringify(presentation.key_labels) !== JSON.stringify(expected.map(([label]) => label))) return false;
  return items.every((item, index) => item?.label === expected[index][0]
    && item.cue === expected[index][1]
    && captureColorIsVisible(item.stroke)
    && (item.cue === 'line' || captureColorIsVisible(item.fill)));
}

function captureFrameIsClear(snapshot, evidenceRole) {
  const layers = snapshot?.capture_layers;
  const presentation = snapshot?.capture_presentation;
  const layout = snapshot?.capture_layout;
  const permittedKeys = layers
    ? [...new Set([...(layers.orientation_keys || []), layers.evidence_layer_key])].sort()
    : [];
  return Array.isArray(layers?.active_keys)
    && JSON.stringify(layers.active_keys) === JSON.stringify(permittedKeys)
    && layers.evidence_layer_key
    && Array.isArray(layers.orientation_keys)
    && presentation?.schema_version === 'atlas-capture-presentation.v1'
    && presentation.evidence_role === evidenceRole
    && presentation.null_handling === 'null_not_zero'
    && presentation.interpolation_allowed === false
    && presentation.propagation_use_allowed === false
    && typeof presentation.title === 'string' && presentation.title.length > 0
    && captureKeyIsClear(presentation, evidenceRole)
    && /no .*propagation inference/i.test(presentation.caveat || '')
    && layout?.overlay_visible === true
    && layout.overlay_bounded === true
    && layout.overlay_content_bounded === true
    && layout.overlay_content_overflow === false
    && layout.overlay_overlaps_map === false
    && layout.map_bounded === true
    && layout.scroll_x_px === 0
    && layout.scroll_y_px === 0
    && layout.map_width_px >= Math.floor(layout.viewport_width_px * 0.65)
    && snapshot.visible_point_count === snapshot.visible_source_chronology_point_count
    && snapshot.visible_modeled_context_feature_count === 0
    && Number.isInteger(snapshot.visible_polygon_feature_count)
    && snapshot.visible_polygon_feature_count >= snapshot.visible_polygon_layer_count;
}

function visualDensityPasses(facts, maximumClusterFootprintRatio) {
  return Number.isInteger(facts?.boundary_count)
    && facts.boundary_count > 0
    && Array.isArray(facts.boundaries)
    && facts.boundaries.length === facts.boundary_count
    && facts.boundaries.every((boundary) => Number.isFinite(boundary?.stroke_width_px)
      && boundary.stroke_width_px <= 1.4
      && Number.isFinite(boundary.opacity)
      && boundary.opacity <= 0.72
      && Number.isFinite(boundary.fill_opacity)
      && boundary.fill_opacity <= 0.04)
    && Number.isInteger(facts.cluster_count)
    && facts.cluster_count >= 0
    && Array.isArray(facts.clusters)
    && facts.clusters.length === facts.cluster_count
    && facts.clusters.every((cluster) => Number.isFinite(cluster?.diameter_px)
      && cluster.diameter_px >= 32
      && cluster.diameter_px <= 44
      && Number.isFinite(cluster.border_width_px)
      && cluster.border_width_px <= 2
      && Number.isInteger(cluster.count)
      && cluster.count > 0
      && cluster.count_text === String(cluster.count))
    && Number.isFinite(facts.aggregate_cluster_footprint_ratio)
    && facts.aggregate_cluster_footprint_ratio >= 0
    && Number.isFinite(maximumClusterFootprintRatio)
    && facts.aggregate_cluster_footprint_ratio <= maximumClusterFootprintRatio;
}

function mapVisibilityPasses(facts, minimumClearFraction = 0.7) {
  return facts?.center_uncovered === true
    && Number.isInteger(facts.uncovered_sample_count)
    && Number.isInteger(facts.sample_count)
    && facts.sample_count >= 81
    && Number.isFinite(minimumClearFraction)
    && minimumClearFraction >= 0
    && minimumClearFraction <= 1
    && facts.uncovered_sample_count >= Math.ceil(facts.sample_count * minimumClearFraction);
}

function expandedLegendPasses(facts) {
  return facts?.expanded === true
    && facts.toggle_expanded === true
    && facts.toggle_uncovered === true
    && facts.body_visible === true
    && facts.panel_center_uncovered === true
    && facts.panel_bounded === true
    && facts.body_horizontally_contained === true
    && facts.body_top_contained === true
    && facts.content_accessible === true
    && facts.topbar_non_overlapping === true
    && facts.collapsed_after_journey === true
    && mapVisibilityPasses(facts.map_visibility);
}

function populatedSearchPasses(facts) {
  return facts?.query === 'a'
    && facts.results_visible === true
    && facts.results_bounded === true
    && facts.results_uncovered === true
    && Number.isInteger(facts.result_count)
    && facts.result_count > 0
    && facts.content_accessible === true
    && facts.chronology_controls_uncovered === true
    && mapVisibilityPasses(facts.map_visibility);
}

function focusedRecordPasses(facts) {
  return facts?.result_available === true
    && facts.card_visible === true
    && facts.card_center_uncovered === true
    && facts.card_bounded === true
    && facts.content_accessible === true
    && facts.panel_collapsed === true
    && facts.panel_hidden === true
    && facts.legend_collapsed === true
    && facts.search_collapsed === true
    && facts.topbar_non_overlapping === true
    && mapVisibilityPasses(facts.map_visibility)
    && facts.closed_after_journey === true;
}

function desktopLayoutPasses(layout) {
  return layout.viewport.width >= 901
    && layout.horizontally_bounded
    && layout.desktop_non_overlap === true
    && layout.clear_map.panel_collapsed
    && layout.clear_map.legend_collapsed
    && layout.clear_map.search_collapsed
    && mapVisibilityPasses(layout.clear_map, 0.8)
    && visualDensityPasses(layout.visual_density, 0.04)
    && expandedLegendPasses(layout.expanded_legend)
    && searchControlPasses(layout.search_control)
    && layout.expanded_panel?.sidebar_expanded === true
    && layout.expanded_panel.sidebar_center_uncovered === true
    && layout.expanded_panel.sidebar_bounded === true
    && layout.expanded_panel.content_accessible === true
    && layout.expanded_panel.topbar_non_overlapping === true
    && mapVisibilityPasses(layout.expanded_panel.map_visibility)
    && focusedRecordPasses(layout.focused_record)
    && layout.elements.topbar.width > 0
    && layout.elements.sidebar.width > 0;
}

function helpDialogPasses(facts) {
  return facts.opener_visible
    && facts.opener_uncovered
    && facts.visible
    && facts.card_bounded
    && facts.close_uncovered
    && facts.close_focused
    && facts.background_inert
    && facts.modal_semantics
    && facts.opener_semantics
    && facts.reverse_wraps_to_last
    && facts.forward_wraps_to_first
    && facts.closed.hidden
    && facts.closed.background_interactive
    && facts.closed.opener_collapsed
    && facts.closed.focus_restored;
}

function mobileLayoutPasses(layout) {
  return layout.viewport.width <= 900
    && layout.horizontally_bounded
    && layout.clear_map.panel_collapsed
    && layout.clear_map.legend_collapsed
    && layout.clear_map.search_collapsed
    && mapVisibilityPasses(layout.clear_map, 0.8)
    && visualDensityPasses(layout.visual_density, 0.08)
    && expandedLegendPasses(layout.expanded_legend)
    && searchControlPasses(layout.search_control)
    && layout.mobile?.collapsed.sidebar_collapsed
    && layout.mobile.collapsed.toggle_visible
    && layout.mobile.collapsed.scrim_hidden
    && layout.mobile.expanded.sidebar_expanded
    && layout.mobile.expanded.sidebar_center_uncovered
    && layout.mobile.expanded.sidebar_bounded
    && layout.mobile.expanded.sidebar_height_px <= layout.viewport.height * 0.72 + 1
    && layout.mobile.expanded.content_accessible
    && layout.mobile.expanded.body_open
    && layout.mobile.expanded.scrim_visible
    && layout.mobile.expanded.close_visible
    && layout.mobile.expanded.close_uncovered
    && layout.mobile.expanded.scrim_catches_outside_panel
    && layout.mobile.expanded.topbar_non_overlapping
    && layout.mobile.closed.sidebar_collapsed
    && layout.mobile.closed.body_closed
    && layout.mobile.closed.scrim_hidden
    && focusedRecordPasses(layout.focused_record);
}

function searchControlPasses(facts) {
  return facts.region_visible
    && facts.region_bounded
    && facts.region_uncovered
    && facts.input_visible
    && facts.input_bounded
    && facts.input_uncovered
    && facts.input_focused
    && facts.toggle_expanded
    && mapVisibilityPasses(facts.map_visibility)
    && populatedSearchPasses(facts.populated)
    && facts.escape_hides_region
    && facts.escape_collapses_toggle
    && facts.escape_restores_focus;
}

function evidenceIdentity(snapshot) {
  return {
    build_id: snapshot.build_id,
    scope_slug: snapshot.scope_slug,
    version: snapshot.version,
    countries: snapshot.countries,
    time_window_bp: snapshot.time_window_bp,
    source_chronology: snapshot.source_chronology,
    visible_point_count: snapshot.visible_point_count,
    visible_polygon_layer_count: snapshot.visible_polygon_layer_count,
    visible_governed_candidate_count: snapshot.visible_governed_candidate_count,
    scientific_posture: snapshot.scientific_posture,
  };
}

async function screenshot(cdp, relativePath) {
  const result = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  const path = join(artifactRoot, relativePath);
  await mkdir(resolve(path, '..'), { recursive: true });
  await writeFile(path, Buffer.from(result.data, 'base64'));
}

async function writeScenario(scope, scenario, receiptsList) {
  const path = `${scope.name}/${scenario.name}.json`;
  await mkdir(join(artifactRoot, scope.name), { recursive: true });
  await writeFile(join(artifactRoot, path), `${JSON.stringify(scenario, null, 2)}\n`);
  if (!receiptsList.includes(path)) receiptsList.push(path);
}

function assertCandidate() {
  const head = git('rev-parse', 'HEAD');
  const tree = git('rev-parse', 'HEAD^{tree}');
  const atlasCommit = git('log', '-1', '--format=%H', '--', ...scopes.map((scope) => scope.document));
  if (head !== candidate.repository_head || tree !== candidate.repository_tree || atlasCommit !== candidate.atlas_output_commit) {
    throw new Error('candidate identity changed or differs from the plan');
  }
}

function git(...args) {
  return execFileSync('git', args, { cwd: repositoryRoot, encoding: 'utf8' }).trim();
}

function debuggerEndpoint(process, waitMilliseconds) {
  return new Promise((accept, reject) => {
    let buffer = '';
    const timeout = setTimeout(() => reject(new Error('browser did not publish a debugger endpoint')), waitMilliseconds);
    const inspect = (chunk) => {
      buffer += chunk.toString();
      const match = buffer.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (!match) return;
      clearTimeout(timeout);
      process.stdout.off('data', inspect);
      process.stderr.off('data', inspect);
      accept(match[1]);
    };
    process.stdout.on('data', inspect);
    process.stderr.on('data', inspect);
    process.once('exit', (code) => reject(new Error(`browser exited before debugger readiness: ${code}`)));
  });
}

function connectCdp(url) {
  return new Promise((accept, reject) => {
    const socket = new WebSocket(url);
    let nextId = 0;
    const pending = new Map();
    const listeners = new Set();
    const waiters = new Map();
    socket.addEventListener('error', reject, { once: true });
    socket.addEventListener('open', () => {
      socket.addEventListener('message', (message) => {
        const payload = JSON.parse(message.data);
        if (payload.id) {
          const waiter = pending.get(payload.id);
          pending.delete(payload.id);
          if (!waiter) return;
          if (payload.error) waiter.reject(new Error(JSON.stringify(payload.error)));
          else waiter.resolve(payload.result || {});
          return;
        }
        listeners.forEach((listener) => listener(payload));
        const events = waiters.get(payload.method) || [];
        waiters.delete(payload.method);
        events.forEach((waiter) => waiter.resolve(payload.params || {}));
      });
      accept({
        send(method, params = {}) {
          const id = ++nextId;
          socket.send(JSON.stringify({ id, method, params }));
          return new Promise((resolveRequest, rejectRequest) => pending.set(id, { resolve: resolveRequest, reject: rejectRequest }));
        },
        waitFor(method, waitMilliseconds) {
          return new Promise((resolveEvent, rejectEvent) => {
            const timeout = setTimeout(() => rejectEvent(new Error(`${method} timed out`)), waitMilliseconds);
            const resolve = (value) => { clearTimeout(timeout); resolveEvent(value); };
            waiters.set(method, [...(waiters.get(method) || []), { resolve, reject: rejectEvent }]);
          });
        },
        onEvent(listener) { listeners.add(listener); },
        close() { socket.close(); },
      });
    });
  });
}

async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
