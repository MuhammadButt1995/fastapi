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
        connection_status = {"connection_type": None}

        if system == "Windows":
            vpn_adapters = subprocess.check_output("ipconfig /all", shell=True, text=True)
            routing_table = subprocess.check_output("route print", shell=True, text=True)

            is_vpn = re.search(r"Description\s+: .*(VPN|TAP|TUNNEL|Tunneling)", vpn_adapters, re.IGNORECASE)
            is_zscaler = re.search(r"\b0\.0\.0\.0\b.*\b100\.64\.", routing_table)

        elif system == "Darwin":
            vpn_adapters = subprocess.check_output("ifconfig", shell=True, text=True)
            routing_table = subprocess.check_output("netstat -rn", shell=True, text=True)

            is_vpn = re.search(r"utun\d+", vpn_adapters)
            is_zscaler = re.search(r"\b0\.0\.0\.0\b.*\b100\.64\.", routing_table)

        if is_vpn:
            connection_status["connection_type"] = "VPN"
        elif is_zscaler:
            connection_status["connection_type"] = "ZPA"

        return connection_status