from datetime import datetime
from pydantic import BaseModel, ConfigDict
class _Orm(BaseModel):
    model_config=ConfigDict(from_attributes=True)
class MissionObjectiveResponse(_Orm):
    id:str; mission_id:str; objective_name:str; objective_description:str|None; objective_type:str; objective_target:str|None; objective_status:str; operator_note:str|None; created_at:datetime; updated_at:datetime
class MissionObjectiveUpdate(BaseModel):
    objective_name:str|None=None; objective_description:str|None=None; objective_type:str|None=None; objective_target:str|None=None; objective_status:str|None=None; operator_note:str|None=None
class MissionPhaseResponse(_Orm):
    id:str; mission_id:str; phase_key:str; name:str; description:str|None; status:str; order_index:int; started_at:datetime|None; completed_at:datetime|None; summary:str|None
class MissionPhaseUpdate(BaseModel):
    status:str|None=None; summary:str|None=None
class TimelineEventCreate(BaseModel):
    event_type:str; title:str; description:str|None=None; source:str='manual'; severity:str='info'; related_host_id:str|None=None; related_service_id:str|None=None; related_finding_id:str|None=None; related_evidence_id:str|None=None; related_job_id:str|None=None; related_report_id:str|None=None; related_bloodhound_collection_id:str|None=None; metadata_json:dict|None=None
class TimelineEventResponse(_Orm):
    id:str; mission_id:str; event_type:str; title:str; description:str|None; source:str; severity:str; related_host_id:str|None; related_service_id:str|None; related_finding_id:str|None; related_evidence_id:str|None; related_job_id:str|None; related_report_id:str|None; related_bloodhound_collection_id:str|None; metadata_json:dict|None; created_at:datetime
class ProgressScoreResponse(BaseModel):
    score:int; level:str; completed_items:list[str]; missing_items:list[str]; details:dict
