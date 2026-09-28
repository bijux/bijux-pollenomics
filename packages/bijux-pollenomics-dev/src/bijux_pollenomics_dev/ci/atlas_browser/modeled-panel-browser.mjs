// Check rendered modeled panel selectors and real frame downloads against retained sources.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { extname, join, relative, resolve } from 'node:path';
import { gunzipSync } from 'node:zlib';

const [candidateArg, panelsArg, outputArg, browserBinary] = process.argv.slice(2);
if (!candidateArg || !panelsArg || !outputArg || !browserBinary) throw Error('usage: node modeled-panel-browser.mjs CANDIDATE PANELS_CSV OUTPUT BRAVE');
const candidate = resolve(candidateArg), output = resolve(outputArg);
await mkdir(output, { recursive: true });
const generation = JSON.parse(await readFile(join(candidate, 'generation.json')));
const panelBytes = await readFile(resolve(panelsArg));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
assert.equal(digest(panelBytes), generation.panel_csv_sha256);
const [header, ...lines] = panelBytes.toString().trim().split('\n');
const columns = header.split(',');
const panels = lines.map(line => Object.fromEntries(line.split(',').map((value, index) => [columns[index], value])));
assert.equal(panels.length, 400);
const sourceById = new Map();
for (const name of await readdir(candidate)) {
  if (!name.includes('.atlas-nodes.')) continue;
  const script = await readFile(join(candidate, name), 'utf8'), marker = 'globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';
  const envelope = JSON.parse(script.slice(script.indexOf(marker) + marker.length, -3));
  const raw = envelope.payload_encoding === 'gzip_base64' ? gunzipSync(Buffer.from(envelope.payload_gzip_base64, 'base64')) : Buffer.from(envelope.payload_json);
  assert.equal(digest(raw), envelope.payload_sha256);
  for (const feature of JSON.parse(raw).features) {
    const id = feature.properties.record_id;
    if (sourceById.has(id)) assert.deepEqual(feature, sourceById.get(id));
    sourceById.set(id, feature);
  }
}
assert.equal(sourceById.size, 1875);

const served = new Map();
const server = createServer(async (request, response) => {
  const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidate, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const raw = await readFile(path); served.set(relative(candidate, path), digest(raw));
    response.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png' }[extname(path)] || 'application/octet-stream', 'Cache-Control': 'no-store' }).end(raw);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));
const browser = spawn(browserBinary, ['--headless=new', '--disable-gpu', '--disable-background-networking', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${join(output, 'browser-profile')}`, 'about:blank'], { stdio: ['ignore', 'pipe', 'pipe'] });
const closed = new Promise(accept => browser.once('close', accept));
let log = '', cdp;
const receipt = { schema_version: 'atlas-modeled-panel-browser-verification.v1', status: 'FAIL', scientific_admission: false, scenarios: [], runtime_errors: [], blocked_tile_requests: 0 };
const budget = setTimeout(() => browser.kill('SIGKILL'), 180000);
try {
  const endpoint = await new Promise((accept, reject) => {
    const timer = setTimeout(() => reject(Error('debugger readiness timed out')), 20000);
    browser.once('error', reject);
    browser.stderr.on('data', bytes => { log += bytes.toString(); const match = log.match(/DevTools listening on (ws:\/\/[^\s]+)/); if (match) { clearTimeout(timer); accept(match[1]); } });
  });
  const debuggerOrigin = new URL(endpoint); debuggerOrigin.protocol = 'http:'; debuggerOrigin.pathname = '';
  const target = await (await fetch(`${debuggerOrigin.origin}/json/new?about:blank`, { method: 'PUT' })).json();
  cdp = await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable'); await cdp.send('Network.enable');
  cdp.listen(event => { if (event.method === 'Runtime.exceptionThrown') receipt.runtime_errors.push(event.params.exceptionDetails); if (event.method === 'Network.loadingFailed' && event.params.blockedReason) receipt.blocked_tile_requests++; });
  await cdp.send('Network.setBlockedURLs', { urls: ['*://tile.openstreetmap.org/*', '*://*.tile.openstreetmap.org/*', '*://tile.opentopomap.org/*', '*://*.tile.opentopomap.org/*'] });
  receipt.browser = await cdp.send('Browser.getVersion');
  for (const width of [320, 1440]) {
    await cdp.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    for (const [mode, country, windowIndex] of [['no_basemap', 'Denmark', 0], ['blocked_provider', 'Sweden', 24]]) {
      const window = generation.manifest.windows_oldest_to_present[windowIndex];
      for (const [metric, family, label, sourceClass] of [
        ['ET', 'source_land_cover_types', 'Evergreen trees', 'source_land_cover_type'],
        ['ST', 'source_land_cover_types', 'Summer-green trees', 'source_land_cover_type'],
        ['OL', 'source_land_cover_types', 'Open land', 'source_land_cover_type'],
        ['AL', 'source_pft_codes', 'Agricultural land - cereals', 'source_pft_component_of_open_land'],
      ]) {
        const hash = new URLSearchParams({ basemap: mode === 'no_basemap' ? 'none' : 'street', countries: country, modeled_context: window.label, modeled_family: family, modeled_metric: metric });
        const url = `http://127.0.0.1:${server.address().port}/index.html?width=${width}&mode=${mode}&metric=${metric}#${hash}`;
        await navigate(url); await waitFor('globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && !document.getElementById("modeled-context-download").disabled');
        const state = await evaluate(`({capture:BijuxPollenomicsAtlasCapture.snapshot(),family:document.getElementById('modeled-context-family').value,familyText:document.getElementById('modeled-context-family').selectedOptions[0].textContent,metric:document.getElementById('modeled-context-metric').value,metricText:document.getElementById('modeled-context-metric').selectedOptions[0].textContent,windowText:document.getElementById('modeled-context-window').selectedOptions[0].textContent,status:document.getElementById('modeled-context-state').textContent,hash:location.hash})`);
        assert.equal(state.family, family); assert.equal(state.metric, metric);
        assert.ok(state.familyText.includes(family === 'source_pft_codes' ? 'plant-functional-type' : 'land-cover types'));
        assert.ok(state.metricText.includes(metric === 'AL' ? 'AL' : label));
        assert.ok(state.windowText.includes(window.label)); assert.ok(state.status.includes('source standard error'));
        assert.ok(state.status.includes('no interpolation or propagation'));
        assert.deepEqual(state.capture.countries, [country]);
        assert.equal(state.capture.modeled_context.window_label, window.label);
        assert.equal(state.capture.modeled_context.metric_key, metric);
        const directory = join(output, 'downloads', `${width}-${mode}-${metric}`);
        const downloaded = await download(directory);
        const frame = downloaded.value;
        assert.equal(frame.schema_version, 'modeled-context-visible-frame.v3');
        assert.equal(frame.modeled_context.metric_family_key, family);
        assert.equal(frame.modeled_context.metric_key, metric);
        assert.equal(frame.modeled_context.metric_source_label, metric === 'AL' ? 'AL' : `${label} (${metric})`);
        assert.equal(frame.modeled_context.metric_definition, label);
        assert.equal(frame.modeled_context.metric_label, `${label} (${metric})`);
        assert.equal(frame.modeled_context.evidence_role, 'context_only');
        assert.equal(frame.modeled_context.interpolation_allowed, false);
        assert.equal(frame.modeled_context.propagation_use_allowed, false);
        const expected = [...sourceById.values()].filter(feature => feature.properties.country === country && feature.properties.time_label === window.label).sort((a, b) => a.properties.record_id.localeCompare(b.properties.record_id));
        assert.deepEqual(frame.features, expected, 'downloaded frame must preserve exact source records');
        const panel = panels.find(row => row.country === country && row.source_window === window.label && row.metric_key === metric);
        assert.ok(panel); assert.equal(panel.source_label, label); assert.equal(panel.source_class, sourceClass);
        assert.equal(expected.length, Number(panel.cell_count));
        const missing = expected.filter(feature => feature.properties.quality_class === 'no_pollen_data');
        assert.equal(missing.length, Number(panel.no_pollen_data_count));
        assert.equal(frame.modeled_context.quality_class_counts.no_pollen_data || 0, missing.length);
        for (const feature of missing) for (const values of ['reconstruction_values', 'standard_errors']) assert.ok(Object.values(feature.properties[values]).every(value => value === null));
        const modeled = expected.filter(feature => feature.properties.quality_class !== 'no_pollen_data');
        assert.equal(modeled.length, Number(panel.modeled_count));
        for (const [property, minimum, maximum] of [
          ['reconstruction_values', 'minimum_estimate_percent', 'maximum_estimate_percent'],
          ['standard_errors', 'minimum_standard_error_percent', 'maximum_standard_error_percent'],
        ]) {
          const values = modeled.map(feature => feature.properties[property][metric]);
          assert.ok(values.every(value => typeof value === 'number' && Number.isFinite(value)));
          assert.ok(Math.abs(Math.min(...values) - Number(panel[minimum])) < 1e-9);
          assert.ok(Math.abs(Math.max(...values) - Number(panel[maximum])) < 1e-9);
        }
        receipt.scenarios.push({ width, mode, country, source_window: window.label, metric, family, source_label: label, source_class: sourceClass, feature_count: expected.length, modeled_count: modeled.length, no_pollen_null_count: missing.length, source_records_equal: true, estimates_and_standard_errors_equal: true, panel_csv_equal: true, download_path: relative(output, downloaded.path), download_sha256: downloaded.sha256 });
      }
      const screenshot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
      await writeFile(join(output, `${width}-${mode}.png`), Buffer.from(screenshot.data, 'base64'));
    }
  }
  assert.equal(receipt.scenarios.length, 16); assert.equal(receipt.runtime_errors.length, 0);
  receipt.status = 'PASS';
} catch (error) { receipt.error = String(error.stack || error); if (cdp) receipt.diagnostic = await evaluate('({hash:location.hash,status:document.getElementById("modeled-context-state")?.textContent,snapshot:globalThis.BijuxPollenomicsAtlasCapture?.snapshot()})').catch(() => null); process.exitCode = 1; }
finally {
  clearTimeout(budget); if (cdp) cdp.close(); browser.kill('SIGTERM'); const kill = setTimeout(() => browser.kill('SIGKILL'), 4000); await closed; clearTimeout(kill); await new Promise(accept => server.close(accept));
  receipt.served_files_sha256 = Object.fromEntries([...served].sort());
  receipt.verifier_sha256 = digest(await readFile(new URL(import.meta.url)));
  receipt.panel_csv_sha256 = digest(panelBytes);
  receipt.candidate_generation_sha256 = digest(await readFile(join(candidate, 'generation.json')));
  receipt.candidate_source_feature_sha256 = generation.source_feature_sha256;
  await writeFile(join(output, 'receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  await writeFile(join(output, 'browser.log'), log);
  await rm(join(output, 'browser-profile'), { recursive: true, force: true });
}

async function evaluate(expression) { const value = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (value.exceptionDetails) throw Error(JSON.stringify(value.exceptionDetails)); return value.result.value; }
async function waitFor(expression) { const deadline = Date.now() + 20000; while (Date.now() < deadline) { if (await evaluate(expression)) return; await new Promise(accept => setTimeout(accept, 50)); } throw Error(`timed out: ${expression}`); }
async function navigate(url) { let waiting = true; const loaded = new Promise((accept, reject) => { const timeout = setTimeout(() => { waiting = false; reject(Error('page load timed out')); }, 20000); cdp.listen(event => { if (waiting && event.method === 'Page.loadEventFired') { waiting = false; clearTimeout(timeout); accept(); } }); }); const result = await cdp.send('Page.navigate', { url }); if (!result.loaderId) await cdp.send('Page.reload', { ignoreCache: true }); await loaded; }
async function download(directory) { await mkdir(directory, { recursive: true }); await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: directory }); await evaluate("document.getElementById('modeled-context-download').click()"); const deadline = Date.now() + 20000; while (Date.now() < deadline) { const files = (await readdir(directory)).filter(name => !name.endsWith('.crdownload')); if (files.length === 1) { const path = join(directory, files[0]); try { const raw = await readFile(path); return { path, sha256: digest(raw), value: JSON.parse(raw.toString()) }; } catch { /* download is still being written */ } } await new Promise(accept => setTimeout(accept, 50)); } throw Error('actual frame download timed out'); }
async function connect(url) { return new Promise((accept, reject) => { const socket = new WebSocket(url), pending = new Map(), listeners = new Set(); let id = 0; socket.addEventListener('error', reject); socket.addEventListener('open', () => { socket.addEventListener('message', event => { const value = JSON.parse(event.data); if (!value.id) { listeners.forEach(listener => listener(value)); return; } const request = pending.get(value.id); if (!request) return; pending.delete(value.id); clearTimeout(request.timeout); if (value.error) request.reject(Error(JSON.stringify(value.error))); else request.accept(value.result); }); accept({ send(method, params = {}) { const requestId = ++id; return new Promise((acceptRequest, rejectRequest) => { const timeout = setTimeout(() => { pending.delete(requestId); rejectRequest(Error(`CDP timeout: ${method}`)); }, 20000); pending.set(requestId, { accept: acceptRequest, reject: rejectRequest, timeout }); socket.send(JSON.stringify({ id: requestId, method, params })); }); }, listen(callback) { listeners.add(callback); }, close() { socket.close(); } }); }); }); }
