import psutil
from typing import Any, Optional, Dict


async def get_disk_usage(params: Optional[Dict[str, Any]] = None):
    total_disk_size_gb = psutil.disk_usage("/").total / (1024**3)
    current_disk_usage_gb = psutil.disk_usage("/").used / (1024**3)
    remaining_space_gb = total_disk_size_gb - current_disk_usage_gb
    remaining_space_percent = (remaining_space_gb / total_disk_size_gb) * 100

    if remaining_space_percent > 25:
        disk_utilization_health = "healthy"
    elif 15 < remaining_space_percent <= 25:
        disk_utilization_health = "suboptimal"
    else:
        disk_utilization_health = "at risk"

    description = f"You are using {current_disk_usage_gb:.2f} GB out of {total_disk_size_gb:.2f} GB. You have {remaining_space_gb:.2f} GB ({remaining_space_percent:.2f}%) of disk space remaining."
    rating = {
        "healthy": "ok",
        "suboptimal": "warn",
        "at risk": "error",
    }[disk_utilization_health]

    return {
        "Total_disk_size": f"{total_disk_size_gb:.2f} GB",
        "Current_disk_usage": f"{current_disk_usage_gb:.2f} GB",
        "Remaining_disk_space": f"{remaining_space_gb:.2f} GB",
        "Disk_utilization_health": disk_utilization_health.upper(),
        "description": description,
        "rating": rating,
    }
