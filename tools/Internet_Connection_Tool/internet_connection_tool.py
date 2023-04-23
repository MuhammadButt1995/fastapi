import platform
import subprocess
import asyncio
import socket
from observable import Observable
from tools.toolbox import BaseTool

class InternetConnectionTool(Observable, BaseTool):
    def __init__(self):
        Observable.__init__(self)
        BaseTool.__init__(self, name="Internet Connection Tool", description="Check if the user is connected to the internet", icon="internetconnectiontool.png")
        self._previous_state = None

    @staticmethod
    def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as ex:
            print(ex)
            return False

    def execute(self):
        return {"connected": self.check_internet_connection()}

    async def monitor_status(self):
        while True:
            connection_status = self.check_internet_connection()
            if connection_status != self._previous_state:
                self._previous_state = connection_status
                await self.notify(connection_status)
            await asyncio.sleep(5)  # Adjust the interval as needed