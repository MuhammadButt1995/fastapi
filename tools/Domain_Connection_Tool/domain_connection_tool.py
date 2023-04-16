import platform
import subprocess
from base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):

    def __init__(self):
        super().__init__()

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

    def check_zpa_status(self, system):
        if system == "Windows":
            command = 'net user %USERNAME% /domain'
        elif system == "Darwin":
            command = 'id -Gn'
        else:
            return False

        try:
            output = subprocess.check_output(command, shell=True, text=True).strip()
            return "ZPA" in output
        except subprocess.CalledProcessError:
            return False

    def execute(self):
        system = platform.system()
        if self.check_vpn_status(system):
            return {"connection_type": "VPN"}
        elif self.check_zpa_status(system):
            return {"connection_type": "ZPA"}
        else:
            return {"connection_type": None}