import psutil
from typing import Any, Optional, Dict


async def get_disk_usage(params: Optional[Dict[str, Any]] = None):
    total_disk_size_gb = psutil.disk_usage("/").total / (1024**3)
    current_disk_usage_gb = psutil.disk_usage("/").used / (1024**3)
    remaining_space_gb = total_disk_size_gb - current_disk_usage_gb

    if remaining_space_gb > 25:
        disk_space_usage = "low"
    elif 10 < remaining_space_gb <= 25:
        disk_space_usage = "medium"
    else:
        disk_space_usage = "high"

    description = f"You are using {current_disk_usage_gb:.2f} GB out of {total_disk_size_gb:.2f} GB. You have {remaining_space_gb:.2f} GB of disk space remaining."
    rating = {
        "low": "ok",
        "medium": "warn",
        "high": "error",
    }[disk_space_usage]

    return {
        "Total_disk_size": f"{total_disk_size_gb:.2f} GB",
        "Current_disk_usage": f"{current_disk_usage_gb:.2f} GB",
        "Remaining_disk_space": f"{remaining_space_gb:.2f} GB",
        "Disk_space_usage": disk_space_usage.upper(),
        "description": description,
        "rating": rating,
    }
