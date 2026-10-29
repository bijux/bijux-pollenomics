// Selection waiters have separate lifetimes from reusable static cache requests.
let staticAtlasSelectionController = null;
function beginStaticAtlasSelection(required) {
  staticAtlasSelectionController?.abort();
  staticAtlasSelectionController = new AbortController();
  const needed = new Set(required.map((row) => row.asset_key));
  for (const [key, operation] of staticAtlasInFlightAssets) {
    if (operation.controller && !operation.retained && !needed.has(key)) {
      // Remove before abort completion so A → B → A can start a fresh A request.
      staticAtlasInFlightAssets.delete(key);
      operation.controller.abort();
    }
  }
  return staticAtlasSelectionController.signal;
}
function waitForStaticAtlasSelection(promise, signal) {
  return new Promise((resolve, reject) => {
    const cancelled = () => reject(signal.reason);
    signal.addEventListener('abort', cancelled, { once: true });
    if (signal.aborted) cancelled();
    promise.then((value) => {
      signal.removeEventListener('abort', cancelled);
      if (signal.aborted) reject(signal.reason);
      else resolve(value);
    }, (error) => {
      signal.removeEventListener('abort', cancelled);
      reject(signal.aborted ? signal.reason : error);
    });
  });
}
async function fetchStaticAtlasNodeAsset(row, signal) {
  const response = await fetch(`./${row.path}`, {
    signal, integrity: row.integrity, credentials: 'same-origin',
  });
  signal.throwIfAborted();
  if (!response.ok) staticAtlasFailure(`${row.asset_key} request failed`);
  const text = await response.text();
  signal.throwIfAborted();
  if (new TextEncoder().encode(text).byteLength !== row.byte_count) staticAtlasFailure(`${row.asset_key} script byte count mismatch`);
  if (await staticAtlasSha256(text) !== row.sha256) staticAtlasFailure(`${row.asset_key} script integrity mismatch`);
  signal.throwIfAborted();
  // This is the exact publisher's data envelope, never JavaScript evaluation.
  const prefix = 'globalThis.__BIJUX_ATLAS_RAW_CHUNKS__=globalThis.__BIJUX_ATLAS_RAW_CHUNKS__||[];globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push(';
  if (!text.startsWith(prefix) || !text.endsWith(');\n')) staticAtlasFailure(`${row.asset_key} registration wrapper is invalid`);
  let envelope;
  try {
    envelope = JSON.parse(text.slice(prefix.length, -3));
  } catch (error) {
    staticAtlasFailure(`${row.asset_key} registration JSON is invalid`);
  }
  if (!envelope || typeof envelope !== 'object' || Array.isArray(envelope)) staticAtlasFailure(`${row.asset_key} registration envelope is invalid`);
  await consumeStaticAtlasAsset(row, signal, envelope);
}
