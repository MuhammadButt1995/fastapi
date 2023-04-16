import platform
import subprocess
import re
from tools.base_tool import BaseTool


class DomainConnectionTool(BaseTool):
    def __init__(self):
        super().__init__('DomainConnectionTool', 'Check if connected to ZPA or VPN', 'domain_connection_tool.png')

    @staticmethod
    def check_zscaler_routes(system):
        zscaler_route_pattern = re.compile(r'100\.64\.')

        if system == 'Windows':
            routes_output = subprocess.check_output('route print', shell=True, text=True)
        elif system == 'Darwin':
            routes_output = subprocess.check_output('netstat -rn', shell=True, text=True)
        else:
            return False

        if zscaler_route_pattern.search(routes_output):
            return True

        return False

    @staticmethod
    def execute():
        system = platform.system()
        connection_status = {"zscaler_authenticated": False}

        if system == "Windows" or system == "Darwin":
            connection_status["zscaler_authenticated"] = DomainConnectionTool.check_zscaler_routes(system)

        return connection_status