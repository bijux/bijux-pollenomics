/** Exact debugger endpoint policy for the local capture browser. */

export function requireLoopbackDebuggerEndpoint(value) {
  const parsed = new URL(value);
  if (
    parsed.protocol !== 'ws:'
    || parsed.hostname !== '127.0.0.1'
    || parsed.port === ''
    || parsed.username !== ''
    || parsed.password !== ''
  ) throw new Error('browser debugger endpoint is not exact loopback');
  return parsed.href;
}

export function requireTargetDebuggerEndpoint(value, debuggerOrigin) {
  const parsed = new URL(value);
  const expected = new URL(debuggerOrigin.href);
  expected.protocol = 'ws:';
  if (
    parsed.protocol !== 'ws:'
    || parsed.hostname !== expected.hostname
    || parsed.port !== expected.port
    || parsed.username !== ''
    || parsed.password !== ''
  ) throw new Error('browser target debugger endpoint differs');
}
