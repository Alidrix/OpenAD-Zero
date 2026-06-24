import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.init_db import init_db
from app.api.routes_health import router as health_router
from app.api.routes_missions import router as missions_router
from app.api.routes_events import router as events_router
from app.api.routes_capabilities import router as capabilities_router
from app.api.routes_evidence import router as evidence_router
logging.basicConfig(level=logging.INFO)
settings=get_settings(); app=FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(',')], allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
@app.on_event('startup')
def startup(): init_db()
app.include_router(health_router, prefix='/api')
app.include_router(missions_router, prefix='/api')
app.include_router(capabilities_router, prefix='/api')
app.include_router(evidence_router, prefix='/api')
app.include_router(events_router)
