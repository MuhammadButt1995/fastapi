import platform
import psutil
import socket
import datetime
from getpass import getuser
import asyncio
from tools.base_tool.base_tool import BaseTool
from observable import Observable

class FMInfo(BaseTool, Observable):
    def __init__(self):
        super().__init__(name="FMInfo", description="Fetches and displays system and user information", icon="fminfo.png")
        Observable.__init__(self)

    def execute(self, section: str):
        section_methods = {
            "user": self.get_user_data,
            "device": self.get_device_data,
            "networking": self.get_networking_data,
        }

        if section not in section_methods:
            raise ValueError("Invalid section specified.")

        return section_methods[section]()

    def get_user_data(self):
        # This is a placeholder implementation, as some of the user data is highly platform and
        # environment-dependent. You might need to use platform-specific libraries or call
        # external tools or services to obtain some of the information.
        return {
            "logged_on_domain": "example.com",  # Platform-dependent, needs a specific implementation
            "current_user_name": getuser(),
            "last_login_time": "2023-04-12T10:15:30",
            "last_password_set": "2023-03-20T14:30:15",
            "password_expiration": "2023-06-20T14:30:15",
        }


    def get_device_data(self):
        cpu_info = platform.processor() 
        ram_info = psutil.virtual_memory()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()
        total_disk_size_gb = psutil.disk_usage('/').total / (1024 ** 3)
        current_disk_usage_gb = psutil.disk_usage('/').used / (1024 ** 3)

        manufacturer, model, serial_number = self.get_device_identifiers()

        return {
            "computer_name": platform.node(),
            "CPU_details": cpu_info,
            "RAM": f"{round(float(ram_info.total) / (1024 ** 3), 2)} GB",
            "total_disk_size": f"{total_disk_size_gb:.2f} GB",
            "current_disk_usage": f"{current_disk_usage_gb:.2f} GB",
            "manufacturer": manufacturer,
            "model": model,
            "CPU_architecture": platform.machine(),
            "last_boot_time": boot_time,
            "serial_number": serial_number,
        }

    def get_device_identifiers(self):
        system = platform.system()
        if system == "Windows":
            # You will need to use Windows Management Instrumentation (WMI) library.
            # It can be installed with: pip install wmi
            import wmi

            w = wmi.WMI()
            for item in w.Win32_ComputerSystem():
                manufacturer = item.Manufacturer
                model = item.Model
            for item in w.Win32_BIOS():
                serial_number = item.SerialNumber

        elif system == "Darwin":
            # macOS implementation
            import subprocess

            def get_system_profiler_data(datatype: str) -> str:
                return subprocess.check_output(["system_profiler", datatype]).decode("utf-8").strip()

            manufacturer = "Apple Inc."
            model = get_system_profiler_data("SPHardwareDataType").split("Model Name:")[1].split("\n")[0].strip()
            serial_number = get_system_profiler_data("SPHardwareDataType").split("Serial Number (system):")[1].split("\n")[0].strip()

        else:
            # Other platforms (e.g., Linux) or fallback implementation
            manufacturer = "Unknown"
            model = "Unknown"
            serial_number = "Unknown"

        return manufacturer, model, serial_number

    @staticmethod
    def get_networking_data():
        active_adapters = {}
        other_adapters = {}
        
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    if psutil.net_if_stats()[interface].isup:
                        active_adapters[interface] = addr.address
                    else:
                        other_adapters[interface] = addr.address

        return {"active_adapters": active_adapters, "other_adapters": other_adapters}
    
    async def monitor_status(self):
        previous_state = None
        while True:
            current_state = self.get_networking_data()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed
    

    