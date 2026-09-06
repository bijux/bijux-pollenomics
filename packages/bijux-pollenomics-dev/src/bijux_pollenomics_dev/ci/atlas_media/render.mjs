import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { createWriteStream } from 'node:fs';
import { mkdir, mkdtemp, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { extname, join, normalize, relative, resolve } from 'node:path';

import { boundedGit } from './candidate_git.mjs';
import { requireLoopbackDebuggerEndpoint, requireTargetDebuggerEndpoint } from './debugger_policy.mjs';
import { classifyNetworkRequest } from './network_policy.mjs';
import { validateSnapshot } from './snapshot_policy.mjs';
import { normalizeStaticAssetAuthority, validateStaticAssetPayload } from './static_asset_policy.mjs';

const plan = JSON.parse(await readFile(resolve(process.argv[2]), 'utf8'));
if (plan.schema_version !== 'atlas-media-render-plan.v2') throw new Error('unsupported render plan schema');
if (plan.frame_hash_contract !== 'python-json-sort-keys-utf8-newline.v1') throw new Error('unsupported frame hash contract');
const repositoryRoot = resolve(plan.repository_root);
const artifactRoot = resolve(plan.artifact_root);
const staticRoot = resolve(plan.static_root);
if (staticRoot === artifactRoot || relative(artifactRoot, staticRoot).startsWith('..')) {
  throw new Error('candidate static snapshot escapes artifact root');
}
const timeoutMs = Number(plan.timeout_seconds) * 1000;
const candidate = plan.candidate;
const atlasIdentity = plan.atlas_identity;
if (
  atlasIdentity?.build_id !== candidate.build_id
  || typeof atlasIdentity?.scope_slug !== 'string'
  || atlasIdentity.scope_slug === ''
  || typeof atlasIdentity?.version !== 'string'
  || atlasIdentity.version === ''
) throw new Error('render plan atlas identity is invalid');
if (
  !Array.isArray(plan.allowed_static_paths)
  || plan.allowed_static_paths.length === 0
  || new Set(plan.allowed_static_paths).size !== plan.allowed_static_paths.length
  || plan.allowed_static_paths.some((path) => typeof path !== 'string' || !path.startsWith('/') || path.includes('..'))
) throw new Error('governed static request inventory is invalid');
const allowedStaticPaths = new Set(plan.allowed_static_paths);
const governedStaticAssets = normalizeStaticAssetAuthority(plan.governed_static_assets);
if (
  governedStaticAssets.size !== allowedStaticPaths.size
  || [...governedStaticAssets.keys()].some((path) => !allowedStaticPaths.has(path))
) throw new Error('governed static asset identities differ from request inventory');
if (
  plan.candidate_succession?.product_key !== 'candidate_succession'
  || plan.candidate_succession?.status !== 'refused'
  || plan.candidate_succession?.reason_code !== 'accepted_scientific_classifications_not_available'
  || plan.candidate_succession?.story_count !== 0
  || plan.candidate_succession?.edge_count !== 0
) throw new Error('candidate succession refusal posture differs');
assertCandidate();
const server = createServer(async (request, response) => {
  const requestUrl = new URL(request.url, 'http://127.0.0.1');
  if (request.method !== 'GET' || !allowedStaticPaths.has(requestUrl.pathname) || requestUrl.search !== '') {
    response.writeHead(403).end('forbidden');
    return;
  }
  const requestedPath = resolve(staticRoot, `.${normalize(decodeURIComponent(requestUrl.pathname))}`);
  if (relative(staticRoot, requestedPath).startsWith('..')) {
    response.writeHead(403).end('forbidden');
    return;
  }
  try {
    const canonicalPath = await realpath(requestedPath);
    if (relative(staticRoot, canonicalPath).startsWith('..')) {
      response.writeHead(403).end('forbidden');
      return;
    }
    const payload = await readFile(canonicalPath);
    validateStaticAssetPayload(governedStaticAssets.get(requestUrl.pathname), payload);
    response.writeHead(200, {
      'Cache-Control': 'no-store',
      'Content-Security-Policy': "connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'",
      'Content-Length': payload.length,
      'Content-Type': {
        '.css': 'text/css; charset=utf-8',
        '.html': 'text/html; charset=utf-8',
        '.js': 'text/javascript; charset=utf-8',
        '.json': 'application/json',
        '.png': 'image/png',
      }[extname(canonicalPath)] || 'application/octet-stream',
    });
    response.end(payload);
  } catch {
    response.writeHead(404).end('not found');
  }
});
await new Promise((accept, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', accept);
});
const serverPort = server.address().port;
const networkAuthority = {
  scheme: 'http',
  host: '127.0.0.1',
  port: serverPort,
  origin: `http://127.0.0.1:${serverPort}`,
  allowedPaths: allowedStaticPaths,
};
const profileRoot = await mkdtemp(join(artifactRoot, 'brave-profile-'));
const browserLog = createWriteStream(join(artifactRoot, 'brave-browser.log'), { flags: 'wx' });
const browser = spawn(plan.browser_binary, [
  '--headless=new', '--disable-gpu', '--disable-background-networking',
  '--disable-component-update', '--disable-default-apps', '--no-default-browser-check',
  '--disable-extensions', '--disable-sync', '--metrics-recording-only',
  '--disable-quic', '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
  '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1',
  '--no-first-run', '--remote-allow-origins=*', '--remote-debugging-port=0',
  `--user-data-dir=${profileRoot}`, 'about:blank',
], { stdio: ['ignore', 'pipe', 'pipe'] });
browser.stdout.pipe(browserLog, { end: false });
browser.stderr.pipe(browserLog, { end: false });

const networkRequests = [];
const observedNetworkRequests = [];
const rejectedNetworkRequests = [];
const pendingNetworkActions = new Set();
try {
  const browserWebSocket = requireLoopbackDebuggerEndpoint(await debuggerEndpoint(browser, timeoutMs));
  const debuggerOrigin = new URL(browserWebSocket);
  debuggerOrigin.protocol = 'http:';
  debuggerOrigin.pathname = '';
  debuggerOrigin.search = '';
  debuggerOrigin.hash = '';
  const response = await boundedFetch(`${debuggerOrigin.origin}/json/new?about:blank`, {
    method: 'PUT',
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!response.ok) throw new Error(`cannot create browser target: ${response.status}`);
  const target = await response.json();
  requireTargetDebuggerEndpoint(target.webSocketDebuggerUrl, debuggerOrigin);
  const cdp = await connectCdp(target.webSocketDebuggerUrl, timeoutMs);
  const runtimeFailures = [];
  cdp.onEvent((event) => {
    if (event.method === 'Runtime.exceptionThrown') runtimeFailures.push(event.params.exceptionDetails?.text || 'runtime exception');
    if (event.method === 'Runtime.consoleAPICalled' && event.params.type === 'error') {
      runtimeFailures.push((event.params.args || []).map((arg) => arg.description || arg.value || '').join(' '));
    }
    if (event.method === 'Fetch.requestPaused') {
      const classified = classifyNetworkRequest(event.params, networkAuthority);
      networkRequests.push(classified.receipt);
      observedNetworkRequests.push({ ...classified.receipt, url: event.params.request.url });
      if (!classified.allowed) rejectedNetworkRequests.push(classified.receipt);
      const action = cdp.send(
        classified.allowed ? 'Fetch.continueRequest' : 'Fetch.failRequest',
        classified.allowed
          ? { requestId: event.params.requestId }
          : { requestId: event.params.requestId, errorReason: 'BlockedByClient' },
      );
      pendingNetworkActions.add(action);
      action.then(
        () => pendingNetworkActions.delete(action),
        (error) => {
          pendingNetworkActions.delete(action);
          runtimeFailures.push(`network enforcement failed: ${error.message}`);
        },
      );
    }
  });
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
  await cdp.send('Network.setBlockedURLs', {
    urls: ['ws://*', 'wss://*', 'ftp://*', 'file://*'],
  });
  await cdp.send('Fetch.enable', {
    patterns: [{ urlPattern: '*', requestStage: 'Request' }],
    handleAuthRequests: false,
  });
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: plan.viewport.width, height: plan.viewport.height, deviceScaleFactor: 1, mobile: false,
  });
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
  const loaded = cdp.waitFor('Page.loadEventFired', timeoutMs);
  await cdp.send('Page.navigate', {
    url: `http://127.0.0.1:${serverPort}/${plan.atlas_document}#basemap=none`,
  });
  await loaded;
  const initial = await captureReady(cdp);
  if (initial.build_id !== candidate.build_id) throw new Error('atlas build differs before capture');
  const storyReceipts = [];
  for (const story of plan.stories) {
    const frameRoot = join(artifactRoot, 'frames', story.story_id);
    await mkdir(frameRoot, { recursive: true });
    const frameReceipts = [];
    for (const [ordinal, plannedFrame] of story.frames.entries()) {
      const frame = plannedFrame.capture;
      if (!/^[a-f0-9]{64}$/.test(String(plannedFrame.canonical_sha256 || ''))) {
        throw new Error(`canonical frame SHA-256 is invalid: ${story.story_id}`);
      }
      if (frame.ordinal !== ordinal) throw new Error(`non-contiguous frame ordinal: ${story.story_id}`);
      const snapshot = await evaluate(cdp, `(async () => {
        const api = globalThis.BijuxPollenomicsAtlasCapture;
        let timer;
        try {
          const timeout = new Promise((_, reject) => {
            timer = setTimeout(
              () => reject(new Error('atlas frame application timed out')),
              ${timeoutMs},
            );
          });
          return await Promise.race([api.applyFrame(${JSON.stringify(frame)}), timeout]);
        } finally {
          clearTimeout(timer);
        }
      })()`);
      validateSnapshot(snapshot, frame, story, atlasIdentity);
      const expectedVisible = story.expected_visible_feature_counts?.[ordinal] ?? null;
      if (
        frame.story_kind === 'source_chronology'
        && snapshot.visible_source_chronology_point_count !== expectedVisible
      ) {
        throw new Error(`captured source frame visibility differs from governed atlas assets: ${story.story_id}/${ordinal}`);
      }
      const screenshot = await cdp.send('Page.captureScreenshot', {
        format: 'png', captureBeyondViewport: false, fromSurface: true,
      });
      const payload = Buffer.from(screenshot.data, 'base64');
      const file = `${String(ordinal).padStart(6, '0')}.png`;
      await writeFile(join(frameRoot, file), payload, { flag: 'wx' });
      frameReceipts.push({
        ordinal,
        frame_sha256: plannedFrame.canonical_sha256,
        png_sha256: digest(payload),
        byte_count: payload.length,
        file: `frames/${story.story_id}/${file}`,
        capture_api_version: snapshot.capture_api_version,
        ready: snapshot.ready,
        build_id: snapshot.build_id,
        scope_slug: snapshot.scope_slug,
        version: snapshot.version,
        classifications_status: snapshot.scientific_posture.classifications_status,
        classifications_reason_code: snapshot.scientific_posture.classifications_reason_code,
        observation_chronology_is_propagation: snapshot.scientific_posture.observation_chronology_is_propagation,
        visible_governed_candidate_count: snapshot.visible_governed_candidate_count,
        time_start_bp: frame.time_start_bp,
        time_end_bp: frame.time_end_bp,
        node_count: snapshot.source_chronology?.facet_node_count ?? null,
        observation_denominator: snapshot.source_chronology?.facet_observation_denominator ?? null,
        feature_count: snapshot.modeled_context?.feature_count ?? null,
        source_level: snapshot.source_chronology?.level ?? null,
        source_code: snapshot.source_chronology?.source_code ?? null,
        source_taxon: snapshot.source_chronology?.source_taxon ?? null,
        source_window_label: snapshot.modeled_context?.window_label ?? null,
        metric_family_key: snapshot.modeled_context?.metric_family_key ?? null,
        metric_key: snapshot.modeled_context?.metric_key ?? null,
        visible_point_count: snapshot.visible_point_count,
        visible_polygon_layer_count: snapshot.visible_polygon_layer_count,
        visible_feature_count: snapshot.visible_point_count + snapshot.visible_polygon_layer_count,
        visible_source_chronology_point_count: snapshot.visible_source_chronology_point_count,
        visible_modeled_context_feature_count: snapshot.visible_modeled_context_feature_count,
      });
    }
    if (
      story.evidence_role === 'observation_chronology'
      && !frameReceipts.some((frame) => frame.visible_source_chronology_point_count > 0)
    ) {
      throw new Error(`source story rendered no selected-layer evidence: ${story.story_id}`);
    }
    storyReceipts.push({
      story_id: story.story_id,
      evidence_role: story.evidence_role,
      selector: story.selector,
      node_count: story.node_count,
      observation_denominator: story.observation_denominator,
      frame_feature_denominators: story.frame_feature_denominators,
      expected_visible_feature_counts: story.expected_visible_feature_counts,
      source_authority_sha256: story.source_authority_sha256,
      frame_count: frameReceipts.length,
      frames: frameReceipts,
    });
  }
  await Promise.all([...pendingNetworkActions]);
  if (rejectedNetworkRequests.length) {
    throw new Error(`capture denied non-local requests: ${JSON.stringify(rejectedNetworkRequests)}`);
  }
  if (runtimeFailures.length) throw new Error(`browser runtime failures: ${runtimeFailures.join(' | ')}`);
  const navigationEvidence = requireExactNavigation(observedNetworkRequests, serverPort, plan.atlas_document);
  const closeResponse = await boundedFetch(`${debuggerOrigin.origin}/json/close/${target.id}`, {
    signal: AbortSignal.timeout(timeoutMs),
  });
  if (!closeResponse.ok) throw new Error(`cannot close browser target: ${closeResponse.status}`);
  await Promise.all([...pendingNetworkActions]);
  cdp.close();
  networkRequests.sort((left, right) => JSON.stringify(left).localeCompare(JSON.stringify(right)));
  assertCandidate();
  const receipt = {
    schema_version: 'atlas-media-capture-receipt.v2',
    candidate,
    atlas_identity: atlasIdentity,
    capture_api_version: 'atlas-capture.v1',
    basemap: 'none',
    temporal_direction: 'oldest_to_present',
    interpolation_allowed: false,
    frame_hash_contract: plan.frame_hash_contract,
    candidate_succession: plan.candidate_succession,
    network_policy: 'deny-before-send-governed-origin-data-blob-only.v2',
    governed_static_assets: plan.governed_static_assets,
    network_authority: {
      scheme: networkAuthority.scheme,
      host: networkAuthority.host,
      port: networkAuthority.port,
      origin: networkAuthority.origin,
      allowed_static_paths: plan.allowed_static_paths,
    },
    network_request_count: networkRequests.length,
    network_requests: networkRequests,
    navigation_evidence: navigationEvidence,
    stories: storyReceipts,
  };
  await writeFile(join(artifactRoot, 'capture-receipt.json'), `${JSON.stringify(receipt, null, 2)}\n`, { flag: 'wx' });
} catch (error) {
  if (rejectedNetworkRequests.length) {
    const rejection = {
      schema_version: 'atlas-media-network-rejection.v1',
      policy: 'deny-before-send-governed-origin-data-blob-only.v2',
      candidate,
      rejected_request_count: rejectedNetworkRequests.length,
      rejected_requests: rejectedNetworkRequests,
    };
    await writeFile(
      join(artifactRoot, 'network-rejection-receipt.json'),
      `${JSON.stringify(rejection, null, 2)}\n`,
      { flag: 'wx' },
    );
  }
  throw error;
} finally {
  browser.kill('SIGTERM');
  await Promise.race([
    new Promise((accept) => browser.once('exit', accept)),
    new Promise((accept) => setTimeout(accept, 4000)),
  ]);
  if (browser.exitCode === null) {
    browser.kill('SIGKILL');
    await Promise.race([
      new Promise((accept) => browser.once('exit', accept)),
      new Promise((_, reject) => setTimeout(() => reject(new Error('browser kill timed out')), timeoutMs)),
    ]);
  }
  server.closeAllConnections();
  await Promise.race([
    new Promise((accept, reject) => server.close((error) => error ? reject(error) : accept())),
    new Promise((_, reject) => setTimeout(() => reject(new Error('local atlas server close timed out')), timeoutMs)),
  ]);
  await Promise.race([
    new Promise((accept, reject) => {
      browserLog.once('error', reject);
      browserLog.end(accept);
    }),
    new Promise((_, reject) => setTimeout(() => reject(new Error('browser log close timed out')), timeoutMs)),
  ]);
  await rm(profileRoot, { recursive: true, force: true });
}

function requireExactNavigation(requests, port, documentPath) {
  const expectedPath = `/${documentPath}`;
  const matches = requests.filter((request) => {
    try {
      const parsed = new URL(request.url);
      return request.method === 'GET'
        && request.resource_type === 'Document'
        && parsed.protocol === 'http:'
        && parsed.hostname === '127.0.0.1'
        && parsed.port === String(port)
        && parsed.pathname === expectedPath;
    } catch {
      return false;
    }
  });
  if (matches.length !== 1) throw new Error('capture requires exactly one governed loopback navigation');
  return {
    request_count: 1,
    method: 'GET',
    resource_type: 'Document',
    scheme: 'http',
    host: '127.0.0.1',
    port,
    path: expectedPath,
    query: '',
  };
}

async function boundedFetch(url, options) {
  try {
    return await fetch(url, options);
  } catch (error) {
    throw new Error(`bounded local browser request failed: ${error.message}`);
  }
}

function digest(payload) {
  return createHash('sha256').update(payload).digest('hex');
}

function assertCandidate() {
  const head = git('rev-parse', 'HEAD');
  const tree = git('rev-parse', 'HEAD^{tree}');
  const atlasCommit = git('log', '-1', '--format=%H', '--', plan.atlas_document);
  if (head !== candidate.repository_head || tree !== candidate.repository_tree || atlasCommit !== candidate.atlas_output_commit) {
    throw new Error('candidate identity changed or differs from the render plan');
  }
  if (git('status', '--porcelain=v1', '--untracked-files=no')) {
    throw new Error('tracked worktree changes make the candidate mutable');
  }
}

function git(...args) {
  return boundedGit(repositoryRoot, args);
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

function connectCdp(url, waitMilliseconds) {
  return new Promise((accept, reject) => {
    const socket = new WebSocket(url);
    const openTimeout = setTimeout(() => {
      socket.close();
      reject(new Error('CDP WebSocket open timed out'));
    }, waitMilliseconds);
    let nextId = 0;
    const pending = new Map();
    const listeners = new Set();
    const waiters = new Map();
    socket.addEventListener('error', (error) => {
      clearTimeout(openTimeout);
      reject(error);
    }, { once: true });
    socket.addEventListener('open', () => {
      clearTimeout(openTimeout);
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
          return new Promise((resolveRequest, rejectRequest) => {
            const timeout = setTimeout(() => {
              pending.delete(id);
              rejectRequest(new Error(`${method} timed out`));
            }, waitMilliseconds);
            pending.set(id, {
              resolve(value) { clearTimeout(timeout); resolveRequest(value); },
              reject(error) { clearTimeout(timeout); rejectRequest(error); },
            });
          });
        },
        waitFor(method, waitMilliseconds) {
          return new Promise((resolveEvent, rejectEvent) => {
            const timeout = setTimeout(() => rejectEvent(new Error(`${method} timed out`)), waitMilliseconds);
            const resolveEventOnce = (value) => { clearTimeout(timeout); resolveEvent(value); };
            waiters.set(method, [...(waiters.get(method) || []), { resolve: resolveEventOnce }]);
          });
        },
        onEvent(listener) { listeners.add(listener); },
        close() {
          for (const waiter of pending.values()) waiter.reject(new Error('CDP connection closed'));
          pending.clear();
          socket.close();
        },
      });
    });
  });
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

async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
