from pathlib import Path
from app.core.config import get_settings
def job_dir(mission_id:str, job_id:str)->Path:
    p=Path(get_settings().evidence_dir)/mission_id/'jobs'/job_id; p.mkdir(parents=True, exist_ok=True); return p
