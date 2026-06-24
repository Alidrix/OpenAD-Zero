from pydantic import BaseModel
class SharpHoundCommand(BaseModel):
    command:str; execution_mode:str='manual'; risk_level:int=3; requires_domain_user_context:bool=True; notes:list[str]
