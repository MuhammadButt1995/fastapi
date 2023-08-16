import platform
import subprocess
import psutil
from typing import Dict, Any

async def get_disk_usage() -> Dict[str, Any]:
    system = platform.system()

    if system == "Windows":
        return fetch_disk_usage_windows()
    elif system == "Darwin":
        return fetch_disk_usage_macos()
    else:
        raise Exception("Unsupported OS")


def fetch_disk_usage_windows() -> Dict[str, Any]:
    partition_info = psutil.disk_usage('C:\\')
    total_disk_size_gb = partition_info.total / (1024**3)
    current_disk_usage_gb = partition_info.used / (1024**3)
    remaining_space_gb = partition_info.free / (1024**3)

    return create_disk_usage_response(total_disk_size_gb, current_disk_usage_gb, remaining_space_gb)


def fetch_disk_usage_macos() -> Dict[str, Any]:
    cmd = ["df", "-h", "/"]
    try:
        stdout = subprocess.check_output(cmd)
        lines = stdout.decode("utf-8").splitlines()

        if len(lines) < 2:
            raise Exception("Unexpected output format from `df` command")

        headers = lines[0].split()
        values = lines[1].split()

        if "Used" in headers and "Size" in headers:
            size_index = headers.index("Size")
            used_index = headers.index("Used")

            total_disk_size_gb = convert_to_gb(values[size_index])
            current_disk_usage_gb = convert_to_gb(values[used_index])
            remaining_space_gb = total_disk_size_gb - current_disk_usage_gb
        else:
            raise Exception("Unexpected column headers in `df` command output")

        return create_disk_usage_response(total_disk_size_gb, current_disk_usage_gb, remaining_space_gb)
    
    except subprocess.CalledProcessError as e:
        return {
            "error": f"An error occurred while fetching disk usage for macOS: {str(e)}"
        }


def convert_to_gb(size_str: str) -> float:
    """Convert sizes from string with possible 'G', 'M', 'K' suffixes to float GB."""
    size_str = size_str.upper().rstrip('I')  # Remove 'I' suffix if present

    conversion_factors = {
        'G': 1,
        'M': 1/1024,
        'K': 1/(1024**2),
    }

    for suffix, factor in conversion_factors.items():
        if size_str.endswith(suffix):
            return float(size_str.rstrip(suffix)) * factor

    return float(size_str) / (1024**3)  # assume bytes if no suffix


def create_disk_usage_response(total_disk_size_gb: float, current_disk_usage_gb: float, remaining_space_gb: float) -> Dict[str, Any]:
    remaining_space_percent = (remaining_space_gb / total_disk_size_gb) * 100
    disk_utilization_health = determine_disk_health(remaining_space_percent)
    
    description = (f"You are using {current_disk_usage_gb:.2f} GB out of {total_disk_size_gb:.2f} GB. "
                   f"You have {remaining_space_gb:.2f} GB ({remaining_space_percent:.2f}%) of disk space remaining.")
    
    rating = {
        "healthy": "ok",
        "at risk": "warn",
        "unhealthy": "error",
    }[disk_utilization_health]

    return {
        "Total_disk_size": f"{total_disk_size_gb:.2f} GB",
        "Current_disk_usage": f"{current_disk_usage_gb:.2f} GB",
        "Remaining_disk_space": f"{remaining_space_gb:.2f} GB",
        "Disk_utilization_health": disk_utilization_health.upper(),
        "description": description,
        "rating": rating,
    }


def determine_disk_health(remaining_space_percent: float) -> str:
    if remaining_space_percent > 25:
        return "healthy"
    elif 15 < remaining_space_percent <= 25:
        return "at risk"
    else:
        return "unhealthy"