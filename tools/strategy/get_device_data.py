import platform
import psutil
import datetime

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getDeviceData(ToolExecutionStrategy):

    def get_device_data(self):
        cpu_info = platform.processor() 
        ram_info = psutil.virtual_memory()
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()
        total_disk_size_gb = psutil.disk_usage('/').total / (1024 ** 3)
        current_disk_usage_gb = psutil.disk_usage('/').used / (1024 ** 3)

        manufacturer, model, serial_number = self.get_device_identifiers()

        return {
            "Computer name": platform.node(),
            "CPU details": cpu_info,
            "RAM": f"{round(float(ram_info.total) / (1024 ** 3), 2)} GB",
            "Total disk size": f"{total_disk_size_gb:.2f} GB",
            "Current disk usage": f"{current_disk_usage_gb:.2f} GB",
            "Manufacturer": manufacturer,
            "Model": model,
            "CPU architecture": platform.machine(),
            "Last boot time": boot_time,
            "Serial number": serial_number,
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
        
    def execute(self):
        return self.get_device_data()