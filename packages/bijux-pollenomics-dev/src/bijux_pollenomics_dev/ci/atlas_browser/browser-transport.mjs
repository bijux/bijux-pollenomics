export function debuggerEndpoint(process, waitMilliseconds) {
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

export function connectCdp(url) {
  return new Promise((accept, reject) => {
    const socket = new WebSocket(url);
    let nextId = 0;
    const pending = new Map();
    const listeners = new Set();
    const waiters = new Map();
    socket.addEventListener('error', reject, { once: true });
    socket.addEventListener('open', () => {
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
          return new Promise((resolveRequest, rejectRequest) => pending.set(id, { resolve: resolveRequest, reject: rejectRequest }));
        },
        waitFor(method, waitMilliseconds) {
          return new Promise((resolveEvent, rejectEvent) => {
            const timeout = setTimeout(() => rejectEvent(new Error(`${method} timed out`)), waitMilliseconds);
            const resolve = (value) => { clearTimeout(timeout); resolveEvent(value); };
            waiters.set(method, [...(waiters.get(method) || []), { resolve, reject: rejectEvent }]);
          });
        },
        onEvent(listener) { listeners.add(listener); },
        close() { socket.close(); },
      });
    });
  });
}

export async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
