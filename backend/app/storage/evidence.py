from pathlib import Path
from app.core.paths import mission_evidence_dir
def job_dir(mission_id:str, job_id:str)->Path:
    return mission_evidence_dir(mission_id, 'jobs', job_id)
