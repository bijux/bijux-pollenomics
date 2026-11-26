// An operation-local byte snapshot; no request reads from the source tree.
import { createHash } from 'node:crypto';

export function captureAssets(input) {
  const files = new Map();
  for (const [name, value] of Object.entries(input)) {
    if (!name || name.startsWith('/') || name.includes('\\') || name.split('/').some(part => !part || part === '.' || part === '..')) throw Error('invalid captured asset path');
    if (!Buffer.isBuffer(value)) throw Error('captured asset must be bytes');
    files.set(name, Buffer.from(value));
  }
  const observed = new Map();
  return Object.freeze({
    names: () => [...files.keys()].sort(),
    read: name => files.has(name) ? Buffer.from(files.get(name)) : null,
    serve: name => {
      if (!name || name.startsWith('/') || name.includes('\\') || name.split('/').some(part => !part || part === '.' || part === '..') || !files.has(name)) return null;
      const bytes = Buffer.from(files.get(name));
      const sha = createHash('sha256').update(bytes).digest('hex');
      if (observed.has(name) && observed.get(name) !== sha) throw Error('captured response identity changed');
      observed.set(name, sha);
      return bytes;
    },
    served: () => Object.fromEntries([...observed].sort()),
  });
}
