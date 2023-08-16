import platform
import subprocess
import psutil
from typing import Dict, Any

async def get_disk_usage() -> Dict[str, Any]:
    system = platform.system()

    if system == "Windows":
        partition_info = psutil.disk_usage('C:\\')
        total_disk_size_gb = partition_info.total / (1024**3)
        current_disk_usage_gb = partition_info.used / (1024**3)
        remaining_space_gb = partition_info.free / (1024**3)
        
    elif system == "Darwin":  # macOS
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

                size = values[size_index]
                used = values[used_index]
                
                total_disk_size_gb = convert_to_gb(size)
                current_disk_usage_gb = convert_to_gb(used)
                remaining_space_gb = total_disk_size_gb - current_disk_usage_gb
            else:
                raise Exception("Unexpected column headers in `df` command output")
        except subprocess.CalledProcessError as e:
            return {
                "error": f"An error occurred while fetching disk usage for macOS: {str(e)}"
            }
    else:
        raise Exception("Unsupported OS")

    remaining_space_percent = (remaining_space_gb / total_disk_size_gb) * 100

    # Determine disk health
    if remaining_space_percent > 25:
        disk_utilization_health = "healthy"
    elif 15 < remaining_space_percent <= 25:
        disk_utilization_health = "at risk"
    else:
        disk_utilization_health = "unhealthy"
        
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

def convert_to_gb(size_str: str) -> float:
    """Convert sizes from string with possible 'G', 'M', 'K', 'I' suffixes to float GB."""
    size_str = size_str.upper()
    if 'G' in size_str:
        return float(size_str.replace('G', ''))
    if 'M' in size_str:
        return float(size_str.replace('M', '')) / 1024
    if 'K' in size_str:
        return float(size_str.replace('K', '')) / (1024**2)
    if 'I' in size_str:  # Removing the 'I' and assuming it's in bytes for now.
        return float(size_str.replace('I', '')) / (1024**3)
    return float(size_str) / (1024**3)  # assume bytes if no suffix
