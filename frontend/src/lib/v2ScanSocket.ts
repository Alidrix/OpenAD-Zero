import type {V2ScanEvent} from './v2ScansApi';

type Options={replay?:boolean;onStatus?:(status:'connected'|'disconnected'|'error')=>void};
export function connectScanSocket(scanId:string,onEvent:(event:V2ScanEvent)=>void,options:Options={}){
  const explicit=(import.meta.env.VITE_WS_URL as string|undefined);
  const base=explicit||`${location.protocol==='https:'?'wss':'ws'}://${location.host}`;
  const qs=new URLSearchParams();if(options.replay)qs.set('replay','true');
  const ws=new WebSocket(`${base}/ws/v2/scans/${encodeURIComponent(scanId)}${qs.toString()?`?${qs}`:''}`);
  ws.onopen=()=>options.onStatus?.('connected');
  ws.onmessage=(message)=>{try{onEvent(JSON.parse(message.data) as V2ScanEvent)}catch{undefined}};
  ws.onerror=()=>options.onStatus?.('error');
  ws.onclose=()=>options.onStatus?.('disconnected');
  return {close:()=>ws.close(),socket:ws};
}
