import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { readFile, mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import { dirname, extname, join, relative, resolve } from 'node:path';

const [repositoryArg, artifactArg, browserBinary] = process.argv.slice(2);
if (!repositoryArg || !artifactArg || !browserBinary) throw new Error('repository, artifact directory, and browser binary are required');
const repository = resolve(repositoryArg);
const artifact = resolve(artifactArg);
const site = resolve(repository, 'docs/report');
if (!relative(repository, artifact).startsWith('artifacts/')) throw new Error('output must be under repository artifacts');
await mkdir(dirname(artifact), { recursive: true });
await mkdir(artifact, { recursive: false });
const downloads = join(artifact, 'downloads');
const profile = join(artifact, 'brave-profile');
await mkdir(downloads);
const requests = [];
const server = createServer(async (request, response) => {
  const pathname = new URL(request.url, 'http://127.0.0.1').pathname;
  requests.push(pathname);
  const path = resolve(site, `.${decodeURIComponent(pathname)}`);
  if (relative(site, path).startsWith('..')) return response.writeHead(403).end();
  try {
    const content = await readFile(path);
    response.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' }[extname(path)] || 'application/octet-stream' });
    response.end(content);
  } catch { response.writeHead(404).end(); }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const browser = spawn(browserBinary, [
  '--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-component-update',
  '--disable-default-apps', '--no-default-browser-check', '--disable-extensions', '--disable-sync',
  '--no-first-run', '--remote-allow-origins=*', '--remote-debugging-port=0',
  '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
  `--user-data-dir=${profile}`, 'about:blank',
], { stdio: ['ignore', 'pipe', 'pipe'] });
let browserLog = '';
browser.stdout.on('data', (part) => { browserLog += part.toString(); });
browser.stderr.on('data', (part) => { browserLog += part.toString(); });
const timeout = 60000;
function until(check, label) {
  return new Promise((ok, fail) => {
    const start = Date.now();
    const tick = async () => {
      try { const value = await check(); if (value) return ok(value); }
      catch (error) { return fail(error); }
      if (Date.now() - start > timeout) return fail(new Error(`${label} timed out`));
      setTimeout(tick, 100);
    };
    tick();
  });
}
function connect(url) {
  return new Promise((ok, fail) => {
    const socket = new WebSocket(url);
    const pending = new Map();
    const events = [];
    let nextId = 0;
    socket.addEventListener('error', fail, { once: true });
    socket.addEventListener('open', () => {
      socket.addEventListener('message', (message) => {
        const payload = JSON.parse(message.data);
        if (payload.id) {
          const task = pending.get(payload.id);
          pending.delete(payload.id);
          if (payload.error) task.fail(new Error(JSON.stringify(payload.error)));
          else task.ok(payload.result || {});
        } else events.push(payload);
      });
      ok({
        events,
        send(method, params = {}) {
          const id = ++nextId;
          socket.send(JSON.stringify({ id, method, params }));
          return new Promise((resolveRequest, rejectRequest) => pending.set(id, { ok: resolveRequest, fail: rejectRequest }));
        },
        close() { socket.close(); },
      });
    }, { once: true });
  });
}
async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
let cdp;
try {
  const debuggerUrl = await until(() => browserLog.match(/DevTools listening on (ws:\/\/[^\s]+)/)?.[1], 'debugger endpoint');
  const debuggerOrigin = new URL(debuggerUrl);
  debuggerOrigin.protocol = 'http:';
  const targetResponse = await fetch(`${debuggerOrigin.origin}/json/new?about:blank`, { method: 'PUT' });
  if (!targetResponse.ok) throw new Error(`target creation: ${targetResponse.status}`);
  const target = await targetResponse.json();
  cdp = await connect(target.webSocketDebuggerUrl);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads, eventsEnabled: true });
  await cdp.send('Page.navigate', { url: `http://127.0.0.1:${server.address().port}/regions/nordic/nordic_map.html#basemap=none&modeled_context=0-100+BP` });
  await until(async () => evaluate(cdp, `document.readyState === 'complete' && document.querySelectorAll('.country-checkbox').length === 4 && document.getElementById('modeled-context-window').options.length === 25 && !document.getElementById('modeled-context-download').disabled`), 'initial modeled map readiness');
  const controls = await evaluate(cdp, `(() => {
    for (const country of ['Finland', 'Norway']) {
      const checkbox = [...document.querySelectorAll('.country-checkbox')].find((item) => item.value === country);
      if (!checkbox || !checkbox.checked) throw Error('country control unavailable: ' + country);
      checkbox.click();
    }
    const windowControl = document.getElementById('modeled-context-window');
    const option = [...windowControl.options].find((item) => item.textContent.startsWith('0-100 BP'));
    if (!option) throw Error('source window unavailable');
    windowControl.value = option.value;
    windowControl.dispatchEvent(new Event('change', { bubbles: true }));
    const toggle = document.getElementById('modeled-context-toggle');
    if (toggle.getAttribute('aria-pressed') !== 'true') throw Error('modeled context was not activated');
    return { selected_countries: [...document.querySelectorAll('.country-checkbox')].filter((item) => item.checked).map((item) => item.value).sort(), source_window: windowControl.options[windowControl.selectedIndex].textContent, modeled_toggle_pressed: toggle.getAttribute('aria-pressed') };
  })()`);
  console.log(JSON.stringify({ controls, readiness: await evaluate(cdp, `({ download_disabled: document.getElementById('modeled-context-download').disabled, toggle_pressed: document.getElementById('modeled-context-toggle').getAttribute('aria-pressed'), state: document.getElementById('modeled-context-state').textContent, selected_window: document.getElementById('modeled-context-window').value, errors: document.querySelectorAll('[role="alert"]').length })`) }));
  await until(async () => evaluate(cdp, `!document.getElementById('modeled-context-download').disabled && document.getElementById('modeled-context-state').textContent.includes('visible cells')`), 'export readiness');
  const visibleState = await evaluate(cdp, `document.getElementById('modeled-context-state').textContent`);
  await evaluate(cdp, `document.getElementById('modeled-context-download').click()`);
  const filename = await until(async () => (await readdir(downloads)).find((name) => name.endsWith('.geojson')), 'GeoJSON download');
  const content = await until(async () => {
    try { const bytes = await readFile(join(downloads, filename)); return JSON.parse(bytes.toString()) && bytes; }
    catch { return null; }
  }, 'complete GeoJSON');
  await until(() => cdp.events.find((event) => event.method === 'Browser.downloadProgress' && event.params?.state === 'completed' && event.params?.receivedBytes === content.length), 'completed download event');
  const observation = {
    browser_binary: browserBinary,
    control_state: controls,
    visible_state: visibleState,
    download_filename: filename,
    download_bytes: content.length,
    requests: [...new Set(requests)].sort(),
    download_events: cdp.events.filter((event) => event.method?.startsWith('Browser.download')).map((event) => ({ method: event.method, params: event.params })),
  };
  await writeFile(join(artifact, 'browser-observation.json'), `${JSON.stringify(observation, null, 2)}\n`);
  console.log(JSON.stringify({ artifact, filename, bytes: content.length, controls, visibleState }));
} finally {
  cdp?.close();
  browser.kill();
  server.close();
  await writeFile(join(artifact, 'browser.log'), browserLog);
  if (browser.exitCode === null) await new Promise((ok) => browser.once('exit', ok));
  await rm(profile, { recursive: true, force: true });
}
