##### IMPORTS #####

# Third-party Libraries
from fastapi import APIRouter
import requests


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
        },
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    versions = []

    for version_group in data["versions"].values():
        versions.extend(version_group)

    return versions