import httpx
from app.core.config import get_settings
from .errors import BloodHoundError
class BloodHoundUnavailable(BloodHoundError): pass
class BloodHoundAuthError(BloodHoundError): pass
class BloodHoundNotFound(BloodHoundError): pass
class BloodHoundRateLimited(BloodHoundError): pass
class BloodHoundClient:
    def __init__(self): self.s=get_settings()
    def _headers(self): return {'Authorization':f'Bearer {self.s.bloodhound_api_token}'} if self.s.bloodhound_api_token else {}
    def status(self):
        if not self.s.bloodhound_enabled: return {'status':'disabled','enabled':False,'base_url':self.s.bloodhound_base_url}
        return {'status':'enabled','enabled':True,'base_url':self.s.bloodhound_base_url}
    async def ping(self):
        if not self.s.bloodhound_enabled: return False
        try:
            async with httpx.AsyncClient(timeout=5,verify=self.s.bloodhound_verify_tls) as c:
                r=await c.get(f'{self.s.bloodhound_base_url.rstrip("/")}/api/v2/health',headers=self._headers())
                return r.status_code < 500
        except httpx.HTTPError: return False
    async def upload_zip(self,path):
        async with httpx.AsyncClient(timeout=self.s.bloodhound_ingest_timeout, verify=self.s.bloodhound_verify_tls) as c:
            with open(path,'rb') as f:
                r=await c.post(f'{self.s.bloodhound_base_url.rstrip("/")}/api/v2/file-upload/start', headers=self._headers(), files={'file':('sharphound.zip',f,'application/zip')})
            r.raise_for_status(); return r.json() if r.content else {'status_code':r.status_code}
    async def run_cypher_query(self, query:str, include_properties:bool=True)->dict:
        if not self.s.bloodhound_enabled: raise BloodHoundUnavailable('BloodHound CE is disabled')
        payload={'query':query,'include_properties':include_properties}
        urls=['/api/v2/graphs/cypher','/api/v2/cypher','/api/v2/queries']
        try:
            async with httpx.AsyncClient(timeout=self.s.bloodhound_ingest_timeout,verify=self.s.bloodhound_verify_tls) as c:
                last=None
                for u in urls:
                    r=await c.post(f'{self.s.bloodhound_base_url.rstrip("/")}{u}',headers=self._headers(),json=payload); last=r
                    if r.status_code==404: continue
                    if r.status_code in (401,403): raise BloodHoundAuthError('BloodHound authentication failed')
                    if r.status_code==429: raise BloodHoundRateLimited('BloodHound rate limit reached')
                    r.raise_for_status()
                    try: return r.json()
                    except ValueError as e: raise BloodHoundError('BloodHound returned invalid JSON') from e
                raise BloodHoundNotFound(f'BloodHound Cypher endpoint not found ({last.status_code if last else "no response"})')
        except httpx.HTTPError as e: raise BloodHoundUnavailable(str(e)) from e
