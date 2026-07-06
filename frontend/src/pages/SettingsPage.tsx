import {useEffect,useState} from 'react';
import {ApiError,health,dbHealth,redisHealth,toolHealth,workerHealth,getCapabilitiesConfig,getVersion,authStatus,type AuthStatus,type VersionInfo} from '../lib/api';
import {clearApiToken,getApiToken,setApiToken} from '../lib/auth';

const value = (v:any) => v === undefined || v === null || v === '' ? 'unavailable' : String(v);
const available = (ok:boolean|undefined) => ok ? 'available' : 'unavailable';

export function SettingsPage(){
  const [theme,setTheme]=useState(localStorage.theme||'dark');
  const [api,setApi]=useState<any>({status:'checking'});
  const [db,setDb]=useState<any>();
  const [redis,setRedis]=useState<any>();
  const [tools,setTools]=useState<any>();
  const [worker,setWorker]=useState<any>();
  const [cfg,setCfg]=useState<any>();
  const [version,setVersion]=useState<VersionInfo|null>(null);
  const [versionUnavailable,setVersionUnavailable]=useState(false);
  const [auth,setAuth]=useState<AuthStatus|null>(null);
  const [tokenDraft,setTokenDraft]=useState('');
  const [tokenConfigured,setTokenConfigured]=useState(Boolean(getApiToken()));
  const [authMessage,setAuthMessage]=useState('');
  useEffect(()=>{document.documentElement.classList.toggle('dark',theme==='dark');localStorage.theme=theme},[theme]);
  useEffect(()=>{
    health().then(setApi).catch(()=>setApi({status:'unreachable'}));
    dbHealth().then(setDb).catch(()=>setDb({status:'unavailable'}));
    redisHealth().then(setRedis).catch(()=>setRedis({status:'unavailable'}));
    toolHealth().then(setTools).catch(()=>setTools({error:'unreachable'}));
    workerHealth().then(setWorker).catch(()=>setWorker({redis_available:false,queues:{}}));
    getCapabilitiesConfig().then(setCfg).catch(()=>setCfg(undefined));
    getVersion().then(setVersion).catch(()=>setVersionUnavailable(true));
    authStatus().then(setAuth).catch(()=>setAuth(null));
  },[]);
  return <div className='card max-w-3xl'>
    <h1 className='text-3xl font-bold'>Settings</h1>
    <h2 className='mt-5 font-bold'>Application Version</h2>
    {version?<div className='mt-2 grid gap-2 md:grid-cols-3'><p>Name: <b>{version.name}</b></p><p>Version: <b>{version.version}</b></p><p>Release stage: <b>{version.release_stage}</b></p></div>:<p className='mt-2 text-amber-400'>{versionUnavailable?'Version unavailable':'Loading version...'}</p>}

    <h2 className='mt-5 font-bold'>Local API authentication</h2>
    <p className='text-sm text-slate-500'>Store an API bearer token locally in this browser. The saved token is never displayed after saving.</p>
    <div className='mt-3 grid gap-3'>
      <p>Backend auth: <b>{auth?.auth_enabled?'enabled':'disabled or unavailable'}</b></p>
      <p>Localhost bypass: <b>{auth?.localhost_bypass_enabled?'enabled':'disabled or unavailable'}</b></p>
      <p>Backend token configured: <b>{auth?.token_configured?'yes':'no or unavailable'}</b></p>
      <p>Browser token: <b>{tokenConfigured?'Token configured locally':'No local token configured'}</b></p>
      <input className='input' type='password' value={tokenDraft} placeholder='Paste local API token' onChange={(event)=>setTokenDraft(event.target.value)} autoComplete='off' />
      <div className='flex flex-wrap gap-2'>
        <button className='btn' onClick={()=>{setApiToken(tokenDraft);setTokenDraft('');setTokenConfigured(Boolean(getApiToken()));setAuthMessage('Token saved locally.')}}>Save token</button>
        <button className='btn' onClick={()=>{clearApiToken();setTokenDraft('');setTokenConfigured(false);setAuthMessage('Local token cleared.')}}>Clear token</button>
        <button className='btn' onClick={()=>{health().then(()=>setAuthMessage('Health check succeeded.')).catch((error)=>setAuthMessage(error instanceof ApiError&&error.status===401?'Health check returned 401 Unauthorized.':'Health check failed.'))}}>Test health</button>
      </div>
      {authMessage&&<p className='text-sm text-slate-400'>{authMessage}</p>}
    </div>
    <h2 className='mt-5 font-bold'>System Health</h2>
    <div className='mt-2 grid gap-2 md:grid-cols-2'>
      <p>API health: <b>{value(api.status)}</b></p>
      <p>DB health: <b>{value(db?.status)}</b></p>
      <p>Redis health: <b>{value(redis?.status)}</b></p>
      <p>Worker Redis: <b>{available(worker?.redis_available)}</b></p>
      <p>Queue openadzero-default: <b>{value(worker?.queues?.['openadzero-default'])}</b></p>
      <p>Queue openadzero-scans: <b>{value(worker?.queues?.['openadzero-scans'])}</b></p>
      <p>Nmap: <b>{available(tools?.nmap?.available)}</b> {tools?.nmap?.version}</p>
      <p>NetExec: <b>{available(tools?.netexec?.available)}</b> {tools?.netexec?.version}</p>
      <p>Nuclei: <b>{available(tools?.nuclei?.available)}</b> {tools?.nuclei?.version}</p>
      <p>BloodHound enabled/configured: <b>{String(Boolean(tools?.bloodhound?.enabled))}/{String(Boolean(tools?.bloodhound?.configured))}</b></p>
    </div>
    {tools?.error&&<p className='text-amber-400'>Tool health unavailable.</p>}
    <h2 className='mt-5 font-bold'>Execution Modes & Feature Flags</h2>
    <p className='text-sm text-slate-500'>These values are controlled by backend environment variables.</p>
    {cfg?<div className='mt-2 grid gap-2 md:grid-cols-2'><p>Default mode: <b>{cfg.default_mode}</b></p><p>Assisted mode enabled: <b>{String(cfg.assisted_mode_enabled)}</b></p><p>CTF/Lab mode enabled: <b>{String(cfg.ctf_lab_mode_enabled)}</b></p><p>Manual action cards enabled: <b>{String(cfg.manual_action_cards_enabled)}</b></p><p>External evidence import enabled: <b>{String(cfg.external_evidence_import_enabled)}</b></p><p>Reporting enabled: <b>{String(cfg.reporting_enabled)}</b></p><p>AI planner enabled: <b>{String(cfg.ai_planner_enabled)}</b></p><p>Advanced automation enabled: <b>{String(cfg.advanced_automation_enabled)}</b></p>{!cfg.ctf_lab_mode_enabled&&<p className='text-amber-400'>CTF/Lab Mode is disabled by configuration.</p>}</div>:<p>Capability configuration unavailable.</p>}
    <button className='btn mt-4' onClick={()=>setTheme(theme==='dark'?'light':'dark')}>Basculer thème {theme}</button>
    <p className='mt-4 text-slate-500'>Nuclei and NetExec are limited to safe, backend-allowlisted workflows with human approval where required.</p>
  </div>
}
