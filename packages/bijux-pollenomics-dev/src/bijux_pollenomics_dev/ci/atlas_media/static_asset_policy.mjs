import { createHash } from 'node:crypto';

export function normalizeStaticAssetAuthority(rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    throw new Error('governed static asset authority is absent');
  }
  const authority = new Map();
  for (const row of rows) {
    if (
      !row
      || typeof row.path !== 'string'
      || !row.path.startsWith('/')
      || row.path.includes('..')
      || !Number.isInteger(row.byte_count)
      || row.byte_count < 0
      || !/^[a-f0-9]{64}$/.test(String(row.sha256 || ''))
      || authority.has(row.path)
    ) throw new Error('governed static asset authority is invalid');
    authority.set(row.path, row);
  }
  return authority;
}

export function validateStaticAssetPayload(expected, payload) {
  if (!expected) throw new Error('static asset path is not governed');
  if (!Buffer.isBuffer(payload)) throw new Error('static asset payload is invalid');
  const digest = createHash('sha256').update(payload).digest('hex');
  if (payload.length !== expected.byte_count || digest !== expected.sha256) {
    throw new Error('static asset bytes differ from candidate authority');
  }
}
