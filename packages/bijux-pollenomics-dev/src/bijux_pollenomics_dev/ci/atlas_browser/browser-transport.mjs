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
  const started=performance.now(), elapsed=()=>performance.now()-started;
  const fs = await import('node:fs/promises'), {constants} = await import('node:fs');
  await mkdir(output, {recursive:false});
  const receipt={status:'FAIL', scope:'Chromium startup/CDP only; no site, page or scientific qualification',
    clock:'monotonic milliseconds since probe entry', milestones:{started:0},
    readiness_budgets:{endpoint_ms:15000,primary_work_ms:30000,late_tail_ms:0,whole_cleanup_bound:'not_claimed'},
    node:{executable:process.execPath,version:process.version,platform:process.platform,architecture:process.arch},
    requested_binary:binary, observations:{}, cleanup:{}, cleanup_errors:[]};
  const logs=[]; let size=0, retained=0, runtime, profile, cdp, timer, primary, acquisition, initialProcess;
  const failure=(where,error)=>{
    receipt.status='FAIL';
    if(!primary){primary=error;receipt.error=String(error);receipt.primary_error={where,error:String(error)};}
    else receipt.cleanup_errors.push({where,error:String(error)});
  };
  // These observation budgets do not bound the independent launcher cleanup.
  const observe=async(work,milliseconds=200)=>{
    let timeout;
    try{return await Promise.race([
      Promise.resolve().then(work).then(value=>({status:'available',...value}),error=>({status:'unavailable',error:String(error),code:error.code??null})),
      new Promise(accept=>{timeout=setTimeout(()=>accept({status:'unavailable',reason:'observation_deadline',budget_ms:milliseconds}),milliseconds);}),
    ]);}finally{clearTimeout(timeout);}
  };
  const directory=path=>observe(async()=>{
    const info=await fs.lstat(path);
    if(!info.isDirectory() || info.isSymbolicLink())return {path,type:info.isSymbolicLink()?'symlink':'not_directory',mode:info.mode&0o777,access:'not_attempted'};
    let access='read_write_search';
    try{await fs.access(path,constants.R_OK|constants.W_OK|constants.X_OK);}catch(error){access=String(error);}
    return {path,type:'directory',mode:info.mode&0o777,access};
  });
  const boundedFile=async(path)=>{
    if(!Number.isInteger(constants.O_NOFOLLOW) || !Number.isInteger(constants.O_NONBLOCK))throw Error('Safe nonblocking file observation is unsupported');
    const file=await fs.open(path,constants.O_RDONLY|constants.O_NOFOLLOW|constants.O_NONBLOCK);
    try{
      const info=await file.stat();
      if(!info.isFile())return {path,type:'not_regular',bytes:info.size};
      if(info.size>4096)return {path,type:'regular',bytes:info.size,content:'not_read_over_budget'};
      const bytes=Buffer.alloc(4096), read=await file.read(bytes,0,bytes.length,0), after=await file.stat();
      return {path,type:'regular',bytes:after.size,read_bytes:read.bytesRead,changed_size:info.size!==after.size,
        text:new TextDecoder('utf-8',{fatal:true}).decode(bytes.subarray(0,read.bytesRead))};
    }finally{await file.close();}
  };
  const port=()=>observe(async()=>{
    const path=join(profile,'DevToolsActivePort'), info=await fs.lstat(path);
    if(info.isSymbolicLink())return {path,type:'symlink',content:'not_read'};
    if(!info.isFile())return {path,type:'not_regular',content:'not_read'};
    const value=await boundedFile(path);
    if(value.text!==undefined){value.lines=value.text.split(/\r?\n/).slice(0,2);delete value.text;}
    return value;
  });
  const ownedProcess=()=>observe(async()=>{
    if(process.platform!=='linux' || !runtime?.browser.pid)return {status:'unavailable',platform:process.platform,identity:'not_available'};
    if(receipt.process.exit_observed || runtime.browser.exitCode!==null || runtime.browser.signalCode!==null)return {identity:'not_available',reason:'child_already_exited'};
    const value=await boundedFile(`/proc/${runtime.browser.pid}/stat`);
    if(receipt.process.exit_observed || runtime.browser.exitCode!==null || runtime.browser.signalCode!==null)throw Error('Owned child exited during process observation');
    if(value.text===undefined || value.read_bytes===4096)throw Error('Owned Linux process stat unavailable or exceeds budget');
    const end=value.text.lastIndexOf(')'), fields=value.text.slice(end+2).trim().split(/\s+/);
    const pid=Number(value.text.slice(0,value.text.indexOf('(')).trim()), start_ticks=fields[19], state=fields[0];
    if(pid!==runtime.browser.pid || !/^\d+$/.test(start_ticks??'') || !/^[A-Za-z]$/.test(state??''))throw Error('Invalid owned Linux process identity');
    return {pid,start_ticks,state};
  });
  const snapshot=async(initial=false)=>{
    const processObservation=initial ? await ownedProcess() : initialProcess?.start_ticks ? await ownedProcess() : {status:'unavailable',reason:'initial_linux_identity_unavailable'};
    if(initial)initialProcess=processObservation.status==='available'?processObservation:null;
    else if(processObservation.status==='available' && (processObservation.pid!==initialProcess.pid || processObservation.start_ticks!==initialProcess.start_ticks)){
      processObservation.status='unavailable';processObservation.reason='owned_pid_start_mismatch';delete processObservation.state;
    }
    const [profileObservation,ipcObservation,portObservation]=await Promise.all([directory(profile),directory(runtime.directory),port()]);
    return {at_ms:elapsed(),process:processObservation,profile:profileObservation,ipc:ipcObservation,devtools_active_port:portObservation};
  };
  try {
    receipt.resolved_binary=await observe(async()=>({path:await fs.realpath(binary)}));
    profile=await mkdtemp(join(output,'browser-profile-'));
    receipt.milestones.launch_requested=elapsed();
    runtime=await launchChromium(binary,profile);
    receipt.milestones.acquired=elapsed();receipt.ipc_directory=runtime.directory;
    const browser=runtime.browser;
    receipt.process={pid:browser.pid??null,spawnfile:browser.spawnfile,spawnargs:browser.spawnargs,spawn_observed:false,exit_observed:false,close_observed:false};
    browser.once('spawn',()=>{receipt.process.spawn_observed=true;receipt.milestones.spawn=elapsed();});
    browser.on('error',error=>{receipt.process.error=String(error);receipt.milestones.process_error=elapsed();});
    browser.once('exit',(code,signal)=>{receipt.process.exit_observed=true;receipt.process.exit={code,signal};receipt.milestones.exit=elapsed();});
    browser.once('close',(code,signal)=>{receipt.process.close_observed=true;receipt.process.close={code,signal};receipt.milestones.close=elapsed();});
    const capture=chunk=>{
      receipt.milestones.first_output??=elapsed();size+=chunk.length;
      const accepted=chunk.subarray(0,Math.max(0,1048576-retained));
      if(accepted.length){logs.push(Buffer.from(accepted));retained+=accepted.length;}
      if(size>1048576)browser.kill('SIGTERM');
    };
    browser.stdout.on('data',capture);browser.stderr.on('data',capture);
    // Start the readiness listener before asynchronous observations.
    const work=Promise.race([(async()=>{
      receipt.milestones.endpoint_wait_started=elapsed();
      const endpoint=await debuggerEndpoint(browser,15000);
      receipt.milestones.endpoint_observed=elapsed();
      cdp=await connectCdp(endpoint);receipt.browser=await cdp.send('Browser.getVersion');
      if(!receipt.browser.product)throw Error('Chromium CDP version is empty');
    })(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Error('Chromium startup deadline exceeded')),30000);})]);
    acquisition=snapshot(true);
    await work;
    if(size>1048576)throw Error('Chromium startup log exceeds budget');
    receipt.status='PASS';
  } catch(error) {
    failure('primary_work',error);receipt.milestones.primary_failure=elapsed();
    if(runtime){
      if(acquisition)receipt.observations.acquisition=await acquisition;
      receipt.observations.failure=await snapshot();
    }
  } finally {
    clearTimeout(timer);
    if(acquisition && !receipt.observations.acquisition)receipt.observations.acquisition=await acquisition;
    try{cdp?.close();}catch(error){failure('cdp_close',error);}
    receipt.milestones.cleanup_requested=elapsed();
    if(runtime){
      receipt.cleanup.runtime_close='requested';
      try{await runtime.close();receipt.cleanup.runtime_close='fulfilled';}catch(error){receipt.cleanup.runtime_close='rejected';failure('runtime_close',error);}
    }else receipt.cleanup.runtime_close='not_acquired';
    if(profile){try{await rm(profile,{recursive:true,force:true,maxRetries:5,retryDelay:50});receipt.cleanup.profile_remove='fulfilled';}catch(error){receipt.cleanup.profile_remove='rejected';failure('profile_remove',error);}}
    const absent=path=>observe(async()=>{try{const info=await fs.lstat(path);return {removed:false,type:info.isSymbolicLink()?'symlink':info.isDirectory()?'directory':'other'};}catch(error){if(error.code==='ENOENT')return {removed:true};throw error;}});
    receipt.cleanup.profile=profile?await absent(profile):{status:'available',removed:true,reason:'not_created'};
    receipt.cleanup.ipc=runtime?await absent(runtime.directory):{status:'available',removed:true,reason:'not_acquired'};
    receipt.ipc_removed=receipt.cleanup.ipc.status==='available'?receipt.cleanup.ipc.removed:null;
    receipt.cleanup.process_group_absence='not_independently_observed';
    if(runtime)receipt.process.final={exitCode:runtime.browser.exitCode,signalCode:runtime.browser.signalCode};
    receipt.milestones.cleanup_finished=elapsed();
    receipt.logs={observed_bytes:size,retained_bytes:retained,truncated:size>retained,budget_bytes:1048576};
    receipt.log_write=await observe(async()=>{await writeFile(join(output,'browser.log'),Buffer.concat(logs));return {bytes:retained};},1000);
    if(receipt.log_write.status!=='available')failure('browser_log_write',Error(JSON.stringify(receipt.log_write)));
    const saved=await observe(async()=>{await writeFile(join(output,'startup.json'),JSON.stringify(receipt,null,2)+'\n');return {written:true};},1000);
    if(saved.status!=='available')failure('startup_receipt_write',Error(JSON.stringify(saved)));
  }
  if(receipt.status!=='PASS'){
    const error=primary instanceof Error?primary:Error(receipt.error??'Chromium startup failed');
    if(receipt.cleanup_errors.length)error.cleanup_errors=receipt.cleanup_errors;
    throw error;
  }
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
