from typing import Any

from pydantic import BaseModel


class MissionEvent(BaseModel):
    type: str
    mission_id: str
    payload: dict[str, Any]
