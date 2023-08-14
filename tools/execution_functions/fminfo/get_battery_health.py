import os
import platform
import psutil
import subprocess
from bs4 import BeautifulSoup
from typing import Any


# Function to get system and architecture
def get_system_architecture():
    system = platform.system()
    architecture = platform.machine()
    return system, architecture


# Function to check if system is Windows
def is_windows(system):
    return system == "Windows"


# Function to check if system is MacOS
def is_mac(system):
    return system == "Darwin"


# Function to check if architecture is ARM-based Mac
def is_mac_arm(architecture):
    return "arm" in architecture.lower()


# Function to check if architecture is Intel-based Mac
def is_mac_intel(architecture):
    return "x86" in architecture.lower()


# Function to get current battery metrics
def get_battery_metrics():
    battery = psutil.sensors_battery()
    plugged = battery.power_plugged
    percent = str(battery.percent)
    plugged = True if plugged else False
    return percent, plugged


# Function to get battery health for Windows systems
def get_windows_battery_health():
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
        print(f"File Error: {e}")
        return None, None

    # Parse battery report
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


# Function to get battery health for Mac systems
def get_mac_battery_health(architecture):
    battery_condition_cmd = subprocess.check_output(
        "system_profiler SPPowerDataType | grep Condition", shell=True
    )
    battery_condition = battery_condition_cmd.decode().split(":")[1].strip()

    battery_health_status = "healthy" if battery_condition == "Normal" else "unhealthy"

    # Different commands for Intel and ARM based Macs
    if architecture == "macint":
        max_cap_command = subprocess.check_output(
            "ioreg -l -w0 | grep MaxCapacity | sed - E 's/.*\"MaxCapacity\" *= *([0-9]+).*/\1/'",
            shell=True,
        )
        max_cap = int(max_cap_command.decode().split(" = ")[1][:4])

        design_cap_cmd = subprocess.check_output(
            "ioreg -l -w0 | grep DesignCapacity | tail -n 1", shell=True
        )
        design_cap = int(design_cap_cmd.decode().split(" = ")[1][:4])

        battery_health = round(max_cap / design_cap, 2) * 100
    elif architecture == "macarm":
        battery_health_cmd = subprocess.check_output(
            'system_profiler SPPowerDataType | grep "Capacity"', shell=True
        )
        battery_health = battery_health_cmd.decode().split(":")[1].strip()

    return battery_health, battery_health_status


# Main function to get battery health
async def get_battery_health(**params: Any):
    try:
        system, architecture = get_system_architecture()
        battery_percent, is_plugged = get_battery_metrics()

        # Different checks for Windows and Mac
        if is_windows(system):
            battery_health_percent, battery_health_status = get_windows_battery_health()
        elif is_mac(system):
            if is_mac_intel(architecture):
                battery_health_percent, battery_health_status = get_mac_battery_health(
                    "macint"
                )
            elif is_mac_arm(architecture):
                battery_health_percent, battery_health_status = get_mac_battery_health(
                    "macarm"
                )

        if battery_health_status == "healthy":
            description = "Your battery is healthy, which means it's functioning well."
        else:
            description = "Your battery is unhealthy. This may affect your system's performance. Please contact tech support for assistance."

        rating = {
            "healthy": "ok",
            "unhealthy": "error",
        }[battery_health_status]

        # Return battery health information
        return {
            "battery_health_status": battery_health_status.upper(),
            "battery_health_percentage": str(int(battery_health_percent)) + "%",
            "battery_charge_percentage": battery_percent + "%",
            "is_plugged": is_plugged,
            "description": description,
            "rating": rating,
        }
    except Exception as e:
        print(e)
