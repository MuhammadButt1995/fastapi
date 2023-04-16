import subprocess
import re
import platform
from tools.base_tool.base_tool import BaseTool


class AzureConnectionTool(BaseTool):
    def __init__(self):
        super().__init__('AzureConnectionTool', 'Check Azure AD join and registration status', 'azure_connection_tool.png')

    @staticmethod
    def execute():
        system = platform.system()

        if system == "Windows":
            result = subprocess.check_output("dsregcmd /status", shell=True, text=True)
            azure_ad_joined = re.search(r"AzureAdJoined\s+:\s+(\w+)", result)
            azure_ad_registered = re.search(r"IsDeviceJoined\s+:\s+(\w+)", result)
            domain_joined = re.search(r"DomainJoined\s+:\s+(\w+)", result)
            azure_ad_user = re.search(r"IsUserAzureAD\s+:\s+(\w+)", result)

            status = {
                "azure_ad_joined": azure_ad_joined.group(1) == "YES" if azure_ad_joined else False,
                "azure_ad_registered": azure_ad_registered.group(1) == "YES" if azure_ad_registered else False,
                "domain_joined": domain_joined.group(1) == "YES" if domain_joined else False,
                "azure_ad_user": azure_ad_user.group(1) == "YES" if azure_ad_user else False,
            }

            return status

        elif system == "Darwin":
            # Add macOS implementation if needed
            pass