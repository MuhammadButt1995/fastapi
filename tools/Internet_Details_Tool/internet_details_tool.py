import platform
import subprocess
import asyncio
from tools.base_tool.base_tool import BaseTool
from observable import Observable

class InternetDetailsTool(BaseTool, Observable):
    def __init__(self):
        super().__init__(
            name="Internet Details Tool",
            description="Get Wi-Fi and Ethernet connection details",
            icon="internetdetailstool.png"
        )
        Observable.__init__(self)

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
        previous_state = None
        while True:
            current_state = self.execute()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed