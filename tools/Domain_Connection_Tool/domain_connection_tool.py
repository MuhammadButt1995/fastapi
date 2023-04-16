import os
import platform
import subprocess
import json
from typing import Dict
from tools.base_tool import BaseTool

class DomainConnectionTool(BaseTool):
    @staticmethod
    def execute() -> Dict[str, str]:
        connection_type = None

        # Check for VPN connection
        if DomainConnectionTool.check_vpn_connection():
            connection_type = "VPN"
        else:
            # Check for ZPA connection
            if DomainConnectionTool.check_zpa_connection():
                connection_type = "ZPA"

        return {"connection_type": connection_type}

    @staticmethod
    def check_vpn_connection() -> bool:
        system = platform.system()

        if system == "Windows":
            output = subprocess.check_output("netsh interface show interface", shell=True, text=True)
            if "VPN" in output:
                return True
        elif system == "Darwin":
            output = subprocess.check_output("ifconfig -a", shell=True, text=True)
            if "utun" in output:
                return True

        return False

    @staticmethod
    def check_zpa_connection() -> bool:
        system = platform.system()
        
        if system == "Windows":
            try:
                output = subprocess.check_output("net user %USERNAME% /domain", shell=True, text=True)
            except subprocess.CalledProcessError:
                return False

            if "User name" in output:
                return True
        elif system == "Darwin":
            output = subprocess.check_output("dscl /Search -read /Users/$(whoami)", shell=True, text=True)
            if "OriginalNodeName" in output:
                return True

        return False