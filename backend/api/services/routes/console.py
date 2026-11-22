##### IMPORTS #####

# Standard Library
import asyncio

# Third-party Libraries
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Local Imports
from services.state.server_state import (
    running_servers,
    log_subscribers
)

##### Pydantic models #####
class CommandRequest(BaseModel):
    command: str


##### API ROUTER #####
router = APIRouter()


#==============================#
#       CONSOLE ENDPOINTS      #
#==============================#
@router.get("/api/servers/{server_id}/logs")
async def stream_logs(server_id: str):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    log_subscribers.setdefault(server_id, []).append((loop, queue))

    async def event_generator():   
        try:
            while True:
                line = await queue.get()
                yield f"data: {line}\n\n"
        finally:
            log_subscribers[server_id].remove((loop, queue))

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.post("/api/servers/{server_id}/command")
def do_command(server_id: str, request: CommandRequest):
    command = request.command.strip()
    
    if command == "":
        raise HTTPException(
            status_code=400, 
            detail="Empty command!"
        )

    if server_id not in running_servers:
        raise HTTPException(
            status_code=404, 
            detail="Server is not running"
        )

    process = running_servers[server_id]

    if process.poll() is not None:
        del running_servers[server_id]

        raise HTTPException(
            status_code=404,
            detail="Server is not running"
        )

    if process.stdin is None:
        raise HTTPException(
            status_code=500,
            detail="Server input is not available"
        )


    try:
        process.stdin.write(command + "\n")
        process.stdin.flush()
    except (BrokenPipeError, OSError):
        raise HTTPException(
            status_code=500,
            detail="Could not send command to server"
        )

    return {"message": "Command "}