// Observe cold, warm, and offline keyless atlas behavior in an actual browser.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { extname, join, relative, resolve } from 'node:path';

const [candidateArgument, outputArgument, browserBinary] = process.argv.slice(2);
if (!candidateArgument || !outputArgument || !browserBinary) {
  throw Error('usage: node keyless-cache-matrix.mjs CANDIDATE OUTPUT BROWSER');
}
const candidate = resolve(candidateArgument);
const output = resolve(outputArgument);
await mkdir(output, { recursive: true });
const generationBytes = await readFile(join(candidate, 'generation.json'));
const generation = JSON.parse(generationBytes);
assert.deepEqual(generation.countries, ['Denmark', 'Finland', 'Norway', 'Sweden']);

const served = new Map();
const server = createServer(async (request, response) => {
  const path = resolve(candidate, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidate, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(path);
    const name = relative(candidate, path);
    served.set(name, { count: (served.get(name)?.count || 0) + 1, sha256: hash(bytes) });
    const type = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png' }[extname(path)] || 'application/octet-stream';
    response.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'public, max-age=3600' }).end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));

const browser = spawn(browserBinary, [
  '--headless=new', '--disable-gpu', '--disable-background-networking',
  '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0',
  `--user-data-dir=${join(output, 'browser-profile')}`, 'about:blank',
], { stdio: ['ignore', 'pipe', 'pipe'] });
const closed = new Promise(accept => browser.once('close', accept));
const receipt = {
  schema_version: 'atlas-keyless-cache-matrix.v1', status: 'FAIL',
  candidate_build_id: generation.candidate_build_id,
  generation_sha256: hash(generationBytes), scenarios: [], runtime_errors: [],
};
let log = '', cdp;
const tileRequests = [];
const cachedRequests = [];
const budget = setTimeout(() => browser.kill('SIGKILL'), 120000);
try {
  const endpoint = await new Promise((accept, reject) => {
    const timer = setTimeout(() => reject(Error('debugger readiness timed out')), 20000);
    browser.once('error', reject);
    browser.stderr.on('data', bytes => {
      log += bytes.toString();
      const match = log.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) { clearTimeout(timer); accept(match[1]); }
    });
  });
  const debuggerOrigin = new URL(endpoint);
  debuggerOrigin.protocol = 'http:';
  debuggerOrigin.pathname = '';
  const target = await (await fetch(`${debuggerOrigin.origin}/json/new?about:blank`, { method: 'PUT' })).json();
  cdp = await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Network.enable');
  cdp.listen(event => {
    if (event.method === 'Runtime.exceptionThrown') receipt.runtime_errors.push(event.params.exceptionDetails);
    if (event.method === 'Network.requestServedFromCache') cachedRequests.push(event.params.requestId);
    if (event.method === 'Network.requestWillBeSent' && /https:\/\/(tile\.openstreetmap\.org|tile\.opentopomap\.org)\//.test(event.params.request.url)) {
      tileRequests.push({ url: event.params.request.url, headers: event.params.request.headers });
    }
  });
  await cdp.send('Network.setBlockedURLs', { urls: [
    '*://tile.openstreetmap.org/*', '*://*.tile.openstreetmap.org/*',
    '*://tile.opentopomap.org/*', '*://*.tile.opentopomap.org/*',
  ] });
  receipt.browser = await cdp.send('Browser.getVersion');
  const base = `http://127.0.0.1:${server.address().port}/index.html`;
  for (const width of [1440, 390]) {
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
    await cdp.send('Network.clearBrowserCache');
    await cdp.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    for (const [name, url, offline] of [
      ['cold-blocked-providers', `${base}#basemap=street`, false],
      ['warm-blocked-providers', `${base}#basemap=street`, false],
      ['offline-no-basemap', `${base}#basemap=none`, true],
    ]) {
      await cdp.send('Page.navigate', { url: 'about:blank' });
      await cdp.send('Network.emulateNetworkConditions', { offline, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
      const serverBefore = [...served.values()].reduce((total, item) => total + item.count, 0);
      const cacheBefore = cachedRequests.length, tileBefore = tileRequests.length;
      await navigate(url);
      await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
      const snapshot = await evaluate("({points:BijuxPollenomicsAtlasCapture.snapshot().visible_point_count,countries:BijuxPollenomicsAtlasCapture.snapshot().countries,basemap:BijuxPollenomicsAtlasCapture.snapshot().basemap,readout:document.getElementById('basemap-readout').textContent,center:document.getElementById('center-readout').textContent})");
      assert.equal(snapshot.points, 8);
      assert.equal(snapshot.basemap, 'none');
      const tiles = tileRequests.slice(tileBefore);
      if (offline) assert.equal(tiles.length, 0);
      else {
        assert.ok(tiles.some(row => new URL(row.url).hostname === 'tile.openstreetmap.org'));
        assert.ok(tiles.some(row => new URL(row.url).hostname === 'tile.opentopomap.org'));
      }
      for (const tile of tiles) {
        assert.equal(new URL(tile.url).search, '');
        assert.equal(Object.keys(tile.headers).some(key => key.toLowerCase() === 'authorization'), false);
      }
      const serverAfter = [...served.values()].reduce((total, item) => total + item.count, 0);
      const row = { width, name, offline, url_hash: new URL(url).hash, snapshot,
        local_server_requests: serverAfter - serverBefore,
        browser_cache_events: cachedRequests.length - cacheBefore,
        street_tile_requests: tiles.filter(tile => new URL(tile.url).hostname === 'tile.openstreetmap.org').length,
        terrain_tile_requests: tiles.filter(tile => new URL(tile.url).hostname === 'tile.opentopomap.org').length,
        runtime_error_count: receipt.runtime_errors.length,
      };
      receipt.scenarios.push(row);
    }
    const [cold, warm, tileFree] = receipt.scenarios.slice(-3);
    assert.ok(cold.local_server_requests > 0, 'cold load did not request local assets');
    assert.ok(warm.browser_cache_events > 0, 'warm load did not use browser cache');
    assert.equal(warm.local_server_requests, 0, 'warm load reached the local server');
    assert.equal(tileFree.local_server_requests, 0, 'offline load reached the local server');
  }
  assert.equal(receipt.runtime_errors.length, 0);
  receipt.status = 'PASS';
} catch (error) { receipt.error = String(error.stack || error); process.exitCode = 1; }
finally {
  clearTimeout(budget);
  if (cdp) cdp.close();
  browser.kill('SIGTERM');
  const kill = setTimeout(() => browser.kill('SIGKILL'), 4000);
  await closed; clearTimeout(kill);
  await new Promise(accept => server.close(accept));
  receipt.served_files = Object.fromEntries([...served].sort());
  receipt.verifier_sha256 = hash(await readFile(new URL(import.meta.url)));
  await writeFile(join(output, 'receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  await writeFile(join(output, 'browser.log'), log);
  await rm(join(output, 'browser-profile'), { recursive: true, force: true });
}

function hash(bytes) { return createHash('sha256').update(bytes).digest('hex'); }
async function navigate(url) {
  let waiting = true;
  const loaded = new Promise((accept, reject) => {
    const timer = setTimeout(() => { waiting = false; reject(Error('page load timed out')); }, 20000);
    cdp.listen(event => { if (waiting && event.method === 'Page.loadEventFired') { waiting = false; clearTimeout(timer); accept(); } });
  });
  await cdp.send('Page.navigate', { url });
  await loaded;
}
async function evaluate(expression) {
  const value = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (value.exceptionDetails) throw Error(JSON.stringify(value.exceptionDetails));
  return value.result.value;
}
async function waitFor(expression) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (await evaluate(expression)) return;
    await new Promise(accept => setTimeout(accept, 50));
  }
  throw Error(`timed out: ${expression}`);
}
async function connect(url) {
  return new Promise((accept, reject) => {
    const socket = new WebSocket(url), pending = new Map(), listeners = new Set(); let id = 0;
    socket.addEventListener('error', reject);
    socket.addEventListener('open', () => {
      socket.addEventListener('message', event => {
        const value = JSON.parse(event.data);
        if (!value.id) { listeners.forEach(listener => listener(value)); return; }
        const request = pending.get(value.id); if (!request) return;
        pending.delete(value.id); clearTimeout(request.timeout);
        if (value.error) request.reject(Error(JSON.stringify(value.error)));
        else request.accept(value.result);
      });
      accept({
        send(method, params = {}) {
          const requestId = ++id;
          return new Promise((acceptRequest, rejectRequest) => {
            const timeout = setTimeout(() => { pending.delete(requestId); rejectRequest(Error(`CDP timeout: ${method}`)); }, 20000);
            pending.set(requestId, { accept: acceptRequest, reject: rejectRequest, timeout });
            socket.send(JSON.stringify({ id: requestId, method, params }));
          });
        },
        listen(callback) { listeners.add(callback); }, close() { socket.close(); },
      });
    });
  });
}
