from app.core.config import get_settings
class BloodHoundClient:
    def __init__(self): self.s=get_settings()
    def status(self):
        if not self.s.bloodhound_enabled: return {'status':'disabled','enabled':False,'base_url':self.s.bloodhound_base_url}
        return {'status':'enabled','enabled':True,'base_url':self.s.bloodhound_base_url}
    async def upload_zip(self, path):
        headers={}
        if self.s.bloodhound_api_token: headers['Authorization']=f'Bearer {self.s.bloodhound_api_token}'
        import httpx
        async with httpx.AsyncClient(timeout=self.s.bloodhound_ingest_timeout, verify=self.s.bloodhound_verify_tls) as c:
            with open(path,'rb') as f:
                r=await c.post(f'{self.s.bloodhound_base_url.rstrip("/")}/api/v2/file-upload/start', headers=headers, files={'file':('sharphound.zip',f,'application/zip')})
            r.raise_for_status(); return r.json() if r.content else {'status_code':r.status_code}
