import asyncio
from typing import Dict
from tools.base_tool.base_tool import BaseTool
from observable import Observable

class InternetConnectionTool(BaseTool, Observable):

    def __init__(self):
        super().__init__(
            name="InternetConnectionTool",
            description="Checks the status of the internet connection.",
            icon="internet_connection_tool_icon.png"
        )
        Observable.__init__(self)

    @staticmethod
    def check_internet_connection() -> Dict:
        """
        Perform a simple internet connectivity check.
        """
        import socket

        try:
            # Try connecting to a common DNS server (Google's public DNS)
            socket.create_connection(("8.8.8.8", 53))
            return {"is_connected": True}
        except OSError:
            return {"is_connected": False}


    def execute(self) -> Dict:
       return self.check_internet_connection()

    async def monitor_status(self):
        previous_state = None
        while True:
            current_state = self.execute()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed