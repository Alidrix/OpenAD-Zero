from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.demo.seed_demo import seed_demo

router = APIRouter(prefix='/demo', tags=['demo'])

@router.post('/seed')
def seed_demo_endpoint(db: Session = Depends(get_db)):
    if not get_settings().openadzero_enable_demo_endpoint:
        raise HTTPException(status_code=404, detail='Demo endpoint disabled')
    mission = seed_demo(db)
    return {'mission_id': mission.id, 'name': mission.name, 'status': mission.status}
