import subprocess
import platform
import re
from typing import Any


async def get_ad_status(**params: Any):
    system = platform.system()

    if system == "Windows":
        result = subprocess.check_output("dsregcmd /status", shell=True, text=True)
        azure_ad_joined = re.search(r"AzureAdJoined\s+:\s+(\w+)", result)
        domain_joined = re.search(r"DomainJoined\s+:\s+(\w+)", result)

        status = {
            "azure_ad_joined": azure_ad_joined.group(1) == "YES"
            if azure_ad_joined
            else False,
            "domain_joined": domain_joined.group(1) == "YES"
            if domain_joined
            else False,
        }

        status["is_bound"] = (
            "BOUND"
            if status["azure_ad_joined"] and status["domain_joined"]
            else "NOT BOUND"
        )
        status["description"] = (
            "Your machine is domain joined and bound to Azure AD."
            if status["is_bound"] == "BOUND"
            else "Your machine is either not domain joined or not bound to Azure AD."
        )
        status["rating"] = "ok" if status["is_bound"] == "BOUND" else "error"
        return status

    elif system == "Darwin":
        status = {"ad_bind": True}

        status["is_bound"] = "BOUND" if status["ad_bind"] else "NOT BOUND"
        status["description"] = (
            "Your machine is bound to On-Prem Active Directory."
            if status["is_bound"] == "BOUND"
            else "Your machine is not bound to On-Prem Active Directory."
        )

        return status
