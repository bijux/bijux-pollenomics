import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { readFile, mkdir, readdir, rm, writeFile } from 'node:fs/promises';
import { basename, dirname, extname, join, relative, resolve } from 'node:path';
import { debuggerEndpoint, launchChromium } from '../browser-transport.mjs';

const [repositoryArg, artifactArg, browserBinary] = process.argv.slice(2);
if (!repositoryArg || !artifactArg || !browserBinary) throw new Error('repository, artifact directory, and browser binary are required');
const repository = resolve(repositoryArg);
const artifact = resolve(artifactArg);
const site = resolve(repository, 'docs/report');
if (!relative(repository, artifact).startsWith('artifacts/')) throw new Error('output must be under repository artifacts');
await mkdir(dirname(artifact), { recursive: true });
await mkdir(artifact, { recursive: false });
const downloads = join(artifact, 'downloads');
const profile = join(artifact, 'browser-profile');
await mkdir(downloads);
await mkdir(profile);
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
let browserLog = '';
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
function captureBrowserIdentity(version) {
  for (const key of ['product', 'revision', 'userAgent', 'jsVersion', 'protocolVersion']) {
    if (typeof version?.[key] !== 'string' || !version[key].trim()) throw Error('Browser identity field unavailable: '+key);
  }
  return version;
}
async function captureSourceIdentity(repository, runtime) {
  const document = 'docs/report/regions/nordic/nordic_map.html';
  const paths = [document, 'docs/report/regions/nordic/nordic_map_assets.json'];
  for (const row of [runtime, ...Object.values(runtime.optional_controllers || {})]) {
    if (typeof row.path !== 'string' || basename(row.path) !== row.path) throw Error('Unconfined runtime identity path');
    paths.push(join(dirname(document), row.path));
  }
  const files = [];
  for (const path of paths.sort()) {
    const content = await readFile(join(repository, path));
    files.push({path,bytes:content.length,sha256:createHash('sha256').update(content).digest('hex')});
  }
  const git = ref => execFileSync('git', ['--no-optional-locks', '--no-replace-objects', 'rev-parse', ref], {cwd:repository,timeout:5000}).toString().trim();
  return {head:git('HEAD'),tree:git('HEAD^{tree}'),files};
}
let cdp, runtime, captureError;
try {
  runtime = await launchChromium(browserBinary, profile, [
    '--disable-extensions', '--disable-sync',
    '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
  ]);
  runtime.browser.stdout.on('data', (part) => { browserLog += part.toString(); });
  runtime.browser.stderr.on('data', (part) => { browserLog += part.toString(); });
  const debuggerUrl = await debuggerEndpoint(runtime.browser, timeout);
  const debuggerOrigin = new URL(debuggerUrl);
  debuggerOrigin.protocol = 'http:';
  const targetResponse = await fetch(`${debuggerOrigin.origin}/json/new?about:blank`, { method: 'PUT' });
  if (!targetResponse.ok) throw new Error(`target creation: ${targetResponse.status}`);
  const target = await targetResponse.json();
  cdp = await connect(target.webSocketDebuggerUrl);
  const browserIdentity = captureBrowserIdentity(await cdp.send('Browser.getVersion'));
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
  const runtimeBinding = await evaluate(cdp, `JSON.parse(document.getElementById('atlas-static-bootstrap').textContent).runtime`);
  const candidate = await captureSourceIdentity(repository, runtimeBinding);
  const observation = {
    browser_binary: browserBinary,
    browser_runtime: browserIdentity,
    candidate,
    control_state: controls,
    visible_state: visibleState,
    download_filename: filename,
    download_bytes: content.length,
    requests: [...new Set(requests)].sort(),
    download_events: cdp.events.filter((event) => event.method?.startsWith('Browser.download')).map((event) => ({ method: event.method, params: event.params })),
  };
  await writeFile(join(artifact, 'browser-observation.json'), `${JSON.stringify(observation, null, 2)}\n`);
  console.log(JSON.stringify({ artifact, filename, bytes: content.length, controls, visibleState }));
} catch (error) {
  captureError = error;
} finally {
  const cleanupErrors = [];
  for (const [name, cleanup] of [
    ['CDP', async () => cdp?.close()],
    ['browser', async () => runtime?.close()],
    ['server', () => new Promise((accept, reject) => {
      const timer = setTimeout(() => reject(Error('Capture server close deadline exceeded')), 2000);
      server.close(error => {clearTimeout(timer); if (error) reject(error); else accept();});
      server.closeAllConnections();
    })],
    ['browser log', () => writeFile(join(artifact, 'browser.log'), browserLog)],
    ['profile', () => rm(profile, {recursive:true, force:true, maxRetries:5, retryDelay:50})],
  ]) {
    try {await cleanup();} catch (error) {cleanupErrors.push({name, error});}
  }
  if (captureError !== undefined) {
    for (const {name, error} of cleanupErrors) console.error(`LandClim capture cleanup also failed (${name}): ${error}`);
  } else if (cleanupErrors.length) {
    throw new AggregateError(cleanupErrors.map(({error}) => error), 'LandClim capture cleanup failed');
  }
}
if (captureError !== undefined) throw captureError;
