import platform
import subprocess
from tools.toolbox import BaseTool


class DomainConnectionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="DomainConnectionTool",
            description="A tool to check if the user is connected to ZPA or VPN.",
            icon="domain_connection_tool.png",
        )

    @staticmethod
    def check_domain_connection():
        connection_type = {"connection_type": None}

        if platform.system() == "Windows":
            ip_output = subprocess.check_output(["ipconfig", "/all"]).decode("utf-8")

            if "ZPA" in ip_output:
                connection_type["connection_type"] = "ZPA"
            elif "VPN" in ip_output:
                connection_type["connection_type"] = "VPN"

        elif platform.system() == "Darwin":
            ip_output = subprocess.check_output(["ifconfig"]).decode("utf-8")

            if "ZPA" in ip_output:
                connection_type["connection_type"] = "ZPA"
            elif "VPN" in ip_output:
                connection_type["connection_type"] = "VPN"

        return connection_type

    def execute(self):
        return self.check_domain_connection()