import platform
import subprocess
import socket
from tools.base_tool.base_tool import BaseTool
import winreg

class DomainConnectionTool(BaseTool):

    def __init__(self):
        super().__init__(name="Domain Connection Tool", description="Check if the user is connected to VPN or ZPA", icon="domainconnectiontool.png")

    
    @staticmethod
    def check_vpn_status():
        system = platform.system()
        target_url = "zsproxy.company.com"

        if system == "Windows":
            flush_command = "ipconfig /flushdns"
            ping_command = f'ping -n 1 {target_url} > NUL && echo True || echo False'
            command = f'{flush_command} && {ping_command}'
        elif system == "Darwin":
            flush_command = "sudo killall -HUP mDNSResponder"
            ping_command = f'ping -c 1 {target_url} > /dev/null && echo True || echo False'
            command = f'{flush_command} && {ping_command}'
        else:
            return False

        try:
            output = subprocess.check_output(command, shell=True, text=True).strip()
            return output.lower() == "true"
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def check_zpa_connection():
        system = platform.system()

        if system == "Windows":
            try:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                zscaler_key = winreg.OpenKey(registry, r"SOFTWARE\Zscaler\App")
                zpa_state, _ = winreg.QueryValueEx(zscaler_key, "ZPA_State")
                winreg.CloseKey(zscaler_key)
                winreg.CloseKey(registry)

                if zpa_state == "TUNNEL_FORWARDING":
                    return True
            except FileNotFoundError:
                return False

        elif system == "Darwin":
            output = subprocess.check_output("dscl /Search -read /Users/$(whoami)", shell=True, text=True)
            if "OriginalNodeName" in output:
                return True

        return False

    def execute(self):
        if self.check_zpa_connection():
            return {"connection_type": "ZPA"}
        elif self.check_vpn_status():
            return {"connection_type": "VPN"}
        else:
            return {"connection_type": None}