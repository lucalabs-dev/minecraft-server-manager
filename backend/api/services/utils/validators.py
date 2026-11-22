##### IMPORTS #####

# Standard Library
import re

# Third-party Libraries
from fastapi import HTTPException


#==============================#
#          VALIDATORS          #
#==============================#
def validate_server_names(name: str) -> None:
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