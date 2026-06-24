from pathlib import Path
import re
try:
    import yaml
except Exception:
    yaml=None
from .errors import BloodHoundError

PACK_DIR=Path(__file__).parent/'query_packs'
WRITE_RE=re.compile(r'\b(CREATE|MERGE|SET|DELETE|REMOVE|DROP|CALL\s+dbms|LOAD\s+CSV)\b',re.I)
class QueryCatalogError(BloodHoundError): pass
class QueryCatalog:
    def __init__(self,pack_dir:Path=PACK_DIR):
        self.pack_dir=pack_dir; self.queries={}; self.load()
    def load(self):
        self.queries={}
        for p in sorted(self.pack_dir.glob('*.yml')):
            data=yaml.safe_load(p.read_text()) if yaml else []
            for q in data or []:
                if not q.get('read_only') or WRITE_RE.search(q.get('cypher','')): raise QueryCatalogError(f'Unsafe query {q.get("id")}')
                self.queries[q['id']]=q
    def list_public(self):
        return [{k:q.get(k) for k in ['id','name','description','risk_level','read_only','parameters']} for q in self.queries.values()]
    def get(self,qid):
        if qid not in self.queries: raise QueryCatalogError(f'Unknown query_id {qid}')
        return self.queries[qid]
    def render(self,qid,params:dict):
        q=self.get(qid); clean={}
        for spec in q.get('parameters',[]):
            n=spec['name']; required=spec.get('required',True)
            if required and n not in params: raise QueryCatalogError(f'Missing parameter {n}')
            if n not in params: continue
            v=params[n]
            if spec.get('type')=='integer':
                v=int(v); 
                if 'min' in spec: v=max(v,int(spec['min']))
                if 'max' in spec: v=min(v,int(spec['max']))
            elif spec.get('type')=='list':
                v=v if isinstance(v,list) else [x for x in str(v).split(',') if x]
                allowed=spec.get('allowed')
                if allowed: v=[x for x in v if x in allowed]
            else: v=str(v)
            clean[n]=v
        cypher=q['cypher']
        for k,v in clean.items(): cypher=cypher.replace('{{'+k+'}}', str(v if not isinstance(v,list) else v))
        return q, clean, cypher
