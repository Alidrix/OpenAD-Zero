import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_capabilities import router as capabilities_router
from app.api.routes_events import router as events_router
from app.api.routes_evidence import router as evidence_router
from app.api.routes_health import router as health_router
from app.api.routes_missions import router as missions_router
from app.api.routes_operations import router as operations_router
from app.api.routes_reports import router as reports_router
from app.api.routes_tool_automation import router as tool_automation_router
from app.api.routes_v2_scans import router as v2_scans_router
from app.api.routes_v2_scan_events import router as v2_scan_events_router
from app.api.routes_v2_recommendations import router as v2_recommendations_router
from app.core.config import get_settings
from app.db.init_db import init_db

logging.basicConfig(level=logging.INFO)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(',')],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(health_router, prefix='/api')
app.include_router(missions_router, prefix='/api')
app.include_router(capabilities_router, prefix='/api')
app.include_router(evidence_router, prefix='/api')
app.include_router(reports_router, prefix='/api')
app.include_router(operations_router, prefix='/api')
app.include_router(tool_automation_router, prefix='/api')
app.include_router(v2_scans_router, prefix='/api')
app.include_router(v2_recommendations_router, prefix='/api')
app.include_router(events_router)
app.include_router(v2_scan_events_router)
