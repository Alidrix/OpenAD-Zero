import asyncio, shutil
from pathlib import Path
from app.core.security import ensure_allowed_tool
from app.events.publisher import publish
from app.events.schemas import MissionEvent

class CommandResult:
    def __init__(self, return_code:int, timed_out:bool=False): self.return_code=return_code; self.timed_out=timed_out

async def run_command(tool:str, args:list[str], cwd:Path, stdout_path:Path, stderr_path:Path, mission_id:str, job_id:str, timeout:int, log_event_type: str='job.log', log_prefix: str | None=None)->CommandResult:
    ensure_allowed_tool(tool)
    prefix = log_prefix or tool
    if shutil.which(tool) is None:
        await publish(MissionEvent(type=log_event_type, mission_id=mission_id, payload={'job_id':job_id,'line':f'[{prefix}] executable not found. Install {tool} or use Docker Compose.'}))
        return CommandResult(127)
    proc=await asyncio.create_subprocess_exec(tool,*args,cwd=str(cwd),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
    async def pump(stream, path, stream_prefix):
        with path.open('w') as f:
            while True:
                line=await stream.readline()
                if not line: break
                text=line.decode(errors='replace').rstrip(); f.write(text+'\n'); f.flush()
                await publish(MissionEvent(type=log_event_type, mission_id=mission_id, payload={'job_id':job_id,'line':f'[{stream_prefix}] {text}'}))
    tasks=[asyncio.create_task(pump(proc.stdout,stdout_path,prefix)), asyncio.create_task(pump(proc.stderr,stderr_path,prefix))]
    try:
        rc=await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill(); await proc.wait(); rc=-1; timed=True
    else: timed=False
    await asyncio.gather(*tasks)
    return CommandResult(rc,timed)
