import platform
import psutil
import datetime
from typing import Any, Optional, Dict


async def get_device_data(params: Optional[Dict[str, Any]] = None):
    ram_info = psutil.virtual_memory()
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat()

    manufacturer, model, serial_number = __get_device_identifiers()

    return {
        "computer_name": platform.node(),
        "ram": f"{round(float(ram_info.total) / (1024 ** 3), 2)} GB",
        "manufacturer": manufacturer,
        "model": model,
        "last_boot_time": boot_time,
        "serial_number": serial_number,
    }


def __get_device_identifiers():
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
            return (
                subprocess.check_output(["system_profiler", datatype])
                .decode("utf-8")
                .strip()
            )

        manufacturer = "Apple Inc."
        model = (
            get_system_profiler_data("SPHardwareDataType")
            .split("Model Name:")[1]
            .split("\n")[0]
            .strip()
        )
        serial_number = (
            get_system_profiler_data("SPHardwareDataType")
            .split("Serial Number (system):")[1]
            .split("\n")[0]
            .strip()
        )

    else:
        # Other platforms (e.g., Linux) or fallback implementation
        manufacturer = "Unknown"
        model = "Unknown"
        serial_number = "Unknown"

    return manufacturer, model, serial_number
