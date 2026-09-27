// Focused consumer of a production-rendered synthetic detail candidate.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { extname, resolve, relative, join } from 'node:path';

const [candidateDirectory, outputDirectory, browserBinary] = process.argv.slice(2);
if (!candidateDirectory || !outputDirectory || !browserBinary) throw Error('usage: node detail-focus.mjs CANDIDATE_DIRECTORY OUTPUT_DIRECTORY BROWSER_BINARY');
const candidateRoot = resolve(candidateDirectory);
const outputRoot = resolve(outputDirectory);
await mkdir(outputRoot, { recursive: true });
const served = new Map();
const server = createServer(async (request, response) => {
  const path = resolve(candidateRoot, `.${decodeURIComponent(new URL(request.url, 'http://localhost').pathname)}`);
  if (relative(candidateRoot, path).startsWith('..')) { response.writeHead(403).end(); return; }
  try {
    const bytes = await readFile(path);
    served.set(relative(candidateRoot, path), createHash('sha256').update(bytes).digest('hex'));
    const type = { '.html': 'text/html', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png' }[extname(path)] || 'application/octet-stream';
    response.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' }).end(bytes);
  } catch { response.writeHead(404).end(); }
});
await new Promise(accept => server.listen(0, '127.0.0.1', accept));
const profile = join(outputRoot, 'browser-profile');
const browser = spawn(browserBinary, ['--headless=new', '--disable-gpu', '--disable-background-networking', '--no-first-run', '--no-default-browser-check', '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'], { stdio: ['ignore', 'pipe', 'pipe'] });
const closed = new Promise(accept => browser.once('close', accept));
let log = '';
let cdp;
const receipt = { schema_version: 'atlas-detail-focus-verification.v1', fixture_kind: 'synthetic_ui_contract', status: 'FAIL', assertions: [], runtime_errors: [] };
const jobTimeout = setTimeout(() => browser.kill('SIGKILL'), 120000);
try {
  const endpoint = await new Promise((accept, reject) => {
    const timeout = setTimeout(() => reject(Error('browser debugger readiness timed out')), 20000);
    browser.once('error', reject);
    browser.stderr.on('data', bytes => {
      log += bytes.toString();
      const match = log.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (match) { clearTimeout(timeout); accept(match[1]); }
    });
  });
  const origin = new URL(endpoint); origin.protocol = 'http:'; origin.pathname = '';
  const target = await (await fetch(`${origin.origin}/json/new?about:blank`, { method: 'PUT' })).json();
  cdp = await connect(target.webSocketDebuggerUrl);
  await cdp.send('Runtime.enable');
  cdp.listen(event => { if (event.method === 'Runtime.exceptionThrown') receipt.runtime_errors.push(event.params.exceptionDetails); });
  await cdp.send('Network.enable');
  await cdp.send('Network.setBlockedURLs', { urls: ['*://tile.openstreetmap.org/*', '*://*.tile.openstreetmap.org/*', '*://tile.opentopomap.org/*', '*://*.tile.opentopomap.org/*'] });
  receipt.browser = await cdp.send('Browser.getVersion');
  for (const width of [1440, 390]) {
    await cdp.send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: false });
    await cdp.send('Page.navigate', { url: `http://127.0.0.1:${server.address().port}/index.html?viewport=${width}#basemap=none` });
    await waitFor(`location.search === '?viewport=${width}' && document.getElementById('map')?.getAttribute('aria-busy') === 'false'`);
    await evaluate("document.getElementById('search-toggle').click()");
    await cdp.send('Input.insertText', { text: 'evidence-0' });
    await waitFor("document.querySelector('[data-search-index]') !== null");
    await key('Enter', 13);
    await waitFor("document.getElementById('focus-detail').dataset.detailStatus === 'available'");
    await check('opening-selects-overview', width, "document.activeElement.id === 'focus-tab-overview'");
    await key('ArrowLeft', 37);
    await check('left-wraps-to-provenance', width, "document.activeElement.id === 'focus-tab-provenance'");
    await key('ArrowRight', 39);
    await check('right-wraps-to-overview', width, "document.activeElement.id === 'focus-tab-overview'");
    await key('End', 35);
    await check('end-selects-provenance', width, "document.activeElement.id === 'focus-tab-provenance'");
    await check('provenance-retains-raw-locator', width, "document.getElementById('focus-detail').textContent.includes('raw/sites.json#site:1') && document.getElementById('focus-detail').textContent.includes('fixture-build')");
    await key('Home', 36);
    await key('ArrowRight', 39);
    await check('samples-selected-and-linked', width, "document.activeElement.id === 'focus-tab-samples' && document.getElementById('focus-detail').getAttribute('aria-labelledby') === 'focus-tab-samples' && document.getElementById('focus-detail').textContent.includes('Showing 1–25 of 26') && document.querySelectorAll('#focus-tabs [tabindex=\"0\"]').length === 1");
    await key('Tab', 9);
    await check('tab-enters-evidence-panel', width, "document.activeElement.id === 'focus-detail'");
    await key('Tab', 9);
    await check('tab-skips-disabled-previous', width, "document.activeElement.dataset.pageDirection === 'next'");
    await key('Enter', 13);
    await check('paging-preserves-focus-at-disabled-boundary', width, "document.activeElement.id === 'focus-detail' && document.getElementById('focus-detail').textContent.includes('Showing 26–26 of 26')");
    await evaluate("document.getElementById('focus-tab-chronology').focus()");
    await key('Enter', 13);
    await check('tab-click-retains-focus', width, "document.activeElement.id === 'focus-tab-chronology' && document.getElementById('focus-detail').textContent.includes('cal BP')");
    await key('ArrowRight', 39);
    await check('composition-retains-count-and-unit', width, "document.activeElement.id === 'focus-tab-pollen_composition' && document.getElementById('focus-detail').textContent.includes('taxon:triticum') && document.getElementById('focus-detail').textContent.includes('count')");
    await evaluate("document.getElementById('focus-next').focus()");
    await key('Enter', 13);
    await check('next-record-retains-navigation-focus-and-unavailability', width, "document.activeElement.id === 'focus-next' && document.getElementById('focus-title').textContent === 'evidence-1' && document.getElementById('focus-detail').dataset.detailStatus === 'unavailable'");
    await evaluate("document.getElementById('focus-previous').focus()");
    await key('Enter', 13);
    await waitFor("document.getElementById('focus-detail').dataset.detailStatus === 'available'");
    await check('previous-record-retains-navigation-focus-and-identity', width, "document.activeElement.id === 'focus-previous' && document.getElementById('focus-title').textContent === 'evidence-0'");
    await key('Escape', 27);
    await check('escape-closes-and-returns-to-search', width, "document.getElementById('focus-card').hidden && document.activeElement.id === 'search-toggle'");
    await evaluate("document.getElementById('search-toggle').click()");
    await key('Enter', 13);
    await waitFor("document.getElementById('focus-detail').dataset.detailStatus === 'available'");
    await evaluate("document.getElementById('focus-close').focus()");
    await key('Enter', 13);
    await check('clear-closes-and-returns-to-search', width, "document.getElementById('focus-card').hidden && document.activeElement.id === 'search-toggle'");
  }
  assert.equal(receipt.runtime_errors.length, 0, 'browser runtime errors');
  receipt.status = 'PASS';
} catch (error) {
  receipt.error = String(error.stack || error);
  process.exitCode = 1;
} finally {
  clearTimeout(jobTimeout);
  if (cdp) cdp.close();
  browser.kill('SIGTERM');
  const kill = setTimeout(() => browser.kill('SIGKILL'), 4000);
  await closed; clearTimeout(kill);
  await new Promise(accept => server.close(accept));
  await writeFile(join(outputRoot, 'browser.log'), log);
  receipt.served_files_sha256 = Object.fromEntries([...served].sort());
  receipt.verifier_sha256 = createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex');
  await writeFile(join(outputRoot, 'receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`);
  await rm(profile, { recursive: true, force: true });
}

async function evaluate(expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function waitFor(expression) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (await evaluate(expression)) return;
    await new Promise(accept => setTimeout(accept, 50));
  }
  throw Error(`timed out: ${expression}`);
}
async function check(name, width, expression) {
  const passed = await evaluate(expression);
  receipt.assertions.push({ name, width, passed });
  if (!passed) receipt.failed_observation = await evaluate("({active:document.activeElement?.outerHTML,detail:document.getElementById('focus-detail')?.textContent})");
  assert.equal(passed, true, `${width}: ${name}`);
}
async function key(name, code) {
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: name, code: name, windowsVirtualKeyCode: code, ...(name === 'Enter' ? { text: '\r' } : {}) });
  await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: name, windowsVirtualKeyCode: code });
}
async function connect(url) {
  return new Promise((accept, reject) => {
    const socket = new WebSocket(url);
    const pending = new Map();
    const listeners = new Set();
    let id = 0;
    socket.addEventListener('error', reject);
    socket.addEventListener('open', () => {
      socket.addEventListener('message', event => {
        const value = JSON.parse(event.data);
        if (!value.id) { listeners.forEach(listener => listener(value)); return; }
        const request = pending.get(value.id);
        if (!request) return;
        pending.delete(value.id); clearTimeout(request.timeout);
        if (value.error) request.reject(Error(JSON.stringify(value.error))); else request.accept(value.result);
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
        listen(callback) { listeners.add(callback); },
        close() { socket.close(); },
      });
    });
  });
}
