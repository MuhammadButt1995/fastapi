import platform
import subprocess
import re
from tools.base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):
    def __init__(self):
        super().__init__('DomainConnectionTool', 'Check if connected to ZPA or VPN', 'domain_connection_tool.png')

    @staticmethod
    def execute():
        system = platform.system()
        connection_status = {"zscaler_authenticated": False}

        if system == "Windows":
            cmd = "ipconfig /all"
        elif system == "Darwin":
            cmd = "scutil --dns"
        else:
            return connection_status

        result = subprocess.check_output(cmd, shell=True, text=True)

        zscaler_dns_pattern = r"100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.[0-9]+\.[0-9]+"

        is_zscaler_dns = re.search(zscaler_dns_pattern, result)

        if is_zscaler_dns:
            connection_status["zscaler_authenticated"] = True

        return connection_status