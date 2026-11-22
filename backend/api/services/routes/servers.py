##### IMPORTS #####

# Standard Library
import json
import shutil
import subprocess
import threading
import uuid

# Third-party Libraries
from fastapi import APIRouter, HTTPException

# Local Imports
from services.utils.validators import validate_server_names
from services.services.server_service import (
    read_logs,
    download_server_jar
)
from services.state.server_state import (
    running_servers,
    server_logs,
)


##### API ROUTER #####
router = APIRouter()


#==============================#
#       SERVER ENDPOINTS       #
#==============================#
@router.get("/api/servers")
def get_servers():
    with open("data/servers.json", "r") as servers:
        data = json.load(servers)

    return data["servers"]

@router.post("/api/servers")
def create_server(server: dict):
    name = server["name"].strip()
    validate_server_names(name)
    
    server["name"] = name
    server["id"] = str(uuid.uuid4())

    with open("data/servers.json", "r") as servers:
        data = json.load(servers)

    server_path = "data/servers/" + server["id"]
    try:
        download_server_jar(server["version"], server_path)

        data["servers"].append(server)

        with open("data/servers.json", "w") as servers:
            json.dump(data, servers, indent=2)

    except Exception as e:
        shutil.rmtree(server_path, ignore_errors=True)
        print(f"Server creation failed: {e}")                   
        
        raise HTTPException(
            status_code=500,
            detail="An error occurred while creating the server"
        )
    
    return server

@router.get("/api/servers/{server_id}")
def get_server(server_id: str):

    with open("data/servers.json", "r") as servers:
        data = json.load(servers)

    for server in data["servers"]:
        if server["id"] == server_id:
            return server

    raise HTTPException(
        status_code=404,
        detail="Server not found"
    )

@router.delete("/api/servers/{server_id}")
def delete_server(server_id):
    if server_id not in running_servers:
        with open("data/servers.json", "r") as servers:
            data = json.load(servers)

        if any(server["id"] == server_id for server in data["servers"]):
            # delete server from json
            data["servers"] = [
                server for server in data["servers"]
                if server["id"] != server_id
            ]

            # delete server from /data/servers/
            try:
                shutil.rmtree("/app/data/servers/" + server_id) 
            except FileNotFoundError:
                pass
        
            with open("app/data/servers.json", "w") as servers:
                json.dump(data, servers, indent=2)

            return {"message": "Server deleted"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Server not found"
            )
    else:
        raise HTTPException(
            status_code=409,
            detail="Server is running"
        )

@router.post("/api/servers/{server_id}/start")
def start_server(server_id):
    process = subprocess.Popen(
            ["java", "-jar", "server.jar"],
            cwd=("data/servers/" + server_id),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
    )
    running_servers[server_id] = process
    server_logs[server_id] = []
    
    threading.Thread(
        target = read_logs,
        args = (server_id, process)
    ).start()

    return {"message": "Server is running"}
 
@router.post("/api/servers/{server_id}/stop")
def stop_server(server_id):
    try:
        process = running_servers[server_id]
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Server not found"
        )
    
    process.stdin.write("stop\n")
    process.stdin.flush()
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Stop Timeout"
        ) 
    del running_servers[server_id]

    return {"message": "Server stopped"}

@router.post("/api/servers/{server_id}/restart")
def restart_server(server_id):
    try:
        process = running_servers[server_id]
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Server not found"
        )
    
    if process.poll() is None:
        stop_result = stop_server(server_id)
        if stop_result == {"message": "Server stopped"}:
            start_server(server_id)
        else:
            return stop_result
    else:
        raise HTTPException(
            status_code=409,
            detail="Server is not running"
        )

    return {"message": "Server restarted"}

@router.get("/api/servers/{server_id}/status")
def get_status(server_id):
    if server_id in running_servers:
        process = running_servers[server_id]

        if process.poll() is None:
            return {"status": "online"}
        else:
            del running_servers[server_id]
            return {"status": "offline"}
    else:
        return {"status": "offline"}


    
