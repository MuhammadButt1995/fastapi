import platform
import subprocess
import asyncio
from tools.Internet_Connection_Tool.internet_connection_tool import InternetConnectionTool
from tools.base_tool.base_tool import BaseTool
from observable import Observable
import winreg
from tools.tool_type import ToolType
from tools.tags import Tag

class DomainConnectionTool(BaseTool, Observable):
    def __init__(self):
        super().__init__(
            name="Domain Connection",
            description="Get live data about the status of your connection to trusted networks.",
            tool_type=ToolType.AUTO_ENABLED,
            tags=[Tag.ZSCALER, Tag.NETWORK],
            icon="ShieldCheck"
        )
        Observable.__init__(self)

    
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
    

    def _get_connection_type(self):
        if not InternetConnectionTool.check_internet_connection()["is_connected"]:
            return {"is_connected": False, "status_message": "no_internet"}

        if self.check_zpa_connection():
            return {"is_connected": True, "status_message": "ZPA"}
        elif self.check_vpn_status():
            return {"is_connected": True, "status_message": "VPN"}
        else:
            return {"is_connected": False, "status_message": "not_connected"}


    async def execute(self):
        async def _execute_with_retry(retries, delay):
            for _ in range(retries):
                result = self._get_connection_type()
                if result["status_message"] != "not_connected":
                    return result
                await asyncio.sleep(delay)
            return {"is_connected": False, "status_message": "not_connected"}

        connection_type = await _execute_with_retry(retries=3, delay=1)
        return connection_type

    async def monitor_status(self):
        previous_state = None
        while True:
            current_state = await self.execute()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed