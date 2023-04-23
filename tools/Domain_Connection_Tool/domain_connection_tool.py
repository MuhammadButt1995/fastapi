import platform
import subprocess
import socket
from observable import Observable
import asyncio
from tools.base_tool.base_tool import BaseTool
import winreg

class DomainConnectionTool(Observable, BaseTool):
    def __init__(self):
        Observable.__init__(self)
        BaseTool.__init__(self, name="Domain Connection Tool", description="Check if the user can connect to a domain", icon="domainconnectiontool.png")
        self._previous_status = None

    
    @staticmethod
    def check_vpn_status():
        system = platform.system()
        target_url = "zsproxy.company.com"

        if system == "Windows":
            flush_command = "ipconfig /flushdns > NUL"
            ping_command = f'ping -n 1 {target_url} > NUL && echo True || echo False'
            command = f'{flush_command} && {ping_command}'
        elif system == "Darwin":
            flush_command = "sudo killall -HUP mDNSResponder > /dev/null"
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
    
    @staticmethod
    def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as ex:
            print(ex)
            return False

    def _get_connection_type(self):
        if not self.check_internet_connection():
            return {"connection_type": "NO_INTERNET"}

        if self.check_zpa_connection():
            return {"connection_type": "ZPA"}
        elif self.check_vpn_status():
            return {"connection_type": "VPN"}
        else:
            return {"connection_type": "NOT_CONNECTED"}


    async def execute(self):
        async def _execute_with_retry(retries, delay):
            for _ in range(retries):
                result = self._get_connection_type()
                if result["connection_type"] != "NOT_CONNECTED":
                    return result
                await asyncio.sleep(delay)
            return {"connection_type": "NOT_CONNECTED"}

        connection_type = await _execute_with_retry(retries=3, delay=1)
        return connection_type
        
    async def monitor_status(self):
        while True:
            status = await self.execute()
            if status != self._previous_status:
                self._previous_status = status
                await self.notify(status)
            await asyncio.sleep(5)  # Adjust the interval as needed