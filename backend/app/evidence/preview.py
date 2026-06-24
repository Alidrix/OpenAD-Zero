import json
from pathlib import Path
from app.db.models import Evidence

PREVIEW_EXTENSIONS={'.txt','.log','.json','.jsonl','.xml','.csv','.md'}

def can_preview(evidence: Evidence) -> bool:
    return Path(evidence.stored_path).suffix.lower() in PREVIEW_EXTENSIONS

def build_preview(evidence: Evidence, max_bytes: int) -> dict:
    if not can_preview(evidence):
        return {'available':False,'format':'none','truncated':False,'content':''}
    p=Path(evidence.stored_path)
    data=p.read_bytes()[:max_bytes+1]
    truncated=len(data)>max_bytes
    if truncated: data=data[:max_bytes]
    text=data.decode('utf-8', errors='replace')
    ext=p.suffix.lower(); fmt='text'
    if ext=='.json':
        try:
            text=json.dumps(json.loads(text), indent=2, ensure_ascii=False); fmt='json'
        except Exception: pass
    elif ext=='.jsonl':
        try:
            lines=[json.dumps(json.loads(line), ensure_ascii=False) for line in text.splitlines() if line.strip()]
            text='\n'.join(lines); fmt='jsonl'
        except Exception: pass
    return {'available':True,'format':fmt,'truncated':truncated,'content':text}
