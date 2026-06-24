from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
SEV={'info','low','medium','high','critical'}
@dataclass
class NucleiParsedFinding:
    template_id:str; template_name:str; severity:str; type:str; matcher_name:str|None; matched_at:str|None; host:str|None; ip:str|None; port:int|None; description:str; tags:list[str]; references:list[str]; extracted_results:list[str]; raw_json:dict
    def to_dict(self): return asdict(self)

def _list(v):
    if v is None: return []
    if isinstance(v,list): return v
    if isinstance(v,str): return [x.strip() for x in v.split(',') if x.strip()]
    return [str(v)]

def parse_nuclei_jsonl(path: Path) -> list[NucleiParsedFinding]:
    if not path.exists() or not path.read_text(errors='ignore').strip(): return []
    out=[]
    for line in path.read_text(errors='ignore').splitlines():
        try: raw=json.loads(line)
        except json.JSONDecodeError: continue
        info=raw.get('info') or {}
        sev=str(info.get('severity') or raw.get('severity') or 'info').lower()
        if sev not in SEV: sev='info'
        port=raw.get('port')
        try: port=int(port) if port is not None else None
        except Exception: port=None
        out.append(NucleiParsedFinding(
            template_id=str(raw.get('template-id') or raw.get('template_id') or 'unknown'),
            template_name=str(info.get('name') or raw.get('template-name') or raw.get('template_id') or raw.get('template-id') or 'Nuclei finding'),
            severity=sev,type=str(raw.get('type') or 'http'), matcher_name=raw.get('matcher-name') or raw.get('matcher_name'),
            matched_at=raw.get('matched-at') or raw.get('matched_at'), host=raw.get('host'), ip=raw.get('ip'), port=port,
            description=str(info.get('description') or ''), tags=_list(info.get('tags') or raw.get('tags')), references=_list(info.get('reference') or info.get('references') or raw.get('reference')), extracted_results=_list(raw.get('extracted-results') or raw.get('extracted_results')), raw_json=raw))
    return out
