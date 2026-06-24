from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.demo.seed_demo import seed_demo

router=APIRouter(prefix='/demo')

@router.post('/seed')
def seed(db:Session=Depends(get_db)):
    if not get_settings().openadzero_enable_demo_endpoint:
        raise HTTPException(404, 'Demo endpoint disabled')
    return seed_demo(db)
