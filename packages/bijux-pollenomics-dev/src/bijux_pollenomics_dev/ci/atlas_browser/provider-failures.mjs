// Deterministic provider replies: every intercepted tile is answered locally.
const PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR4nGNgAAIAAAUAAXpeqz8AAAAASUVORK5CYII=';
export const PROVIDER_FAILURE_CASES = Object.freeze([
  {name: 'http-401', status: 401},
  {name: 'http-403', status: 403},
  {name: 'http-404', status: 404},
  {name: 'http-429', status: 429},
  {name: 'http-429-retry-after', status: 429, retryAfter: '1'},
  {name: 'timeout', errorReason: 'TimedOut'},
  {name: 'aborted', errorReason: 'Aborted'},
  {name: 'offline', errorReason: 'InternetDisconnected', both: true},
  {name: 'corrupt-image', corrupt: true},
  {name: 'dual-provider', status: 503, both: true},
]);

export function providerReply(urlText, failure) {
  const url = new URL(urlText);
  if (!['tile.openstreetmap.org', 'tile.opentopomap.org'].includes(url.hostname)
      || url.protocol !== 'https:' || url.search || url.username || url.password) {
    throw Error('unexpected provider URL or credentials');
  }
  const affected = url.hostname === 'tile.openstreetmap.org' || failure.both === true;
  if (affected && failure.errorReason) return {method: 'Fetch.failRequest', params: {errorReason: failure.errorReason}};
  const status = affected ? failure.status ?? 200 : 200;
  const headers = [{name: 'Content-Type', value: 'image/png'}, {name: 'Cache-Control', value: 'no-store'}];
  if (affected && failure.retryAfter) headers.push({name: 'Retry-After', value: failure.retryAfter});
  return {
    method: 'Fetch.fulfillRequest',
    params: {
      responseCode: status,
      responseHeaders: headers,
      body: affected && (failure.corrupt || status !== 200)
        ? Buffer.from(status === 200 ? 'invalid PNG bytes' : `Provider returned HTTP ${status}`).toString('base64') : PNG,
    },
  };
}

export function providerInterception(cdp, providerRequests, runtimeFailures, enabled, failure = null) {
  const pending = new Set(), canceled = new Set(), rejected = [];
  let requestsBlocked = false, acceptingReplies = true, wakeDrain = null;
  const notifyDrain = () => { if (wakeDrain) wakeDrain(); };
  return {
    get requestsBlocked() { return requestsBlocked; },
    handle(event) {
      // Network.requestWillBeSent is appended by the caller after dispatch.
      queueMicrotask(notifyDrain);
      if (event.method === 'Network.loadingFailed' && event.params.canceled === true) canceled.add(event.params.requestId);
      if (event.method === 'Network.loadingFailed') {
        const row = providerRequests.find(item => item.request_id === event.params.requestId && !item.intercepted);
        if (row && failure?.name === 'offline') row.offline_blocked = event.params.errorText === 'net::ERR_INTERNET_DISCONNECTED';
        if (row && event.params.errorText === 'net::ERR_BLOCKED_BY_CLIENT') row.blocked_during_teardown = true;
        if (row && event.params.canceled === true && event.params.errorText === 'net::ERR_ABORTED') {
          row.observed_cancellation = {canceled: true, error_text: event.params.errorText};
        }
      }
      if (event.method !== 'Fetch.requestPaused') return;
      const row = {
        url: event.params.request.url, request_id: event.params.requestId,
        network_id: event.params.networkId ?? null, intercepted: true,
        elapsed_ms: performance.now(),
      };
      providerRequests.push(row);
      if (!acceptingReplies) {
        // Keep late pauses suspended until the owned target is closed; never
        // send a reply after interception teardown has begun.
        row.interception_status = 'held_until_target_close';
        return;
      }
      let reply;
      try {
        if (Object.keys(event.params.request.headers || {}).some(key => /authorization|api[-_]?key|token/i.test(key))) {
          throw Error('provider request carries credential headers');
        }
        reply = failure ? providerReply(row.url, failure)
          : {method: 'Fetch.failRequest', params: {errorReason: 'Failed'}};
      } catch (error) {
        runtimeFailures.push({kind: 'provider-policy', detail: String(error)});
        reply = {method: 'Fetch.failRequest', params: {errorReason: 'BlockedByClient'}};
      }
      row.response = reply.params;
      const operation = cdp.send(reply.method, {requestId: row.request_id, ...reply.params})
        .catch(error => rejected.push({row, error})).finally(() => { pending.delete(operation); notifyDrain(); });
      pending.add(operation);
    },
    async settle(closeTarget) {
      if (typeof closeTarget !== 'function') throw Error('owned target close callback is required');
      if (enabled) {
        // Keep interception enabled: disabling it resumes paused requests.
        // Block new traffic, drain issued replies and close the owned target.
        await cdp.send('Network.setBlockedURLs', {urls: [
          '*://tile.openstreetmap.org/*', '*://*.tile.openstreetmap.org/*',
          '*://tile.opentopomap.org/*', '*://*.tile.opentopomap.org/*',
        ]});
        requestsBlocked = true;
        await cdp.send('Page.stopLoading');
        const deadline = performance.now() + 5000;
        while (pending.size || !providerAttemptFacts(providerRequests).all_locally_handled) {
          const remaining = deadline - performance.now();
          if (remaining <= 0) {
            runtimeFailures.push({kind: 'provider-drain', detail: 'provider transactions did not reach observed pairing/blocking/cancellation before target closure'});
            break;
          }
          await new Promise(resolve => {
            const timer = setTimeout(() => { wakeDrain = null; resolve(); }, remaining);
            wakeDrain = () => { clearTimeout(timer); wakeDrain = null; resolve(); };
          });
        }
        acceptingReplies = false;
      } else {
        while (pending.size) await Promise.all([...pending]);
      }
      await closeTarget();
      for (const row of providerRequests) {
        if (row.interception_status === 'held_until_target_close') row.interception_status = 'target_closed_without_response';
      }
      for (const {row, error} of rejected.splice(0)) {
        let protocolError;
        try { protocolError = JSON.parse(error.message); } catch { protocolError = null; }
        const staleCanceledRequest = protocolError?.code === -32602
          && ['Invalid InterceptionId', 'Invalid InterceptionId.'].includes(protocolError.message)
          && typeof row.network_id === 'string' && canceled.has(row.network_id);
        row.interception_status = staleCanceledRequest ? 'canceled_before_failure_reply' : 'failed';
        row.interception_error = String(error);
        if (!staleCanceledRequest) runtimeFailures.push({
          kind: 'provider-interception', detail: String(error), request_id: row.request_id, network_id: row.network_id,
        });
      }
    },
  };
}

export function providerAttemptFacts(requests) {
  const transactions = new Map();
  for (const row of requests.filter(row => row.intercepted || row.offline_blocked)) {
    const identity = row.network_id ?? row.request_id;
    if (!transactions.has(identity) || row.intercepted) transactions.set(identity, row);
  }
  const attempts = [...transactions.values()];
  const counts = Object.fromEntries(['tile.openstreetmap.org', 'tile.opentopomap.org'].map(host => [host,
    attempts.filter(row => new URL(row.url).hostname === host).length]));
  const duplicateUrls = attempts.filter((row, index) => attempts.findIndex(other => other.url === row.url) !== index).map(row => row.url);
  return {counts, duplicate_urls: duplicateUrls,
    bounded: attempts.length > 0 && attempts.length <= 128 && duplicateUrls.length === 0,
    all_locally_handled: requests.filter(row => !row.intercepted).every(row => row.offline_blocked || row.blocked_during_teardown
      || (row.observed_cancellation?.canceled === true && row.observed_cancellation.error_text === 'net::ERR_ABORTED')
      || attempts.some(other => other.network_id === row.request_id)),
  };
}

export const PROVIDER_MATRIX_ASSERTIONS = Object.freeze([
  'provider_matrix_case_complete', 'provider_matrix_candidate_identity',
  'provider_matrix_configured_fallback', 'provider_matrix_evidence_unchanged',
  'provider_matrix_bounded_attempts', 'provider_matrix_no_live_requests',
  'provider_matrix_credential_free', 'provider_matrix_ui_usable',
  'provider_matrix_runtime_clean', 'provider_matrix_payload_unchanged',
]);

export async function verifyProviderFailureMatrix(scope, debuggerOrigin, helpers) {
  const {openAtlas, closeAtlas, captureReady, evaluate, screenshot, writeScenario,
    evidenceIdentity, candidate, timeoutMs} = helpers;
  const scenarios = [], receipts = [];
  for (const failure of PROVIDER_FAILURE_CASES) {
    const name = `provider-${failure.name}`;
    const atlas = await openAtlas(scope, debuggerOrigin, {
      name, blockProviders: true, providerFailure: failure, hash: '#basemap=none',
    });
    const result = {scope: scope.name, name, failure,
      assertions: Object.fromEntries(PROVIDER_MATRIX_ASSERTIONS.map(key => [key, false]))};
    try {
      const before = await captureReady(atlas.cdp);
      result.baseline_snapshot = before;
      const payloadBefore = await evaluate(atlas.cdp, `(${providerPayloadIdentity.toString()})()`);
      result.scientific_payload_manifest_sha256 = payloadBefore;
      await evaluate(atlas.cdp, `(() => {
        const api = BijuxPollenomicsAtlasCapture;
        const rows = [], failureCounts = [];
        const record = () => {
          const row = {basemap: api.snapshot().basemap,
            readout: document.getElementById('basemap-readout').textContent,
            elapsed_ms: performance.now()};
          if (!rows.length || row.readout !== rows.at(-1).readout) rows.push(row);
        };
        globalThis.providerFailureObservation = {rows, failureCounts, observer: new MutationObserver(mutations => {
          for (const mutation of mutations) for (const node of mutation.removedNodes) {
            const match = /^(street|terrain) tile failure ([0-9]+)\\/([0-9]+)/.exec(node.textContent || '');
            if (match) failureCounts.push({provider: match[1], count: Number(match[2]), threshold: Number(match[3])});
          }
          record();
        })};
        providerFailureObservation.observer.observe(document.getElementById('basemap-readout'),
          {childList: true, characterData: true, subtree: true});
        record();
      })()`);
      if (failure.name === 'offline') await atlas.cdp.send('Network.emulateNetworkConditions', {
        offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0,
      });
      await evaluate(atlas.cdp, `document.querySelector('[data-basemap="street"]').click()`);
      const observation = await evaluate(atlas.cdp, `(() => new Promise(resolve => {
        const started = performance.now(), expected = ${JSON.stringify(failure.both ? 'none' : 'terrain')};
        const inspect = () => {
          const snapshot = BijuxPollenomicsAtlasCapture.snapshot();
          const readout = document.getElementById('basemap-readout').textContent;
          const complete = (${providerTerminal.toString()})(snapshot, readout, expected);
          if (complete || performance.now() - started >= ${timeoutMs}) {
            providerFailureObservation.observer.disconnect();
            resolve({snapshot, readout, transitions: providerFailureObservation.rows, failure_counts: providerFailureObservation.failureCounts,
              elapsed_ms: performance.now() - started, timed_out: !complete});
          } else setTimeout(inspect, 25);
        };
        inspect();
      }))()`);
      if (failure.name === 'offline') await atlas.cdp.send('Network.emulateNetworkConditions', {
        offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1,
      });
      const attempts = providerAttemptFacts(atlas.providerRequests);
      const initialRequests = atlas.providerRequests.map(row => ({...row}));
      Object.assign(result, {observation, attempts, provider_requests: initialRequests});
      const ui = await evaluate(atlas.cdp, `(${providerUiJourney.toString()})()`);
      await screenshot(atlas.cdp, `${scope.name}/${name}.png`);
      receipts.push(`${scope.name}/${name}.png`);
      const payloadAfter = await evaluate(atlas.cdp, `(${providerPayloadIdentity.toString()})()`);
      const credentialFree = await evaluate(atlas.cdp, `!${credentialPattern.toString()}.test(document.documentElement.outerHTML)`);
      const primary = initialRequests.filter(row => (row.intercepted || row.offline_blocked) && new URL(row.url).hostname === 'tile.openstreetmap.org');
      const fallback = initialRequests.filter(row => (row.intercepted || row.offline_blocked) && new URL(row.url).hostname === 'tile.opentopomap.org');
      Object.assign(result, {
        scope: scope.name, name, failure, baseline_snapshot: before, observation,
        provider_requests: initialRequests, attempts, ui,
        browser_offline_applied: failure.name === 'offline',
        assertions: {
          provider_matrix_case_complete: !observation.timed_out,
          provider_matrix_candidate_identity: before.build_id === candidate.build_id && observation.snapshot.build_id === candidate.build_id,
          provider_matrix_configured_fallback: primary.length >= 3
            && (failure.name === 'offline' || fallback.length >= (failure.both ? 3 : 1))
            && observation.snapshot.basemap === (failure.both ? 'none' : 'terrain')
            && observation.failure_counts.every(row => row.threshold === 3 && row.count >= 1 && row.count <= 3)
            && observation.failure_counts.some(row => row.provider === 'street' && row.count === 3)
            && (!failure.both || observation.failure_counts.some(row => row.provider === 'terrain' && row.count === 3))
            && observation.transitions.some(row => /street unavailable/.test(row.readout))
            && (failure.both ? /no-basemap mode active/.test(observation.readout) : /terrain available/.test(observation.readout)),
          provider_matrix_evidence_unchanged: JSON.stringify(evidenceIdentity(before)) === JSON.stringify(evidenceIdentity(observation.snapshot)),
          provider_matrix_bounded_attempts: attempts.bounded && observation.elapsed_ms < timeoutMs,
          provider_matrix_no_live_requests: attempts.all_locally_handled,
          provider_matrix_credential_free: credentialFree && !credentialPattern.test(JSON.stringify(initialRequests)),
          provider_matrix_ui_usable: Object.values(ui).every(value => value === true),
          provider_matrix_payload_unchanged: payloadBefore === payloadAfter,
        },
      });
    } catch (error) {
      result.error = String(error.stack || error);
    } finally {
      // A real offline session must not survive even a failed assertion/journey.
      if (failure.name === 'offline') await atlas.cdp.send('Network.emulateNetworkConditions', {
        offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1,
      });
      await closeAtlas(atlas, debuggerOrigin);
    }
    result.final_provider_requests = atlas.providerRequests;
    result.final_request_policy = providerAttemptFacts(atlas.providerRequests);
    result.assertions.provider_matrix_no_live_requests = result.final_request_policy.all_locally_handled;
    result.assertions.provider_matrix_credential_free &&= !credentialPattern.test(JSON.stringify(atlas.providerRequests));
    result.runtime_failures = atlas.runtimeFailures;
    result.assertions.provider_matrix_runtime_clean = atlas.runtimeFailures.length === 0;
    result.assertions.provider_matrix_credential_free &&= !credentialPattern.test(JSON.stringify(atlas.runtimeFailures));
    await writeScenario(scope, result, receipts);
    scenarios.push(result);
  }
  return {scenarios, receipts};
}

const credentialPattern = /[?&](?:api[_-]?key|access[_-]?token|token)=|(?:Authorization|Proxy-Authorization)\s*:\s*(?:Bearer|Basic)\s+\S+/i;

export async function providerUiJourney() {
  const api = BijuxPollenomicsAtlasCapture;
  const before = await api.awaitReady();
  const legend = document.getElementById('legend-toggle');
  const initialLegend = legend.getAttribute('aria-expanded');
  legend.click();
  const legendChanged = legend.getAttribute('aria-expanded') !== initialLegend;
  legend.click();
  const checkbox = document.querySelector('.country-checkbox:checked');
  if (!checkbox) throw Error('no selected country filter');
  const country = checkbox.value;
  checkbox.click();
  const filtered = await api.awaitReady();
  const currentCheckbox = [...document.querySelectorAll('.country-checkbox')].find(row => row.value === country);
  if (!currentCheckbox || currentCheckbox.checked) throw Error('country filter did not render its unchecked state');
  currentCheckbox.click();
  const restored = await api.awaitReady();
  let slider = document.getElementById('time-start-slider');
  let originalPreset = null, movementBaseline = before;
  if (Number(slider.min) === Number(slider.max)) {
    const presets = [...document.querySelectorAll('[data-time-interval]')];
    originalPreset = presets.find(button => button.classList.contains('is-active'))?.dataset.timeInterval;
    const finite = presets.find(button => button.dataset.timeInterval === '1000');
    if (!originalPreset || !finite) throw Error('full-span time controls lack original/finite preset');
    finite.click();
    movementBaseline = await api.awaitReady();
    slider = document.getElementById('time-start-slider');
    if (Number(slider.min) === Number(slider.max)) throw Error('finite time preset did not enable movement');
  }
  const original = slider.value;
  slider.value = Number(original) === Number(slider.min) ? slider.max : slider.min;
  slider.dispatchEvent(new Event('input', {bubbles: true}));
  const moved = await api.awaitReady();
  slider.value = original;
  slider.dispatchEvent(new Event('input', {bubbles: true}));
  await api.awaitReady();
  if (originalPreset !== null) {
    const restorePreset = [...document.querySelectorAll('[data-time-interval]')]
      .find(button => button.dataset.timeInterval === originalPreset);
    if (!restorePreset) throw Error('original time preset disappeared');
    restorePreset.click();
    await api.awaitReady();
    slider = document.getElementById('time-start-slider');
    slider.value = String(before.time_window_bp.younger_bp);
    slider.dispatchEvent(new Event('input', {bubbles: true}));
  }
  const timeRestored = await api.awaitReady();
  document.getElementById('search-toggle').click();
  const input = document.getElementById('search-input');
  input.value = 'a';
  input.dispatchEvent(new Event('input', {bubbles: true}));
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const record = document.querySelector('[data-search-index]');
  if (record) record.click();
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  const popup = document.getElementById('focus-card');
  const popupUsable = Boolean(record && !popup.hidden && document.getElementById('focus-title').textContent.trim());
  document.getElementById('focus-close').click();
  return {
    legend_toggles_and_restores: legendChanged && legend.getAttribute('aria-expanded') === initialLegend,
    country_filter_changes: JSON.stringify(filtered.countries) !== JSON.stringify(before.countries),
    country_filter_restores: JSON.stringify(restored.countries) === JSON.stringify(before.countries),
    time_control_changes: JSON.stringify(moved.time_window_bp) !== JSON.stringify(movementBaseline.time_window_bp),
    time_control_restores: JSON.stringify(timeRestored.time_window_bp) === JSON.stringify(before.time_window_bp),
    counts_restore: timeRestored.visible_point_count === before.visible_point_count
      && timeRestored.visible_governed_candidate_count === before.visible_governed_candidate_count,
    popup_opens_and_closes: popupUsable && popup.hidden,
    evidence_rendered: Boolean(document.querySelector('.leaflet-point-pane canvas, .leaflet-point-pane path, .leaflet-marker-pane .leaflet-marker-icon')),
  };
}


async function providerPayloadIdentity() {
  // Reuse the existing scientific asset manifest, whose payload digests and SRI
  // are enforced by the map loader, rather than pinning the page's prose/code.
  const source = document.getElementById('atlas-static-bootstrap')?.textContent;
  if (!source || !JSON.parse(source).build_id) throw Error('scientific payload manifest is unavailable');
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(source));
  return [...new Uint8Array(bytes)].map(value => value.toString(16).padStart(2, '0')).join('');
}


export function providerTerminal(snapshot, readout, expected) {
  return snapshot.basemap === expected && (expected === 'terrain'
    ? readout.trim() === 'terrain available'
    : readout.includes('no-basemap mode active'));
}
