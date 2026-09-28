// Verify that a selected country retains a labeled endpoint of a controlled cross-border edge.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node cross-border-neighbor.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generationBytes = await readFile(join(candidate, 'generation.json'));
const generation = JSON.parse(generationBytes);
assert.equal(generation.status, 'controlled_cross_border_only');
assert.equal(generation.scientific_admission, 'not_evaluated');
assert.equal(generation.geometry_status, 'controlled_schematic_rectangles_only');
assert.deepEqual(generation.point_record_ids, ['controlled:no:older', 'controlled:se:younger']);
assert.deepEqual(generation.edge_ids, ['controlled:no-to-se']);
assert.deepEqual([generation.edge_relation.source_record_id, generation.edge_relation.source_country, generation.edge_relation.target_record_id, generation.edge_relation.target_country, generation.edge_relation.cross_border, generation.edge_relation.lag_years], ['controlled:no:older', 'Norway', 'controlled:se:younger', 'Sweden', true, 100]);
assert.ok(generation.edge_relation.wgs84_distance_km > 0 && generation.edge_relation.wgs84_distance_km < 100);
for (const [path, expected] of Object.entries(generation.inputs_sha256)) assert.equal(sha(await readFile(path)), expected, `candidate source ${path}`);
for (const [path, expected] of Object.entries(generation.outputs_sha256)) assert.equal(sha(await readFile(join(candidate, path))), expected, `candidate output ${path}`);
const requests = new Map(), tileRequests = [];
const server = createServer(async (request, response) => {
  const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidate, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(path);
    requests.set(relative(candidate, path), sha(bytes));
    const type = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png' }[extname(path)] || 'application/octet-stream';
    response.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' }).end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));
const browser = spawn(browserBinary, ['--headless=new', '--disable-gpu', '--disable-background-networking', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${join(output, 'browser-profile')}`, 'about:blank'], { stdio: ['ignore', 'pipe', 'pipe'] });
const closed = new Promise(accept => browser.once('close', accept));
const receipt = { schema_version: 'atlas-cross-border-neighbor-browser.v1', status: 'FAIL', candidate: { generation_sha256: sha(generationBytes), fixture_sha256: generation.fixture_sha256, inputs_sha256: generation.inputs_sha256, outputs_sha256: generation.outputs_sha256, edge_relation: generation.edge_relation, scientific_admission: generation.scientific_admission }, scenarios: [], runtime_errors: [] };
let log = '', cdp;
const budget = setTimeout(() => browser.kill('SIGKILL'), 150000);
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
  cdp.listen(event => {
    if (event.method === 'Runtime.exceptionThrown') receipt.runtime_errors.push(event.params.exceptionDetails);
    if (event.method === 'Network.requestWillBeSent' && /https:\/\/(tile\.openstreetmap\.org|tile\.opentopomap\.org)\//.test(event.params.request.url)) tileRequests.push(event.params.request.url);
  });
  await cdp.send('Network.setBlockedURLs', { urls: ['*://tile.openstreetmap.org/*', '*://*.tile.openstreetmap.org/*', '*://tile.opentopomap.org/*', '*://*.tile.opentopomap.org/*'] });
  receipt.browser = await cdp.send('Browser.getVersion');
  for (const width of [320, 1440]) {
    await cdp.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    const origin = `http://127.0.0.1:${server.address().port}/index.html?viewport=${width}`;
    for (const mode of ['provider-failure', 'tile-free']) {
      const firstTile = tileRequests.length;
      const views = {};
      for (const country of ['all', 'Sweden', 'Norway', 'Denmark']) {
        const params = new URLSearchParams({ basemap: mode === 'provider-failure' ? 'street' : 'none' });
        if (country !== 'all') params.set('countries', country);
        await navigate(`${origin}&scenario=${mode}&country=${country}#${params}`);
        await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
        if (mode === 'provider-failure') await waitFor("document.getElementById('basemap-readout').textContent.includes('terrain unavailable')");
        views[country] = { state: await state(), screenshot: await screenshot(width, `${mode}-${country.toLowerCase()}`) };
      }
      receipt.pending_views = { width, mode, views };
      assert.deepEqual(views.all.state.countries, ['Denmark', 'Finland', 'Norway', 'Sweden']);
      assert.equal(views.all.state.focal_count, 2);
      assert.equal(views.all.state.neighbor_count, 0);
      assert.equal(views.all.state.edge_count, 1);
      for (const [focal, neighbor] of [['Sweden', 'Norway'], ['Norway', 'Sweden']]) {
        const view = views[focal].state;
        assert.deepEqual(view.countries, [focal]);
        assert.equal(view.focal_count, 1, `${focal} focal point count`);
        assert.equal(view.neighbor_count, 1, `${neighbor} retained neighbor count`);
        assert.equal(view.edge_count, 1, `${focal} cross-border relation`);
        assert.deepEqual(view.neighbor_labels, [`Neighbor context · ${neighbor}`]);
        assert.ok(view.selection.includes('1 focal point · 1 labeled neighbor context'));
        assert.equal(view.country_chips[focal], 1);
        assert.equal(view.country_chips[neighbor], 0);
        assert.ok(view.neighbor_label_visible, `${neighbor} neighbor label is not visible on map`);
      }
      assert.deepEqual(views.Denmark.state.countries, ['Denmark']);
      assert.equal(views.Denmark.state.focal_count, 0);
      assert.equal(views.Denmark.state.neighbor_count, 0);
      assert.equal(views.Denmark.state.edge_count, 0);
      assert.deepEqual(views.Denmark.state.neighbor_labels, []);
      const tiles = tileRequests.slice(firstTile);
      if (mode === 'tile-free') assert.equal(tiles.length, 0, 'direct No basemap requested provider tiles');
      else {
        assert.ok(tiles.some(url => new URL(url).hostname === 'tile.openstreetmap.org'));
        assert.ok(tiles.some(url => new URL(url).hostname === 'tile.opentopomap.org'));
      }
      delete receipt.pending_views;
      receipt.scenarios.push({ width, mode, tile_requests: tiles.length, views });
    }
  }
  assert.equal(receipt.runtime_errors.length, 0);
  receipt.status = 'PASS';
} catch (error) {
  receipt.error = String(error.stack || error);
  if (cdp) { try { receipt.diagnostic = { state: await state(), hash: await evaluate('location.hash') }; receipt.diagnostic_screenshot = await screenshot(await evaluate('innerWidth'), 'diagnostic'); } catch (diagnosticError) { receipt.diagnostic_error = String(diagnosticError); } }
  process.exitCode = 1;
} finally {
  clearTimeout(budget); if (cdp) cdp.close(); browser.kill('SIGTERM'); const kill = setTimeout(() => browser.kill('SIGKILL'), 4000); await closed; clearTimeout(kill);
  await new Promise(accept => server.close(accept));
  receipt.served_files_sha256 = Object.fromEntries([...requests].sort());
  receipt.verifier_sha256 = sha(await readFile(new URL(import.meta.url)));
  await writeFile(join(output, 'receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  await writeFile(join(output, 'browser.log'), log);
  await rm(join(output, 'browser-profile'), { recursive: true, force: true });
}

function sha(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
async function screenshot(width, mode) { const result = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false }); const bytes = Buffer.from(result.data, 'base64'), path = join(output, `${width}-${mode}.png`); await writeFile(path, bytes); return { path: relative(output, path), sha256: sha(bytes) }; }
async function navigate(url) { let waiting = true; const loaded = new Promise((accept, reject) => { const timeout = setTimeout(() => { waiting = false; reject(Error('page load timed out')); }, 20000); cdp.listen(event => { if (waiting && event.method === 'Page.loadEventFired') { waiting = false; clearTimeout(timeout); accept(); } }); }); const navigation = await cdp.send('Page.navigate', { url }); if (!navigation.loaderId) await cdp.send('Page.reload', { ignoreCache: true }); await loaded; }
async function evaluate(expression) { const value = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true }); if (value.exceptionDetails) throw Error(JSON.stringify(value.exceptionDetails)); return value.result.value; }
async function waitFor(expression) { const deadline = Date.now() + 20000; while (Date.now() < deadline) { if (await evaluate(expression)) return; await new Promise(accept => setTimeout(accept, 50)); } throw Error(`timed out: ${expression}`); }
async function connect(url) { return new Promise((accept, reject) => { const socket = new WebSocket(url), pending = new Map(), listeners = new Set(); let id = 0; socket.addEventListener('error', reject); socket.addEventListener('open', () => { socket.addEventListener('message', event => { const value = JSON.parse(event.data); if (!value.id) { listeners.forEach(listener => listener(value)); return; } const request = pending.get(value.id); if (!request) return; pending.delete(value.id); clearTimeout(request.timeout); if (value.error) request.reject(Error(JSON.stringify(value.error))); else request.accept(value.result); }); accept({ send(method, params = {}) { const requestId = ++id; return new Promise((acceptRequest, rejectRequest) => { const timeout = setTimeout(() => { pending.delete(requestId); rejectRequest(Error(`CDP timeout: ${method}`)); }, 20000); pending.set(requestId, { accept: acceptRequest, reject: rejectRequest, timeout }); socket.send(JSON.stringify({ id: requestId, method, params })); }); }, listen(callback) { listeners.add(callback); }, close() { socket.close(); } }); }); }); }
async function state() { return evaluate(`(() => { const snapshot = BijuxPollenomicsAtlasCapture.snapshot(); const labels = [...document.querySelectorAll('.leaflet-tooltip.atlas-neighbor-context-label')]; const chip = Object.fromEntries([...document.querySelectorAll('.country-checkbox')].map(input => [input.value, Number(input.closest('label').querySelector('.chip-count').textContent)])); return { countries: snapshot.countries, focal_count: snapshot.visible_point_count, neighbor_count: snapshot.visible_neighbor_context_point_count ?? 0, edge_count: snapshot.visible_governed_candidate_count, neighbor_labels: labels.map(label => label.textContent.trim()).sort(), neighbor_label_visible: labels.every(label => { const rect = label.getBoundingClientRect(), style = getComputedStyle(label); return rect.width > 0 && rect.height > 0 && rect.left >= 0 && rect.right <= innerWidth && rect.top >= 0 && rect.bottom <= innerHeight && style.visibility === 'visible' && style.opacity !== '0'; }), country_chips: chip, selection: document.getElementById('selection-readout').textContent, relation: document.getElementById('relation-summary').textContent, basemap: snapshot.basemap }; })()`); }
