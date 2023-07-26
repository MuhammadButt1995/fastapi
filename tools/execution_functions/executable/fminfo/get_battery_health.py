import os
import platform
import psutil
import subprocess
from bs4 import BeautifulSoup
from typing import Any


def __check_user_device():
    system = platform.system()
    architecture = platform.machine()

    if system == "Darwin":
        if "arm" in architecture or "Arm" in architecture:
            return "macarm"
        elif "x86" in architecture:
            return "macint"
    elif system == "Windows":
        return "win"

    raise Exception(
        f"Cannot determine system or architecture: {system}, {architecture}"
    )


def __get_battery_health(user_device):
    dir = r"C:\Temp\batteryreport.html"
    if user_device == "win":
        subprocess.check_output(f"PowerCfg /batteryreport /output {dir}")

        try:
            with open(dir, "r") as file:
                content = file.read()
        except Exception as e:
            print("File Error: {}".format(e))
            return None, None

        try:
            soup = BeautifulSoup(content, "html.parser")
            table = soup.findAll("table")[1]
            arr = []
            for td in table.findAll("td"):
                if "mWh" in td.text:
                    arr.append(int(td.text.split()[0].replace(",", "")))
            full_design_capacity = arr[0]
            full_charge_capacity = arr[1]
            batteryHealth = round(full_charge_capacity / full_design_capacity, 2) * 100
            os.remove(dir)

            if batteryHealth >= 75:
                batteryHealthStatus = "good"
            else:
                batteryHealthStatus = "bad"

            if (
                batteryHealth > 100
            ):  # new batteries are not calibrated properly, so may be a little over 100
                batteryHealth = 100

            return batteryHealth, batteryHealthStatus
        except Exception as e:
            print("Logic Error + {}".format(e))
            return None, None

    elif user_device == "macint":
        try:
            battery_condition_cmd = subprocess.check_output(
                "system_profiler SPPowerDataType | grep Condition", shell=True
            )
            battery_condition = battery_condition_cmd.decode().split(":")[1].strip()

            batteryHealthStatus = "good" if battery_condition == "Normal" else "bad"

            max_cap_command = subprocess.check_output(
                "ioreg -l -w0 | grep MaxCapacity | sed - E 's/.*\"MaxCapacity\" *= *([0-9]+).*/\1/'",
                shell=True,
            )
            max_cap = int(max_cap_command.decode().split(" = ")[1][:4])

            design_cap_cmd = subprocess.check_output(
                "ioreg -l -w0 | grep DesignCapacity | tail -n 1", shell=True
            )
            design_cap = int(design_cap_cmd.decode().split(" = ")[1][:4])

            batteryHealth = round(max_cap / design_cap, 2) * 100
            return batteryHealth, batteryHealthStatus
        except Exception as e:
            print(e)
    elif user_device == "macarm":
        try:
            battery_condition_cmd = subprocess.check_output(
                'system_profiler SPPowerDataType | grep "Condition"', shell=True
            )
            batteryHealthStatus = battery_condition_cmd.decode().split(":")[1].strip()
            battery_health_cmd = subprocess.check_output(
                'system_profiler SPPowerDataType | grep "Capacity"', shell=True
            )
            batteryHealth = battery_health_cmd.decode().split(":")[1].strip()
            return batteryHealth, batteryHealthStatus
        except Exception as e:
            print(e)

    return None, None


def __get_battery_metrics():
    battery = psutil.sensors_battery()
    plugged = battery.power_plugged
    percent = str(battery.percent)
    plugged = True if plugged else False
    return percent, plugged


async def get_battery_health(**params: Any):
    try:
        user_device = __check_user_device()
        battery_percent, is_plugged = __get_battery_metrics()

        battery_health_percent, battery_health_status = __get_battery_health(
            user_device
        )

        description = "Your Battery's Health is in {} condition".format(
            battery_health_status.lower()
        )
        rating = {
            "good": "ok",
            "bad": "error",
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
        print(e)
