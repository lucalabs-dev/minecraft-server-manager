##### IMPORTS #####

# Third-party Libraries
from fastapi import APIRouter, HTTPException

# Local Imports
from services.services.properties_service import write_properties
from services.config.default_properties import default_properties


##### API ROUTER #####
router = APIRouter()


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