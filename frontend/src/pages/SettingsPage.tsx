import {useEffect,useState} from 'react';
import {health,dbHealth,redisHealth,toolHealth,workerHealth,getCapabilitiesConfig} from '../lib/api';

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
  useEffect(()=>{document.documentElement.classList.toggle('dark',theme==='dark');localStorage.theme=theme},[theme]);
  useEffect(()=>{
    health().then(setApi).catch(()=>setApi({status:'unreachable'}));
    dbHealth().then(setDb).catch(()=>setDb({status:'unavailable'}));
    redisHealth().then(setRedis).catch(()=>setRedis({status:'unavailable'}));
    toolHealth().then(setTools).catch(()=>setTools({error:'unreachable'}));
    workerHealth().then(setWorker).catch(()=>setWorker({redis_available:false,queues:{}}));
    getCapabilitiesConfig().then(setCfg).catch(()=>setCfg(undefined));
  },[]);
  return <div className='card max-w-3xl'>
    <h1 className='text-3xl font-bold'>Settings</h1>
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
