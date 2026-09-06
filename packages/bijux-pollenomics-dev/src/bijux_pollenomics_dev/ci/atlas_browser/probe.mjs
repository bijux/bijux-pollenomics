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
      'cereal_finder_exact_state', 'chronology_buttons_navigate', 'chronology_controls_persistent',
      'chronology_status_action', 'basemap_discoverability',
      'comparison_refusal', 'capture_null_inputs_refused', 'responsive_1440',
      'responsive_1024', 'responsive_768', 'responsive_390',
      'reduced_motion_manual_navigation', 'no_basemap_zero_tile_requests',
      'provider_failure_osm_terrain_none', 'provider_failure_evidence_unchanged',
      'runtime_console_clean', 'source_slider_changes_visibility', 'receipt_inventory_complete',
    ],
    'generic-time-aware-atlas-v1': [
      'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
      'default_time_domain_matches_manifest', 'time_controls_persistent', 'time_status_action',
      'time_slider_changes_visibility', 'time_buttons_navigate', 'basemap_discoverability',
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
        && layout.discoverability.chronology_close_restored_focus),
      basemap_discoverability: [responsive[1440], responsive[390]].every((layout) => layout.discoverability.basemap_status_visible
        && layout.discoverability.basemap_status_bounded
        && layout.discoverability.basemap_status_uncovered
        && layout.discoverability.basemap_controls_opened
        && layout.discoverability.active_basemap_focused
        && layout.discoverability.basemap_close_restored_focus
        && layout.discoverability.visible_provider_disclosure),
      source_slider_changes_visibility: Object.values(chronologyJourneys).every((journey) => journey.slider_values_applied
        && journey.visible_counts_within_denominator && journey.distinct_positive_visible_counts >= 2
        && journey.time_readouts_match),
      chronology_buttons_navigate: Object.values(chronologyJourneys).every((journey) => journey.newer_moves_toward_present
        && journey.older_restores_window) && chronologyJourneys.sample.playback_started_at_oldest
        && chronologyJourneys.sample.playback_stopped,
      comparison_refusal: defaultSnapshot.scientific_posture.classifications_status === 'unavailable'
        && defaultSnapshot.scientific_posture.classifications_reason_code === 'accepted_scientific_classifications_not_available'
        && defaultSnapshot.scientific_posture.observation_chronology_is_propagation === false
        && defaultSnapshot.visible_governed_candidate_count === 0,
      capture_null_inputs_refused: captureNullRefusals.every((row) => row.refused && row.evidence_unchanged),
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
        && layout.time_discoverability.controls_opened && layout.time_discoverability.interval_preset_focused
        && layout.time_discoverability.close_restored_focus),
      time_slider_changes_visibility: timeJourney.interval_is_1000_years
        && timeJourney.slider_values_applied && timeJourney.visible_counts_within_denominator
        && timeJourney.distinct_visible_counts >= 2 && timeJourney.time_readouts_match,
      time_buttons_navigate: timeJourney.newer_moves_toward_present
        && timeJourney.older_restores_window && timeJourney.playback_started_at_oldest
        && timeJourney.playback_stopped,
      basemap_discoverability: [responsive[1440], responsive[390]].every((layout) => layout.basemap_discoverability.status_visible
        && layout.basemap_discoverability.status_bounded && layout.basemap_discoverability.status_uncovered
        && layout.basemap_discoverability.controls_opened && layout.basemap_discoverability.active_provider_focused
        && layout.basemap_discoverability.close_restored_focus && layout.basemap_discoverability.visible_provider_disclosure),
      scientific_posture_matches_manifest: defaultSnapshot.scientific_posture?.classifications_status === manifestFacts.classifications_status
        && defaultSnapshot.scientific_posture?.classifications_reason_code === manifestFacts.classifications_reason_code
        && defaultSnapshot.scientific_posture?.observation_chronology_is_propagation === false
        && defaultSnapshot.visible_governed_candidate_count === manifestFacts.edge_record_count,
      capture_invalid_inputs_refused: invalidCaptureInputs.every((row) => row.refused && row.evidence_unchanged),
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
  const finiteMinimums = pointRows.map((row) => row[index.time_min_bp]).filter(Number.isFinite);
  const finiteMaximums = pointRows.map((row) => row[index.time_max_bp]).filter(Number.isFinite);
  if (!pointRows.length || !finiteMinimums.length || !finiteMaximums.length) {
    throw new Error('generic time-aware manifest has no timed point domain');
  }
  const requireCount = (value, label) => {
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new Error(`${label} must be a non-negative safe integer`);
    }
    return value;
  };
  return {
    point_record_count: pointRows.reduce(
      (sum, row, position) => sum + requireCount(row[index.record_count], `point row ${position} record_count`),
      0,
    ),
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
      controls_opened: controls.open && !sidebar.classList.contains('is-collapsed'),
      interval_preset_focused: document.activeElement === preset,
      close_restored_focus: ${width} > 900,
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
    const providerDisclosure = providerButtons.map((button) => button.textContent.trim());
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
    controls.open = false;
    status.focus();
    await settle();
    if (${width} <= 900 && !sidebar.classList.contains('is-collapsed')) {
      document.getElementById('mobile-panel-close').click();
      await settle();
    }
    return {
      status_visible: visible(status),
      status_bounded: bounded(status),
      status_uncovered: uncovered(status),
      controls_opened: controlsOpened,
      active_provider_focused: activeProviderFocused,
      close_restored_focus: document.activeElement === status,
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
    document.documentElement.classList.add('atlas-capture-mode');
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
    const box = (element) => {
      const value = element.getBoundingClientRect();
      return { left: value.left, right: value.right, top: value.top, bottom: value.bottom, width: value.width, height: value.height };
    };
    const topbar = document.querySelector('.map-topbar');
    const chronologyElements = {
      chronology: document.querySelector('.topbar-time-stepper'),
      older: document.getElementById('time-step-older'),
      newer: document.getElementById('time-step-newer'),
      status: document.getElementById('time-stepper-status'),
      playback: document.getElementById('time-playback-toggle'),
    };
    let mobile = null;
    if (${width} <= 900) {
      if (!sidebar.classList.contains('is-collapsed')) toggle.click();
      await settle();
      const collapsed = {
        sidebar_collapsed: sidebar.classList.contains('is-collapsed'),
        toggle_visible: visible(toggle),
        scrim_hidden: !scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'true' && !visible(scrim),
        close_display: getComputedStyle(close).display,
      };
      toggle.click();
      await settle();
      const expanded = {
        sidebar_expanded: !sidebar.classList.contains('is-collapsed') && visible(sidebar),
        body_open: document.body.classList.contains('has-mobile-panel-open'),
        scrim_visible: scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'false' && visible(scrim),
        close_visible: visible(close),
      };
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
    const elements = { topbar: box(topbar), sidebar: box(sidebar), map: box(document.getElementById('map')) };
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
    return {
      viewport: { width: innerWidth, height: innerHeight }, elements, mobile,
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
      chronology_close_restored_focus: ${width} > 900,
      basemap_status_visible: false,
      basemap_status_bounded: false,
      basemap_status_uncovered: false,
      basemap_controls_opened: false,
      active_basemap_focused: false,
      basemap_close_restored_focus: ${width} > 900,
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

function desktopLayoutPasses(layout) {
  return layout.viewport.width >= 901
    && layout.horizontally_bounded
    && layout.desktop_non_overlap === true
    && layout.elements.topbar.width > 0
    && layout.elements.sidebar.width > 0;
}

function mobileLayoutPasses(layout) {
  return layout.viewport.width <= 900
    && layout.horizontally_bounded
    && layout.mobile?.collapsed.sidebar_collapsed
    && layout.mobile.collapsed.toggle_visible
    && layout.mobile.collapsed.scrim_hidden
    && layout.mobile.expanded.sidebar_expanded
    && layout.mobile.expanded.body_open
    && layout.mobile.expanded.scrim_visible
    && layout.mobile.expanded.close_visible
    && layout.mobile.closed.sidebar_collapsed
    && layout.mobile.closed.body_closed
    && layout.mobile.closed.scrim_hidden;
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
