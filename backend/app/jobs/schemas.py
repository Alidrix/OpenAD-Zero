from pydantic import BaseModel
class StartScenarioRequest(BaseModel):
    action: str = "start_scenario"
