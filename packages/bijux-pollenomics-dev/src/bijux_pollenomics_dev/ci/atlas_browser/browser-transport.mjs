import {spawn} from 'node:child_process';
import {mkdtemp, mkdir, realpath, rm, stat, writeFile} from 'node:fs/promises';
import {join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

// Chromium's transient UNIX sockets need a shorter path than artifact storage.
export function requireChromiumSocketPath(directory) {
  const socket = join(directory, 'com.google.Chrome.XXXXXX', 'SingletonSocket');
  if (Buffer.byteLength(socket) >= 104) throw Error('Chromium IPC path exceeds UNIX socket budget');
  return socket;
}

export async function launchChromium(binary, profile, additionalArguments = []) {
  const directory = await mkdtemp(join(await realpath('/tmp'), 'bjx-'));
  let browser, closing, closed;
  const signalGroup = signal => {
    if (!browser?.pid) return;
    try {process.kill(-browser.pid, signal);} catch(error) {if(error.code !== 'ESRCH') throw error;}
  };
  const close = () => closing ??= (async () => {
    process.off('SIGTERM', terminate); process.off('SIGINT', interrupt);
    try {
      signalGroup('SIGTERM');
      if (browser?.pid) {
        let timer;
        await Promise.race([closed, new Promise(accept=>{timer=setTimeout(accept,1000);})]);
        clearTimeout(timer);
        signalGroup('SIGKILL');
        await closed;
      }
    } finally {await rm(directory, {recursive:true, force:true, maxRetries:5, retryDelay:50});}
  })();
  const terminate = () => {void close().finally(()=>process.exit(143));};
  const interrupt = () => {void close().finally(()=>process.exit(130));};
  try {
    requireChromiumSocketPath(directory);
    if(typeof profile!=='string' || resolve(profile)!==profile || !(await stat(profile)).isDirectory())throw Error('Owned Chromium profile directory required');
    if (((await stat(directory)).mode & 0o777) !== 0o700) throw Error('Chromium IPC directory is not private');
    browser = spawn(binary, ['--headless=new', '--disable-gpu', '--disable-background-networking', '--disable-component-update', '--disable-default-apps', '--no-default-browser-check', '--no-first-run', '--remote-allow-origins=*', '--remote-debugging-port=0', ...additionalArguments, `--user-data-dir=${profile}`, 'about:blank'], {
      env:{...process.env, TMPDIR:directory, TMP:directory, TEMP:directory},
      detached:true, stdio:['ignore','pipe','pipe'],
    });
    closed = new Promise(accept=>browser.once('close',accept));
    process.once('SIGTERM', terminate); process.once('SIGINT', interrupt);
    return {browser, directory, close};
  } catch(error) {await close(); throw error;}
}

export async function probeChromium(binary, output) {
  await mkdir(output, {recursive:false});
  const receipt = {status:'FAIL', scope:'Chromium startup/CDP only; no site, page or scientific qualification'};
  const logs=[]; let size=0, runtime, profile, cdp, timer;
  try {
    profile = await mkdtemp(join(output,'browser-profile-'));
    runtime = await launchChromium(binary, profile);
    receipt.ipc_directory=runtime.directory;
    const capture=chunk=>{size+=chunk.length;if(size<=1048576)logs.push(chunk);else runtime.browser.kill('SIGTERM');};
    runtime.browser.stdout.on('data',capture);runtime.browser.stderr.on('data',capture);
    await Promise.race([(async()=>{
      const endpoint = await debuggerEndpoint(runtime.browser,15000);
      cdp=await connectCdp(endpoint);
      receipt.browser=await cdp.send('Browser.getVersion');
      if(!receipt.browser.product)throw Error('Chromium CDP version is empty');
      receipt.status='PASS';
    })(), new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Chromium startup deadline exceeded')),30000);})]);
    if(size>1048576)throw Error('Chromium startup log exceeds budget');
  } catch(error) {receipt.status='FAIL';receipt.error=String(error);}
  finally {
    clearTimeout(timer);cdp?.close();
    if(runtime)try{await runtime.close();}catch(error){receipt.status='FAIL';receipt.error=`Chromium cleanup failed: ${error}`;}
    if(profile)await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:50});
    receipt.ipc_removed=runtime ? await stat(runtime.directory).then(()=>false,error=>{if(error.code==='ENOENT')return true;throw error;}) : true;
    await writeFile(join(output,'startup.json'),JSON.stringify(receipt,null,2)+'\n');
    await writeFile(join(output,'browser.log'),Buffer.concat(logs).subarray(0,1048576));
  }
  if(receipt.status!=='PASS')throw Error(receipt.error);
  return receipt;
}

export function debuggerEndpoint(process, waitMilliseconds) {
  return new Promise((accept, reject) => {
    let buffer = '';
    const cleanup = () => {clearTimeout(timeout);process.stdout.off('data',inspect);process.stderr.off('data',inspect);process.off('exit',exited);process.off('error',failed);};
    const failed = error => {cleanup();reject(error);};
    const exited = code => failed(Error(`browser exited before debugger readiness: ${code}`));
    const inspect = chunk => {
      buffer = (buffer+chunk.toString()).slice(-65536);
      const match=buffer.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if(match){cleanup();accept(match[1]);}
    };
    const timeout=setTimeout(()=>failed(Error('browser did not publish a debugger endpoint')),waitMilliseconds);
    process.stdout.on('data',inspect);process.stderr.on('data',inspect);
    process.once('exit',exited);process.once('error',failed);
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

if(process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length!==5 || process.argv[2]!=='--probe')throw Error('usage: node browser-transport.mjs --probe BROWSER OUTPUT');
  await probeChromium(process.argv[3],process.argv[4]);
}
