from dataclasses import dataclass, asdict
from functools import lru_cache

VALID_STATUSES={'implemented','partial','planned','manual_only','lab_only','disabled','out_of_scope'}
VALID_MODES={'safe','assisted','lab','none'}
VALID_EXECUTIONS={'backend','manual','manual_card','external','none'}
REQUIRED_FIELDS={'id','name','category','status','mode','risk_level','requires_approval','execution','description','evidence'}

@dataclass(frozen=True)
class Capability:
    id:str; name:str; category:str; status:str; mode:str; risk_level:int; requires_approval:bool; execution:str; description:str; evidence:bool
    def model_dump(self): return asdict(self)

_CAPABILITIES=[
Capability('nmap_discovery','Nmap discovery','discovery','implemented','safe',1,False,'backend','Network and service discovery using Nmap.',True),
Capability('netexec_smb_safe_enum','NetExec SMB safe enum','enumeration','implemented','assisted',2,True,'backend','Controlled SMB enumeration and enrichment through NetExec.',True),
Capability('nuclei_web_exposure_scan','Nuclei safe web exposure scan','vulnerability_discovery','implemented','assisted',2,True,'backend','Safe Nuclei scan against HTTP/HTTPS services discovered by Nmap.',True),
Capability('bloodhound_sharphound_upload','BloodHound / SharpHound ZIP ingestion','active_directory_analysis','implemented','assisted',1,False,'backend','Upload, validate, store and optionally ingest SharpHound ZIP data.',True),
Capability('bloodhound_explorer','BloodHound Explorer','active_directory_analysis','implemented','assisted',1,False,'backend','Search and inspect AD objects, properties, relations and permissions using BloodHound data.',True),
Capability('bloodhound_pathfinding','BloodHound read-only pathfinding','active_directory_analysis','implemented','assisted',1,False,'backend','Read-only pathfinding toward sensitive groups such as Domain Admins.',True),
Capability('reporting_engine','Reporting engine','reporting','planned','safe',1,False,'backend','Generate Markdown, HTML and PDF reports from findings and evidence.',True),
Capability('ai_planner','AI-assisted planner','planning','planned','assisted',1,False,'none','Suggest next steps from current findings, without executing sensitive actions.',False),
Capability('credential_collection','Credential collection','advanced_authorized_testing','manual_only','lab',5,True,'manual_card','Not automated in this build. May be documented as a manual, authorized lab/testing activity in future governance workflows.',True),
Capability('lateral_movement','Lateral movement','advanced_authorized_testing','manual_only','lab',5,True,'manual_card','Not automated in this build. May be represented as manual validation notes in authorized lab/testing contexts.',True),
Capability('brute_force','Brute force / password spraying','advanced_authorized_testing','disabled','lab',5,True,'none','Disabled. OpenAD Zero does not provide automated brute force or password spraying.',False),
Capability('pass_the_hash','Pass-the-hash','advanced_authorized_testing','manual_only','lab',5,True,'manual_card','Not automated in this build. May be represented only as a manual lab validation note.',True),
Capability('lsass_dump','LSASS dump','advanced_authorized_testing','disabled','lab',5,True,'none','Disabled. No automated LSASS dump implementation.',False),
Capability('dcsync','DCSync','advanced_authorized_testing','disabled','lab',5,True,'none','Disabled. No automated DCSync implementation.',False),
Capability('persistence','Persistence','advanced_authorized_testing','out_of_scope','none',5,True,'none','Out of scope for OpenAD Zero. Persistence mechanisms are not implemented.',False),
Capability('edr_bypass','EDR bypass','advanced_authorized_testing','out_of_scope','none',5,True,'none','Out of scope for OpenAD Zero. EDR bypass is not implemented.',False),
]

@lru_cache
def list_capabilities():
    validate_catalog(); return list(_CAPABILITIES)

def get_capability(capability_id:str):
    return next((c for c in list_capabilities() if c.id==capability_id), None)

def validate_catalog():
    seen=set()
    for c in _CAPABILITIES:
        d=c.model_dump(); missing=REQUIRED_FIELDS-set(d)
        if missing: raise ValueError(f'{c.id} missing {missing}')
        if c.id in seen: raise ValueError(f'duplicate capability {c.id}')
        seen.add(c.id)
        if c.status not in VALID_STATUSES: raise ValueError(c.id)
        if c.mode not in VALID_MODES: raise ValueError(c.id)
        if c.execution not in VALID_EXECUTIONS: raise ValueError(c.id)
        if not isinstance(c.risk_level,int) or not 1<=c.risk_level<=5: raise ValueError(c.id)

def is_executable(c:Capability): return c.status not in {'disabled','out_of_scope','manual_only'} and c.execution=='backend'
def creates_manual_card_only(c:Capability): return c.status=='manual_only' and c.execution=='manual_card'
