import platform
import subprocess
from tools.base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):

    def __init__(self):
        super().__init__(name="Domain Connection Tool", description="Check if the user is connected to VPN or ZPA", icon="domainconnectiontool.png")

    @staticmethod
    def check_vpn_status():
        system = platform.system()
        target_machine = "pwsys-apcm12-27"

        if system == "Windows":
            command = f'powershell.exe Test-Connection -ComputerName "{target_machine}" -Count 1 -Quiet'
        elif system == "Darwin":
            command = f'ping -c 1 {target_machine} > /dev/null && echo True || echo False'
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
                output = subprocess.check_output("net user %USERNAME% /domain", shell=True, text=True)
            except subprocess.CalledProcessError:
                return False

            if "User name" in output:
                return True
        elif system == "Darwin":
            output = subprocess.check_output("dscl /Search -read /Users/$(whoami)", shell=True, text=True)
            if "OriginalNodeName" in output:
                return True

    def execute(self):
        if self.check_vpn_status():
            return {"connection_type": "VPN"}
        elif self.check_zpa_connection():
            return {"connection_type": "ZPA"}
        else:
            return {"connection_type": None}