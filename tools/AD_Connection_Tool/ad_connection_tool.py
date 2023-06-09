import subprocess
import re
import platform
import asyncio
from tools.base_tool.base_tool import BaseTool
from observable import Observable
from tools.tool_type import ToolType
from tools.tags import Tag
class ADConnectionTool(BaseTool, Observable):
    def __init__(self):
        super().__init__(
            name="AD Connection",
            description="Get live data about the status of your Active Directory or AAD connection.",
            tool_type=ToolType.AUTO_ENABLED,
            tags=[Tag.AD],
            icon='Cloud',
        )
        Observable.__init__(self)

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

            status["is_connected"] = status["azure_ad_joined"] and status["domain_joined"]

            return status

        elif system == "Darwin":
            status = {
                "ad_bind": True
            }

            status["is_connected"] = status["ad_bind"]

            return status

    def execute(self):
        return self.get_connection_status()

    async def monitor_status(self):
        previous_state = None
        while True:
            current_state = self.execute()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed