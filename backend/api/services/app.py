##### IMPORTS #####

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import uuid
import json
import requests
import os
import subprocess
import threading
import asyncio


running_servers = {}
server_logs = {}
log_subscribers = {}


router = APIRouter()

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


##### SERVER ENDPOINTS #####

@router.get("/api/servers")
def get_servers():
    with open("data/servers.json", "r") as servers:
        data = json.load(servers)
    return data["servers"]

@router.post("/api/servers")
def create_server(server: dict):
    server["id"] = str(uuid.uuid4())

    with open("data/servers.json", "r") as servers:
        data = json.load(servers)

    download_server_jar(server["version"], server["id"])

    data["servers"].append(server)

    with open("data/servers.json", "w") as servers:
        json.dump(data, servers, indent=2)

    return server

@router.get("/api/servers/{server_id}")
def get_server(server_id: str):

    with open("data/servers.json", "r") as servers:
        data = json.load(servers)

    for server in data["servers"]:

        if server["id"] == server_id:
            return server

    return {"error": "Server not found"}

@router.post("/api/servers/{server_id}/start")
def start_server(server_id):
    process = subprocess.Popen(
            ["java", "-jar", "server.jar"],
            cwd=("data/servers/" + server_id),
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
        return {"ERROR": "Server can not be stopped"}
    
    process.terminate()
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        return {"ERROR": "Stop timeout"} 
    del running_servers[server_id]

    return {"message": "Server stopped"}

@router.post("/api/servers/{server_id}/restart")
def restart_server(server_id):
    try:
        process = running_servers[server_id]
    except KeyError:
        return {"ERROR": "Server can not be restarted"}
    
    if process.poll() is None:
        stop_result = stop_server(server_id)
        if stop_result == {"message": "Server stopped"}:
            start_server(server_id)
        else:
            return stop_result
    else:
        return {"message": "Server is not running"}

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


##### EULA ENDPOINTS ##### 

@router.get("/api/servers/{server_id}/eula")
def get_eula_status(server_id: str):
    with open("data/servers/" + server_id + "/eula.txt", "r") as file:
        content = file.read()

        if "eula=false" in content:
            return False
        elif "eula=true" in content:
            return True
        else:
            return {"error": "eula.txt is broken"}

@router.post("/api/servers/{server_id}/eula")
def set_eula(server_id: str):
    with open("data/servers/" + server_id + "/eula.txt", "r") as file:
            content = file.read()

            if "eula=false" in content:
                content = content.replace("eula=false", "eula=true")

    with open("data/servers/" + server_id + "/eula.txt", "w") as file:
        file.write(content)

    apply_default_settings(server_id)

    return {"message": "EULA was accepted"}



##### INTERNAL FUNCTIONS #####

def download_server_jar(version, server_id):
    server_path = "data/servers/" + server_id
    os.makedirs(server_path)

    response = requests.get(
        "https://fill.papermc.io/v3/projects/paper/versions/" + version + "/builds",
        headers={
            "User-Agent": "MinecraftServerManager/1.0"
        }
    )
    response.raise_for_status()

    data = response.json()

    stable_build = max(
        (build for build in data if build["channel"] == "STABLE"),
        key=lambda build: build["id"]
    )

    url = stable_build["downloads"]["server:default"]["url"]

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

def apply_default_settings(server_id):
    default_settings = {
        "accepts-transfers": "false",
        "allow-flight": "false",
        "broadcast-console-to-ops": "true",
        "broadcast-rcon-to-ops": "true",
        "bug-report-link": "",
        "chat-spam-threshold-seconds": "10",
        "command-spam-threshold-seconds": "10",
        "debug": "false",
        "difficulty": "normal",
        "enable-code-of-conduct": "false",
        "enable-jmx-monitoring": "false",
        "enable-query": "false",
        "enable-rcon": "false",
        "enable-status": "true",
        "enforce-secure-profile": "true",
        "enforce-whitelist": "false",
        "entity-broadcast-range-percentage": "100",
        "force-gamemode": "false",
        "function-permission-level": "2",
        "gamemode": "survival",
        "generate-structures": "true",
        "generator-settings": "{}",
        "hardcore": "false",
        "hide-online-players": "false",
        "initial-disabled-packs": "",
        "initial-enabled-packs": "vanilla",
        "level-name": "world",
        "level-seed": "",
        "level-type": "minecraft\\:normal",
        "log-ips": "true",
        "management-server-allowed-origins": "",
        "management-server-enabled": "false",
        "management-server-host": "localhost",
        "management-server-port": "0",
        "management-server-tls-enabled": "true",
        "management-server-tls-keystore": "",
        "management-server-tls-keystore-password": "",
        "max-chained-neighbor-updates": "1000000",
        "max-players": "20",
        "max-tick-time": "60000",
        "max-world-size": "29999984",
        "motd": "A Minecraft Server",
        "network-compression-threshold": "256",
        "online-mode": "true",
        "op-permission-level": "4",
        "pause-when-empty-seconds": "-1",
        "player-idle-timeout": "0",
        "prevent-proxy-connections": "false",
        "query.port": "25565",
        "rate-limit": "0",
        "rcon.password": "",
        "rcon.port": "25575",
        "region-file-compression": "deflate",
        "require-resource-pack": "false",
        "resource-pack": "",
        "resource-pack-id": "",
        "resource-pack-prompt": "",
        "resource-pack-sha1": "",
        "server-ip": "",
        "server-port": "25565",
        "simulation-distance": "8",
        "spawn-protection": "16",
        "status-heartbeat-interval": "0",
        "sync-chunk-writes": "true",
        "text-filtering-config": "",
        "text-filtering-version": "0",
        "use-native-transport": "true",
        "view-distance": "20",
        "white-list": "false",

        # Additional settings:
        "pvp": "true",
        "spawn-monsters": "true",
        "spawn-animals": "true",
        "spawn-npcs": "true",
        "allow-nether": "true",
        "enable-command-block": "true"
    }

    with open("data/servers/" + server_id + "/server.properties", "r") as file:
        content = file.read()

    lines = []
    found_settings = []

    for line in content.splitlines():
        if "=" in line:
            setting, old_value = line.split("=", 1)

            found_settings.append(setting)
            
            if setting in default_settings:
                new_value = default_settings[setting]
                line = setting + "=" + new_value
        lines.append(line)

    for setting in default_settings:
        if setting not in found_settings:
            lines.append(setting + "=" + default_settings[setting])
        
    content = "\n".join(lines)

    with open("data/servers/" + server_id + "/server.properties", "w") as file:
                file.write(content)

    
    return {"message": "Default server properties were applied"}

def read_logs(server_id, process):
    for line in process.stdout:
        server_logs[server_id].append(line)
        for loop, queue in log_subscribers.get(server_id, []):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                line
            )