import platform
import subprocess
from base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):

    def __init__(self):
        super().__init__()
        self.name = "Domain Connection Tool"
        self.description = "Check if the user is connected to VPN or ZPA"
        self.icon = "domain.png"

    def check_vpn_status(self, system):
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

    def execute(self):
        system = platform.system()
        if self.check_vpn_status(system):
            return {"connection_type": "VPN"}
        elif self.check_zpa_status(system):
            return {"connection_type": "ZPA"}
        else:
            return {"connection_type": None}