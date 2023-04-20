import platform
import subprocess
from tools.toolbox import BaseTool
class InternetConnectionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="InternetConnectionTool",
            description="A tool to check the user's internet connection status.",
            icon="internet_connection_tool.png",
        )
    @staticmethod
    def get_internet_details():
        if platform.system() == "Windows":
            cmd_output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("utf-8")
            lines = cmd_output.split("\r\n")
            wifi_details = {}
            connection = {
                "is_connected_to_internet": False,
                "connection_type": "Not Connected",
            }

            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "State":
                        connection["is_connected_to_internet"] = value.lower() == "connected"
                        if connection["is_connected_to_internet"]:
                            connection["connection_type"] = "Wi-Fi"

                    wifi_details[key] = value

            # Check for Ethernet connection
            if not connection["is_connected_to_internet"]:
                ip_output = subprocess.check_output(["ipconfig"]).decode("utf-8")
                if "Ethernet adapter" in ip_output and "IPv4 Address" in ip_output:
                    connection["is_connected_to_internet"] = True
                    connection["connection_type"] = "Ethernet"

            wifi_details.pop("There is 1 interface on the system", None)
            return {"wifi_details": wifi_details, "connection": connection}

        elif platform.system() == "Darwin":
            result = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"])
            lines = result.decode("utf-8").strip().split("\n")

            wifi_details = {}
            connection = {
                "is_connected_to_internet": False,
                "connection_type": "Not Connected",
            }

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "state":
                        connection["is_connected_to_internet"] = value.lower() == "running"
                        if connection["is_connected_to_internet"]:
                            connection["connection_type"] = "Wi-Fi"

                    wifi_details[key] = value

            # Check for Ethernet connection
            if not connection["is_connected_to_internet"]:
                ip_output = subprocess.check_output(["ifconfig"]).decode("utf-8")
                if "en0" in ip_output and "inet" in ip_output:
                    connection["is_connected_to_internet"] = True
                    connection["connection_type"] = "Ethernet"

            return {"wifi_details": wifi_details, "connection": connection}

    def execute(self):
        return self.get_internet_details()
