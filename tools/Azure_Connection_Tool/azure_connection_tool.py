import subprocess
import re
import platform
import asyncio
from observable import Observable
from tools.base_tool.base_tool import BaseTool


class AzureConnectionTool(Observable, BaseTool):
    def __init__(self):
        Observable.__init__(self)
        BaseTool.__init__(self, name="Azure Connection Tool", description="Check Azure AD join and registration status", icon="azure_connection_tool.png")
        self._previous_status = None

    def get_connection_status(self):
        system = platform.system()

        if system == "Windows":
            result = subprocess.check_output("dsregcmd /status", shell=True, text=True)
            azure_ad_joined = re.search(r"AzureAdJoined\s+:\s+(\w+)", result)
            domain_joined = re.search(r"DomainJoined\s+:\s+(\w+)", result)

            status = {
                "azure_ad_joined": azure_ad_joined.group(1) == "YES" if azure_ad_joined else False,
                "domain_joined": domain_joined.group(1) == "YES" if domain_joined else False,
            }

            return status

        elif system == "Darwin":
            # Add macOS implementation if needed
            pass

    async def execute(self):
        connection_status = self.get_connection_status()
        return connection_status

    async def monitor_status(self):
        while True:
            status = await self.execute()
            if status != self._previous_status:
                self._previous_status = status
                await self.notify(status)
            await asyncio.sleep(5)  # Adjust the interval as needed