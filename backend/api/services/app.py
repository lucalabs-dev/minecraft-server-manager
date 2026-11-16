##### IMPORTS #####

# Standard Library
import asyncio
import json
import os
import re
import shutil
import subprocess
import threading
import uuid

# Third-party Libraries
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Local Imports
from services.config.default_properties import default_properties


##### Pydantic models #####
class CommandRequest(BaseModel):
    command: str

class PropertiesRequest(BaseModel):
    property: dict[str, str] 


##### SERVER RUNTIME MANAGMENT #####
running_servers = {}
server_logs = {}
log_subscribers = {}


##### API ROUTER #####
router = APIRouter()


#==============================#
#       VERSION ENDPOINT       #
#==============================#
@router.get("/api/versions")
def get_versions():
    response = requests.get(
        "https://fill.papermc.io/v3/projects/paper",
        headers={
            "User-Agent": "MinecraftServerManager/1.0"
        }
    )
    response.raise_for_status()
    data = response.json()

    versions = []

    for version_group in data["versions"].values():
        versions.extend(version_group)

    return versions


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
    if not server_id in running_servers:
        with open("data/servers.json", "r") as servers:
            data = json.load(servers)

        if  any(server["id"] == server_id for server in data["servers"]):
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
        
            with open("data/servers.json", "w") as servers:
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

@router.get("/api/servers/{server_id}/properties")
def get_properties(server_id):
    try:
        properties = parse_properties(server_id)

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Not Found"
        )
    
    return properties

@router.patch("/api/servers/{server_id}/properties")
def patch_properties(server_id, request: PropertiesRequest):
    new_properties = request.property
    old_properties = parse_properties(server_id)

    for property, value in new_properties.items():
        if property not in old_properties:
            raise HTTPException(
                status_code=400,
                detail="Property not found"
            )

    write_properties(server_id, new_properties)

    return {"message": "Properties updated successfully"}

@router.post("/api/servers/{server_id}/properties/reset")
def reset_server_properties(server_id):
    write_properties(server_id, new_properties=default_properties)
    

#==============================#
#        EULA ENDPOINTS        #
#==============================# 
@router.get("/api/servers/{server_id}/eula")
def get_eula_status(server_id: str):
    with open("data/servers/" + server_id + "/eula.txt", "r") as file:
        content = file.read()

        if "eula=false" in content:
            return False
        elif "eula=true" in content:
            return True
        else:
            raise HTTPException(
                status_code=500,
                detail="eula.txt is broken"
            )

@router.post("/api/servers/{server_id}/eula")
def set_eula(server_id: str):
    with open("data/servers/" + server_id + "/eula.txt", "r") as file:
            content = file.read()

            if "eula=false" in content:
                content = content.replace("eula=false", "eula=true")

    with open("data/servers/" + server_id + "/eula.txt", "w") as file:
        file.write(content)

    write_properties(server_id, new_properties=default_properties)

    return {"message": "EULA was accepted"}


#==============================#
#      INTERNAL FUNCTIONS      #
#==============================#
def download_server_jar(version, server_path):
    os.makedirs(server_path)

    response = requests.get(
        "https://fill.papermc.io/v3/projects/paper/versions/" + version + "/builds",
        headers={
            "User-Agent": "MinecraftServerManager/1.0"
        }
    )
    response.raise_for_status()

    data = response.json()

    channel_priority = [
        "STABLE",
        "BETA",
        "ALPHA"
    ]

    build = None
    for channel in channel_priority:
        try:
            build = max(
                (build for build in data if build["channel"] == channel),
                key=lambda build: build["id"]
            )
            if build is not None:
                break
        except ValueError:
            continue

    if build is None:
        raise HTTPException(
            status_code=404,
            detail="No channel for this Version available"
        )

    url = build["downloads"]["server:default"]["url"]

    response = requests.get(url)
    response.raise_for_status()

    with open(server_path + "/server.jar", "wb") as file:
        file.write(response.content)

    initialize_server(server_path)
    
def initialize_server(server_path):
    process = subprocess.Popen(
        ["java", "-jar", "server.jar"],
        cwd=server_path,
    )
    process.wait()

def apply_default_properties(server_id):
    with open("data/servers/" + server_id + "/server.properties", "r") as file:
        content = file.read()

    lines = []
    found_settings = []

    for line in content.splitlines():
        if "=" in line:
            setting, old_value = line.split("=", 1)

            found_settings.append(setting)
            
            if setting in default_properties:
                new_value = default_properties[setting]
                line = setting + "=" + new_value
        lines.append(line)

    for setting in default_properties:
        if setting not in found_settings:
            lines.append(setting + "=" + default_properties[setting])
        
    content = "\n".join(lines)

    with open("data/servers/" + server_id + "/server.properties", "w") as file:
        file.write(content)

    
    return {"message": "Default server properties were applied"}

def parse_properties(server_id):
    server_path = "data/servers/" + server_id + "/server.properties"

    with open(server_path, "r") as file:
        content = file.read()

        properties = {}

        for line in content.splitlines():
            if "=" in line:
                setting, value = line.split("=", 1)

                properties[setting] = value

        return properties

def write_properties(server_id, new_properties):
    server_path = "data/servers/" + server_id + "/server.properties"

    with open(server_path, "r") as file:
        file_content = file.read() 

    lines = []
    found_properties = set()
    line_index = 0


    for line in file_content.splitlines():
        lines.append(line)

        if "=" in line:
            property_name, old_value = line.split("=", 1)

            found_properties.add(property_name)

            for updated_property, new_value in new_properties.items():
                if updated_property == property_name:
                    if new_value != old_value:
                        lines[line_index] = (property_name + "=" + new_value)
                        break

        line_index += 1

    for updated_property, new_value in new_properties.items(): 
        if updated_property not in found_properties:
            lines.append(updated_property + "=" + new_value)

    updated_content = "\n".join(lines)

    with open(server_path, "w") as file:
        file.write(updated_content)
    
def read_logs(server_id, process):
    for line in process.stdout:
        server_logs[server_id].append(line)
        for loop, queue in log_subscribers.get(server_id, []):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                line
            )

def validate_server_names(name):
    if name == "":
        raise HTTPException(
            status_code=400,
            detail="Server name cannot be empty" 
        )
    elif len(name) > 32:
        raise HTTPException(
            status_code=400,
            detail="Server name must not exceed 32 characters" 
        )
    elif re.fullmatch(r"[a-zA-Z0-9 _.-]+", name) is None:
        raise HTTPException(
            status_code=400,
            detail="Server name contains invalid characters. Allowed: letters, numbers, spaces, '.', '_' and '-'" 
        )