from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_name: str = 'OpenAD Zero'
    database_url: str = 'postgresql+psycopg://openadzero:openadzero@openadzero-postgres:5432/openadzero'
    redis_url: str = 'redis://openadzero-redis:6379/0'
    evidence_dir: str = '/app/evidence'
    allow_public_scans: bool = False
    nmap_timeout_seconds: int = 900
    netexec_timeout_seconds: int = 600
    nuclei_rate_limit: int = 20
    nuclei_concurrency: int = 10
    nuclei_timeout: int = 10
    nuclei_job_timeout_seconds: int = 900
    cors_origins: str = 'http://localhost:5173,http://localhost:3000'
    bloodhound_enabled: bool = False
    bloodhound_base_url: str = 'http://bloodhound:8080'
    bloodhound_api_token: str = ''
    bloodhound_verify_tls: bool = False
    bloodhound_ingest_timeout: int = 300
    bloodhound_max_upload_mb: int = 250

@lru_cache
def get_settings() -> Settings:
    return Settings()
