import platform
import subprocess

SSD_STATUS = {"HEALTHY": "healthy", "UNHEALTHY": "unhealthy"}

RATING = {"OK": "ok", "ERROR": "error"}


def get_system_type() -> str:
    """Determine the operating system type."""
    return platform.system()


def get_windows_ssd_health() -> str:
    """Retrieve SSD health status for a Windows system."""
    try:
        output = subprocess.check_output(
            "wmic diskdrive get status", shell=True
        ).decode()
        health_status = output.strip().split()[-1]
        return (
            SSD_STATUS["HEALTHY"] if health_status == "OK" else SSD_STATUS["UNHEALTHY"]
        )
    except subprocess.SubprocessError:
        raise RuntimeError("Failed to retrieve SSD health on Windows.")


def get_mac_ssd_health() -> str:
    """Retrieve SSD health status for a Mac system."""
    try:
        output = subprocess.check_output(
            "diskutil info / | grep SMART", shell=True
        ).decode()
        health_status = output.strip().split(":")[-1].strip()
        return (
            SSD_STATUS["HEALTHY"]
            if health_status == "Verified"
            else SSD_STATUS["UNHEALTHY"]
        )
    except subprocess.SubprocessError:
        raise RuntimeError("Failed to retrieve SSD health on Mac.")


async def get_ssd_health():
    """Asynchronously retrieve SSD health status, description, and rating."""
    try:
        system_type = get_system_type()

        if system_type == "Windows":
            ssd_health_status = get_windows_ssd_health()
        elif system_type == "Darwin":
            ssd_health_status = get_mac_ssd_health()
        else:
            raise NotImplementedError(
                "SSD health check not implemented for this system."
            )

        if ssd_health_status == SSD_STATUS["HEALTHY"]:
            description = "Your SSD is healthy, which means it's functioning well."
            rating = RATING["OK"]
        else:
            description = "Your SSD is unhealthy. This may affect your system's performance. Please contact tech support for assistance."
            rating = RATING["ERROR"]

        return {
            "ssd_health_status": ssd_health_status.upper(),
            "description": description,
            "rating": rating,
        }

    except Exception as e:
        print(e)
        return {
            "ssd_health_status": "ERROR",
            "description": f"An error occurred: {e}",
            "rating": RATING["ERROR"],
        }
