import os
from typing import Any


async def get_daas_status(**params: Any):
    # Getting all environment variables as a dictionary
    env_vars = os.environ

    # Iterating through all the values of environment variables to check if "ViewClient" is present
    for key, value in env_vars.items():
        if "ViewClient" in key or "ViewClient" in value:
            return {"is_on_daas": True}
    return {"is_on_daas": False}
