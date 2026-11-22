##### IMPORTS #####

# Standard Library
import os
import subprocess

# Third-party Libraries
import requests
from fastapi import HTTPException

# Local Imports
from services.services.properties_service import write_properties
from services.state.server_state import (
    server_logs,
    log_subscribers
)


#==============================#
#        SERVER SERVICES       #
#==============================#
def download_server_jar(version, server_path):
    os.makedirs(server_path)

    response = requests.get(
        "https://fill.papermc.io/v3/projects/paper/versions/" + version + "/builds",
        headers={
            "User-Agent": "MinecraftServerManager/1.0"
        },
        timeout=10
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

    
def read_logs(server_id, process):
    for line in process.stdout:
        server_logs[server_id].append(line)
        for loop, queue in log_subscribers.get(server_id, []):
            loop.call_soon_threadsafe(
                queue.put_nowait,
                line
            )