##### IMPORTS #####

# Third-party Libraries
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Local Imports
from services.services.properties_service import (
    parse_properties,
    write_properties
)
from services.config.default_properties import default_properties


##### Pydantic models #####
class PropertiesRequest(BaseModel):
    property: dict[str, str]


##### API ROUTER #####
router = APIRouter()


#==============================#
#          ENDPOINTS           #
#==============================#
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