import platform
import re
import os
from tools.base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):
    def __init__(self):
        super().__init__('DomainConnectionTool', 'Check if connected to ZPA or VPN', 'domain_connection_tool.png')

    @staticmethod
    def execute():
        system = platform.system()
        connection_status = {"zscaler_authenticated": False}

        if system == "Windows":
            log_path = os.path.expandvars(r"%ProgramData%\zscaler\Zscaler Client Connector\logs\zcc.log")
        elif system == "Darwin":
            log_path = "/Library/Application Support/zscaler/Zscaler Client Connector/logs/zcc.log"
        else:
            return connection_status

        try:
            with open(log_path, "r") as log_file:
                log_data = log_file.read()

            authenticated_pattern = r"ZPA\s+authenticated"
            is_authenticated = re.search(authenticated_pattern, log_data, re.IGNORECASE)

            if is_authenticated:
                connection_status["zscaler_authenticated"] = True

        except FileNotFoundError:
            pass

        return connection_status