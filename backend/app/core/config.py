import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def read_secret_value(env_name: str, file_env_name: str | None = None) -> str:
    file_name = file_env_name or f'{env_name}_FILE'
    secret_file = os.getenv(file_name, '').strip()
    if secret_file:
        path = Path(secret_file)
        try:
            return path.read_text(encoding='utf-8').strip()
        except OSError as exc:
            raise RuntimeError(f'{file_name} points to an unreadable secret file') from exc
    return os.getenv(env_name, '')


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_name: str = 'OpenAD Zero'
    openadzero_env: str = 'dev'
    database_url: str = 'postgresql+psycopg://openadzero:openadzero@openadzero-postgres:5432/openadzero'
    postgres_password: str = 'openadzero'
    neo4j_password: str = ''
    redis_url: str = 'redis://openadzero-redis:6379/0'
    evidence_dir: str = './evidence'
    testing: bool = False
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
    external_evidence_max_upload_mb: int = 100
    external_evidence_allowed_extensions: str = '.txt,.log,.json,.jsonl,.xml,.csv,.zip,.png,.jpg,.jpeg,.md'
    external_evidence_preview_max_bytes: int = 200000
    openadzero_auto_create_tables: bool = False
    openadzero_run_migrations_on_startup: bool = False
    openadzero_auto_migrate: bool = False
    openadzero_require_schema_ready: bool = False
    openadzero_default_mode: str = 'safe'
    openadzero_enable_assisted_mode: bool = True
    openadzero_enable_ctf_lab_mode: bool = False
    openadzero_enable_manual_action_cards: bool = False
    openadzero_enable_external_evidence_import: bool = True
    openadzero_enable_reporting: bool = False
    openadzero_enable_ai_planner: bool = False
    openadzero_enable_advanced_automation: bool = False
    openadzero_auth_enabled: bool = False
    openadzero_api_token: str = ''
    openadzero_allow_unauthenticated_localhost: bool = True
    openadzero_auth_protect_docs: bool = False
    openadzero_approval_ttl_seconds: int = 900
    openadzero_action_job_timeout_seconds: int = 900
    openadzero_action_job_ttl_seconds: int = 300
    openadzero_action_result_ttl_seconds: int = 86400
    openadzero_process_log_tail_bytes: int = 20000
    openadzero_process_max_log_bytes: int = 5000000

    def model_post_init(self, __context) -> None:
        self.openadzero_api_token = read_secret_value('OPENADZERO_API_TOKEN') or self.openadzero_api_token
        self.bloodhound_api_token = read_secret_value('BLOODHOUND_API_TOKEN') or self.bloodhound_api_token
        self.postgres_password = read_secret_value('POSTGRES_PASSWORD') or self.postgres_password
        self.neo4j_password = read_secret_value('NEO4J_PASSWORD') or self.neo4j_password


@lru_cache
def get_settings() -> Settings:
    return Settings()
