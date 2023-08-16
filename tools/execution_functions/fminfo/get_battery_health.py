import os
import platform
import plistlib
import psutil
import subprocess
from bs4 import BeautifulSoup
from typing import Any, Dict, Tuple, Union

# --------------------- UTILITY FUNCTIONS --------------------- #


def get_system_architecture() -> Tuple[str, str]:
    """Return the system and architecture."""
    system = platform.system()
    architecture = platform.machine()
    return system, architecture


def get_battery_metrics() -> Tuple[str, bool]:
    """Return current battery metrics: percentage and plugged state."""
    battery = psutil.sensors_battery()
    percent = str(battery.percent)
    plugged = battery.power_plugged
    return percent, plugged


# ----------------- WINDOWS SPECIFIC FUNCTIONS ----------------- #


def get_windows_battery_health() -> Tuple[int, str]:
    """Return battery health metrics for Windows systems."""
    dir_path = r"C:\Temp"
    file_name = "batteryreport.html"
    full_path = os.path.join(dir_path, file_name)

    # Ensure the directory exists
    os.makedirs(dir_path, exist_ok=True)

    # Generate battery report
    subprocess.check_output(f"PowerCfg /batteryreport /output {full_path}")

    try:
        with open(full_path, "r") as file:
            content = file.read()
    except Exception as e:
        raise RuntimeError(f"Error reading battery report file: {e}")

    # Parse battery report using BeautifulSoup
    soup = BeautifulSoup(content, "html.parser")
    table = soup.findAll("table")[1]
    arr = [
        int(td.text.split()[0].replace(",", ""))
        for td in table.findAll("td")
        if "mWh" in td.text
    ]

    # Remove the temporary file
    os.remove(full_path)

    # Calculate battery health
    full_design_capacity = arr[0]
    full_charge_capacity = arr[1]
    battery_health = min(
        round(full_charge_capacity / full_design_capacity, 2) * 100, 100
    )

    # Determine battery health status
    battery_health_status = "healthy" if battery_health >= 75 else "unhealthy"

    return battery_health, battery_health_status


# ----------------- MACOS SPECIFIC FUNCTIONS ----------------- #


def is_mac_intel(architecture: str) -> bool:
    """Check if architecture is Intel-based Mac."""
    return "x86" in architecture.lower()


def is_mac_arm(architecture: str) -> bool:
    """Check if architecture is ARM-based Mac."""
    return "arm" in architecture.lower()


def get_mac_battery_health(architecture: str) -> Tuple[Union[int, str], str]:
    """Return battery health metrics for Mac systems using plistlib (adjusted for data structure)."""
    battery_condition_cmd = subprocess.check_output(
        "system_profiler SPPowerDataType | grep Condition", shell=True
    )
    battery_condition = battery_condition_cmd.decode().split(":")[1].strip()
    battery_health_status = "healthy" if battery_condition == "Normal" else "unhealthy"

    # Fetch plist XML data from ioreg
    xml_data = subprocess.check_output(
        "ioreg -l -a -r -c AppleSmartBattery", shell=True
    )
    battery_data_list = plistlib.loads(xml_data)

    # Assuming the desired data is in the first entry of the list
    if not battery_data_list or not isinstance(battery_data_list, list):
        raise ValueError("Unexpected battery data structure.")

    battery_data = battery_data_list[0]
    
    # Extract battery details
    max_cap = battery_data.get("MaxCapacity", 0)
    design_cap = battery_data.get("DesignCapacity", 0)

    # Calculate battery health
    if design_cap == 0:
        raise ValueError("Design capacity is zero, cannot calculate battery health.")
    
    battery_health = round(max_cap / design_cap, 2) * 100

    return battery_health, battery_health_status


# --------------------- MAIN FUNCTION --------------------- #


async def get_battery_health(**params: Any) -> Dict[str, Union[str, bool]]:
    """Main function to fetch and return battery health details."""
    try:
        system, architecture = get_system_architecture()
        battery_percent, is_plugged = get_battery_metrics()

        if system == "Windows":
            battery_health_percent, battery_health_status = get_windows_battery_health()
        elif system == "Darwin":  # MacOS
            battery_health_percent, battery_health_status = get_mac_battery_health(
                architecture
            )
        else:
            raise ValueError("Unsupported OS")

        description = (
            "Your battery is healthy, which means it's functioning well."
            if battery_health_status == "healthy"
            else "Your battery is unhealthy. This may affect your system's performance. Please contact tech support for assistance."
        )

        rating = {
            "healthy": "ok",
            "unhealthy": "error",
        }[battery_health_status]

        return {
            "battery_health_status": battery_health_status.upper(),
            "battery_health_percentage": str(int(battery_health_percent)) + "%",
            "battery_charge_percentage": battery_percent + "%",
            "is_plugged": is_plugged,
            "description": description,
            "rating": rating,
        }
    except Exception as e:
        return {"error": f"An error occurred while fetching battery details: {e}"}
