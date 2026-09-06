import { execFileSync, spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { createWriteStream } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { extname, join, normalize, relative, resolve } from 'node:path';

const plan = JSON.parse(await readFile(resolve(process.argv[2]), 'utf8'));
if (plan.schema_version !== 'atlas-browser-verification-plan.v1') throw new Error('unsupported plan schema');
const repositoryRoot = resolve(plan.repository_root);
const artifactRoot = resolve(plan.artifact_root);
const timeoutMs = Number(plan.timeout_seconds) * 1000;
const candidate = plan.candidate;
const scopes = plan.scopes;
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
    const scopeResult = await verifyScope(scope, debuggerOrigin.origin);
    scenarios.push(...scopeResult.scenarios);
    receipts.push(...scopeResult.receipts);
  }
  assertCandidate();
  const assertionRows = scenarios.flatMap((scenario) => Object.entries(scenario.assertions || {}));
  const assertions = Object.fromEntries([...new Set(assertionRows.map(([name]) => name))].map((name) => [
    name,
    assertionRows.filter(([candidateName]) => candidateName === name).every(([, passed]) => passed === true),
  ]));
  const required = [
    'capture_api_ready', 'candidate_identity', 'keyless_provider_policy',
    'default_sample_window', 'default_denominators', 'trsh_exact_state',
    'uphe_exact_state', 'aqvp_exact_state', 'secale_exact_state',
    'cereal_finder_exact_state', 'comparison_refusal', 'responsive_1440',
    'responsive_1024', 'responsive_768', 'responsive_390',
    'reduced_motion_manual_navigation', 'no_basemap_zero_tile_requests',
    'provider_failure_osm_terrain_none', 'provider_failure_evidence_unchanged',
    'runtime_console_clean', 'receipt_inventory_complete',
  ];
  for (const name of required) if (!(name in assertions)) assertions[name] = false;
  const report = {
    schema_version: 'atlas-browser-runtime-report.v1',
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

async function verifyScope(scope, debuggerOrigin) {
  const scopeReceipts = [];
  const scopeScenarios = [];
  const normal = await openAtlas(scope, debuggerOrigin, { name: 'normal' });
  const defaultSnapshot = await captureReady(normal.cdp);
  const defaultDom = await pageFacts(normal.cdp);
  const defaultEvidence = evidenceIdentity(defaultSnapshot);
  const responsive = {};
  for (const width of [1440, 1024, 768, 390]) {
    await normal.cdp.send('Emulation.setDeviceMetricsOverride', {
      width, height: width === 390 ? 844 : 1000, deviceScaleFactor: 1, mobile: width === 390,
    });
    responsive[width] = await responsiveFacts(normal.cdp, width);
    const path = `${scope.name}/responsive-${width}.png`;
    await screenshot(normal.cdp, path);
    scopeReceipts.push(path);
  }
  await normal.cdp.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  const sourceStates = {};
  for (const code of ['TRSH', 'UPHE', 'AQVP']) {
    sourceStates[code] = await shortcutFrame(normal.cdp, code);
    const path = `${scope.name}/${code.toLowerCase()}.png`;
    await screenshot(normal.cdp, path);
    scopeReceipts.push(path);
  }
  const secale = await exactTaxonFrame(normal.cdp, 'Secale');
  await screenshot(normal.cdp, `${scope.name}/secale.png`);
  scopeReceipts.push(`${scope.name}/secale.png`);
  const cereal = await cerealFinderFrame(normal.cdp);
  await screenshot(normal.cdp, `${scope.name}/cereal-finder.png`);
  scopeReceipts.push(`${scope.name}/cereal-finder.png`);
  const noBasemap = await applyCurrentFrame(normal.cdp, 'none');
  const normalResult = {
    scope: scope.name,
    name: 'source-and-responsive',
    default_snapshot: defaultSnapshot,
    default_dom: defaultDom,
    source_states: sourceStates,
    secale,
    cereal_finder: cereal,
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
      comparison_refusal: defaultSnapshot.scientific_posture.classifications_status === 'unavailable'
        && defaultSnapshot.scientific_posture.classifications_reason_code === 'accepted_scientific_classifications_not_available'
        && defaultSnapshot.scientific_posture.observation_chronology_is_propagation === false
        && defaultSnapshot.visible_governed_candidate_count === 0,
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
  const failureSnapshot = await waitForProviderRefusal(failure.cdp);
  const failureDom = await pageFacts(failure.cdp);
  await screenshot(failure.cdp, `${scope.name}/provider-failure.png`);
  scopeReceipts.push(`${scope.name}/provider-failure.png`);
  const failureResult = {
    scope: scope.name,
    name: 'provider-failure',
    snapshot: failureSnapshot,
    dom: failureDom,
    provider_requests: failure.providerRequests,
    runtime_failures: failure.runtimeFailures,
    assertions: {
      provider_failure_osm_terrain_none: failureSnapshot.basemap === 'none'
        && failure.providerRequests.some((row) => row.url.includes('tile.openstreetmap.org'))
        && failure.providerRequests.some((row) => row.url.includes('tile.opentopomap.org'))
        && failure.providerRequests.findIndex((row) => row.url.includes('tile.openstreetmap.org'))
          < failure.providerRequests.findIndex((row) => row.url.includes('tile.opentopomap.org'))
        && /unavailable|no basemap/i.test(failureDom.basemap_readout),
      provider_failure_evidence_unchanged: JSON.stringify(evidenceIdentity(failureSnapshot)) === JSON.stringify(defaultEvidence),
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
  });
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
  if (options.reducedMotion) await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  if (options.blockProviders) await cdp.send('Network.setBlockedURLs', { urls: ['*tile.openstreetmap.org/*', '*tile.opentopomap.org/*'] });
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
  return evaluate(cdp, `(() => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    if (!api || api.version !== 'atlas-capture.v1') throw new Error('atlas capture API unavailable');
    return api.awaitReady();
  })()`);
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

async function exactTaxonFrame(cdp, labelPattern) {
  return evaluate(cdp, `(async () => {
    const button = [...document.querySelectorAll('[data-source-shortcut]')].find((row) => row.dataset.sourceShortcut === 'taxa');
    button.click();
    const select = document.getElementById('source-chronology-taxon');
    const option = [...select.options].find((row) => new RegExp(${JSON.stringify(labelPattern)}, 'i').test(row.textContent));
    if (!option) throw new Error('exact source taxon unavailable: ${labelPattern}');
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
    const state = api.snapshot();
    const queryBeforeCapture = document.getElementById('source-chronology-taxon-query')?.value || '';
    const snapshot = await api.applyFrame({
      story_kind: 'source_chronology', basemap: 'none', countries: state.countries,
      source_level: state.source_chronology.level,
      source_taxon: state.source_chronology.source_taxon,
      time_start_bp: state.time_window_bp.younger_bp,
      time_end_bp: state.time_window_bp.older_bp,
    });
    const select = document.getElementById('source-chronology-taxon');
    return { snapshot, selected_label: select.selectedOptions[0]?.textContent || '', selected_value: select.value, query_before_capture: queryBeforeCapture };
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
    let mobile = null;
    if (${width} <= 900) {
      if (!sidebar.classList.contains('is-collapsed')) toggle.click();
      await settle();
      const collapsed = {
        sidebar_collapsed: sidebar.classList.contains('is-collapsed'),
        toggle_visible: visible(toggle),
        scrim_hidden: !scrim.classList.contains('is-visible') && scrim.getAttribute('aria-hidden') === 'true' && !visible(scrim),
        close_css_available: getComputedStyle(close).display === 'inline-flex',
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
    return {
      viewport: { width: innerWidth, height: innerHeight }, elements, mobile,
      document_scroll_width: document.documentElement.scrollWidth,
      horizontally_bounded: horizontallyBounded && document.documentElement.scrollWidth <= innerWidth + 1,
      desktop_non_overlap: ${width} >= 901 ? elements.topbar.right <= elements.sidebar.left - 1 : null,
    };
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
  return evaluate(cdp, `(() => new Promise((resolve, reject) => {
    const api = globalThis.BijuxPollenomicsAtlasCapture;
    const readout = document.getElementById('basemap-readout');
    const finish = async () => {
      const state = api.snapshot();
      if (state.basemap !== 'none') return false;
      observer.disconnect();
      clearTimeout(timeout);
      resolve(await api.awaitReady());
      return true;
    };
    const observer = new MutationObserver(finish);
    const timeout = setTimeout(() => { observer.disconnect(); reject(new Error('provider refusal timed out')); }, ${timeoutMs});
    observer.observe(readout, { childList: true, characterData: true, subtree: true });
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
    && layout.mobile.collapsed.close_css_available
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
