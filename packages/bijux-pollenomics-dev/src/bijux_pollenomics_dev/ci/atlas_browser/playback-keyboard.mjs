// Exercise the production atlas BP playback by keyboard against a controlled fixture.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { resolve, relative, join, extname } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node playback-keyboard.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidate = resolve(candidateDirectory), output = resolve(outputDirectory);
await mkdir(output, { recursive: true });
const generationBytes = await readFile(join(candidate, 'generation.json'));
const generation = JSON.parse(generationBytes);
assert.equal(generation.status, 'controlled_bp_chronology_only');
assert.equal(generation.scientific_admission, 'not_evaluated');
assert.equal(generation.geometry_status, 'controlled_schematic_rectangles_only');
assert.deepEqual(generation.fixture_bp_values, [0, 150, 300]);
for (const [path, expected] of Object.entries(generation.inputs_sha256)) {
  assert.equal(sha(await readFile(path)), expected, `candidate source ${path}`);
}
for (const [path, expected] of Object.entries(generation.outputs_sha256)) {
  assert.equal(sha(await readFile(join(candidate, path))), expected, `candidate output ${path}`);
}
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
const receipt = { schema_version: 'atlas-playback-keyboard-browser.v1', status: 'FAIL', candidate: { status: generation.status, scientific_admission: generation.scientific_admission, fixture_sha256: generation.fixture_sha256, generation_sha256: sha(generationBytes), inputs_sha256: generation.inputs_sha256, outputs_sha256: generation.outputs_sha256 }, scenarios: [], runtime_errors: [] };
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
      await navigate(`${origin}&scenario=${mode}#basemap=${mode === 'provider-failure' ? 'street' : 'none'}&time_interval=100`);
      await waitFor("globalThis.BijuxPollenomicsAtlasCapture?.snapshot().ready === true && BijuxPollenomicsAtlasCapture.snapshot().basemap === 'none'");
      if (mode === 'provider-failure') await waitFor("document.getElementById('basemap-readout').textContent.includes('terrain unavailable')");
      await waitFor("!document.getElementById('time-playback-toggle').disabled");
      const initial = await state();
      const route = [];
      for (let step = 0; step < 180; step++) {
        await key('Tab', 9);
        const focus = await focusSnapshot(); route.push(focus);
        if (step > 3 && focus.id === route[0].id && focus.class_name === route[0].class_name) break;
      }
      const timeRoute = route.filter(item => ['time-step-older', 'time-stepper-status', 'time-step-newer', 'time-playback-toggle'].includes(item.id));
      assert.equal(initial.window.join(','), '0,100');
      assert.equal(initial.playback.disabled, false);
      assert.equal(initial.playback.pressed, 'false');
      assert.equal(initial.older.disabled, false);
      assert.equal(initial.newer.disabled, true);
      assert.deepEqual(timeRoute.map(item => item.id), ['time-step-older', 'time-stepper-status', 'time-playback-toggle']);
      assert.ok(timeRoute.every(item => item.focus_visible && item.center_hit && item.inside_viewport && item.outline_style !== 'none' && Number.parseFloat(item.outline_width) > 0), 'BP Tab stop lacks visible, reachable focus');
      await tabTo('time-step-older'); await key('Enter', 13); await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 100');
      const older = { state: await state(), focus: await focusSnapshot() };
      assert.equal(older.focus.id, 'time-step-older');
      await key('Enter', 13); await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 200');
      const oldestBoundary = { state: await state(), focus: await focusSnapshot() };
      assert.equal(oldestBoundary.focus.id, 'time-step-newer');
      assert.ok(oldestBoundary.focus.focus_visible && oldestBoundary.focus.center_hit && oldestBoundary.focus.inside_viewport, 'oldest BP boundary handoff lacks reachable focus');
      await key(' ', 32); await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 100');
      const newerIntermediate = { state: await state(), focus: await focusSnapshot() };
      assert.equal(newerIntermediate.focus.id, 'time-step-newer');
      await key(' ', 32); await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 0');
      const newer = { state: await state(), focus: await focusSnapshot() };
      assert.equal(newer.focus.id, 'time-step-older');
      assert.ok(newer.focus.focus_visible && newer.focus.center_hit && newer.focus.inside_viewport, 'BP boundary handoff lacks reachable focus');
      await tabTo('time-playback-toggle');
      await key('Tab', 9, true); const reverseStatus = await focusSnapshot();
      await key('Tab', 9, true); const reverseOlder = await focusSnapshot();
      await key('Tab', 9); const forwardStatus = await focusSnapshot();
      await key('Tab', 9); const forwardPlayback = await focusSnapshot();
      assert.deepEqual([reverseStatus.id, reverseOlder.id, forwardStatus.id, forwardPlayback.id], ['time-stepper-status', 'time-step-older', 'time-stepper-status', 'time-playback-toggle']);
      assert.ok([reverseStatus, reverseOlder, forwardStatus, forwardPlayback].every(item => item.focus_visible && item.center_hit && item.inside_viewport), 'BP reverse or forward Tab route lacks reachable focus');
      await key('Enter', 13);
      await waitFor("document.getElementById('time-playback-toggle').getAttribute('aria-pressed') === 'true'");
      const playing = { state: await state(), focus: await focusSnapshot(), screenshot: await screenshot(width, `${mode}-playing`) };
      assert.equal(playing.state.window.join(','), '200,300');
      assert.equal(playing.focus.id, 'time-playback-toggle');
      assert.ok(playing.focus.focus_visible && playing.focus.center_hit && playing.focus.inside_viewport);
      await key(' ', 32); await waitFor("document.getElementById('time-playback-toggle').getAttribute('aria-pressed') === 'false'");
      const paused = { state: await state(), focus: await focusSnapshot() };
      await new Promise(accept => setTimeout(accept, 1100));
      assert.equal((await state()).window.join(','), '200,300', 'Space pause did not stop the timer');
      assert.equal(paused.focus.id, 'time-playback-toggle');
      await key(' ', 32); await waitFor("document.getElementById('time-playback-toggle').getAttribute('aria-pressed') === 'true'");
      const resumed = { state: await state(), focus: await focusSnapshot() };
      await waitFor('BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 100');
      const middle = await state();
      await waitFor("BijuxPollenomicsAtlasCapture.snapshot().time_window_bp?.younger_bp === 0 && document.getElementById('time-playback-toggle').getAttribute('aria-pressed') === 'false'");
      const finished = { state: await state(), focus: await focusSnapshot(), screenshot: await screenshot(width, `${mode}-finished`) };
      assert.equal(resumed.state.window.join(','), '200,300');
      assert.equal(middle.window.join(','), '100,200');
      assert.equal(finished.state.window.join(','), '0,100');
      assert.equal(finished.focus.id, 'time-playback-toggle');
      const tiles = tileRequests.slice(firstTile);
      if (mode === 'tile-free') assert.equal(tiles.length, 0, 'direct No basemap requested provider tiles');
      else {
        assert.ok(tiles.filter(url => new URL(url).hostname === 'tile.openstreetmap.org').length >= 3);
        assert.ok(tiles.filter(url => new URL(url).hostname === 'tile.opentopomap.org').length >= 3);
      }
      receipt.scenarios.push({ width, mode, tile_requests: tiles.length, route: timeRoute, reverse_route: [reverseStatus, reverseOlder, forwardStatus, forwardPlayback], initial, older, oldest_boundary: oldestBoundary, newer_intermediate: newerIntermediate, newer, playing, paused, resumed, middle, finished });
    }
  }
  assert.equal(receipt.runtime_errors.length, 0);
  receipt.status = 'PASS';
} catch (error) {
  receipt.error = String(error.stack || error);
  if (cdp) { try { receipt.diagnostic = { state: await state(), focus: await focusSnapshot(), hash: await evaluate('location.hash') }; receipt.diagnostic_screenshot = await screenshot(await evaluate('innerWidth'), 'diagnostic'); } catch (diagnosticError) { receipt.diagnostic_error = String(diagnosticError); } }
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
async function key(name, code, shift = false) { const params = { type: 'keyDown', key: name, code: name === ' ' ? 'Space' : name, windowsVirtualKeyCode: code, modifiers: shift ? 8 : 0, ...(name === 'Enter' ? { text: '\r' } : name === ' ' ? { text: ' ' } : {}) }; await cdp.send('Input.dispatchKeyEvent', params); await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: name, code: params.code, windowsVirtualKeyCode: code, modifiers: shift ? 8 : 0 }); }
async function focusSnapshot() { return evaluate(`(() => { const element = document.activeElement, rect = element.getBoundingClientRect(), style = getComputedStyle(element), hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2); return { id: element.id || null, class_name: String(element.className || ''), focus_visible: element.matches(':focus-visible'), outline_width: style.outlineWidth, outline_style: style.outlineStyle, center_hit: element.contains(hit), inside_viewport: rect.left >= 0 && rect.right <= innerWidth && rect.top >= 0 && rect.bottom <= innerHeight }; })()`); }
async function tabTo(id) { await evaluate("document.getElementById('fit-active').focus()"); for (let i = 0; i < 30; i++) { await key('Tab', 9); if ((await focusSnapshot()).id === id) return; } throw Error(`Tab did not reach ${id}`); }
async function state() { return evaluate(`(() => { const button = id => { const element = document.getElementById(id); return { disabled: element.disabled, pressed: element.getAttribute('aria-pressed'), text: element.textContent.trim() }; }; const snapshot = BijuxPollenomicsAtlasCapture.snapshot(), window = snapshot.time_window_bp; return { window: [window.younger_bp, window.older_bp], basemap: snapshot.basemap, playback: button('time-playback-toggle'), older: button('time-step-older'), newer: button('time-step-newer'), status: button('time-stepper-status') }; })()`); }
