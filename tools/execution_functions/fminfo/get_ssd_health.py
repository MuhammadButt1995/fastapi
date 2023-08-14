import platform
import subprocess


def __get_system():
    return platform.system()


def __is_windows(system):
    return system == "Windows"


def __is_mac(system):
    return system == "Darwin"


def __get_windows_ssd_health():
    output = subprocess.check_output("wmic diskdrive get status", shell=True).decode()
    health_status = output.strip().split()[-1]
    return "healthy" if health_status == "OK" else "unhealthy"


def __get_mac_ssd_health():
    output = subprocess.check_output(
        "diskutil info / | grep SMART", shell=True
    ).decode()
    health_status = output.strip().split(":")[-1].strip()
    return "healthy" if health_status == "Verified" else "unhealthy"


async def get_ssd_health():
    try:
        system = __get_system()

        if __is_windows(system):
            ssd_health_status = __get_windows_ssd_health()
        elif __is_mac(system):
            ssd_health_status = __get_mac_ssd_health()

        if ssd_health_status == "healthy":
            description = "Your SSD is healthy, which means it's functioning well."
        else:
            description = "Your SSD is unhealthy. This may affect your system's performance. Please contact tech support for assistance."

        rating = {
            "healthy": "ok",
            "unhealthy": "error",
        }[ssd_health_status]

        return {
            "ssd_health_status": ssd_health_status.upper(),
            "description": description,
            "rating": rating,
        }
    except Exception as e:
        print(e)
