/** Bounded local Git reads used to revalidate the capture candidate. */

import { execFileSync } from 'node:child_process';

export function boundedGit(repositoryRoot, args, timeoutMilliseconds = 30_000) {
  try {
    return execFileSync('git', args, {
      cwd: repositoryRoot,
      encoding: 'utf8',
      timeout: timeoutMilliseconds,
      maxBuffer: 1024 * 1024,
    }).trim();
  } catch (error) {
    throw new Error(`bounded candidate git command failed: ${error.message}`);
  }
}
