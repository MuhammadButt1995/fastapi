import platform
import subprocess
import asyncio
from observable import Observable
from tools.toolbox import BaseTool

class InternetDetailsTool(Observable, BaseTool):
    def __init__(self):
        Observable.__init__(self)
        BaseTool.__init__(self, name="Internet Details Tool", description="Get Wi-Fi and Ethernet connection details", icon="internetdetailstool.png")
        self._previous_state = None

    def parse_wifi_details(self, raw_output):
        lines = raw_output.split("\n")
        wifi_details = {}

        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip()
                value = value.strip()
                wifi_details[key] = value

        return wifi_details

    def get_wifi_details(self):
        if platform.system() == "Windows":
            cmd_output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("utf-8")
            parsed_output = self.parse_wifi_details(cmd_output)
            return {"connection_details": {"wifi_details": parsed_output}}
        elif platform.system() == "Darwin":
            result = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"])
            parsed_output = self.parse_wifi_details(result.decode("utf-8").strip())
            return {"connection_details": {"wifi_details": parsed_output}}

    def execute(self):
        return self.get_wifi_details()

    async def monitor_status(self):
        while True:
            wifi_details = self.get_wifi_details()
            if wifi_details != self._previous_state:
                self._previous_state = wifi_details
                await self.notify(wifi_details)
            await asyncio.sleep(5)  # Adjust the interval as needed