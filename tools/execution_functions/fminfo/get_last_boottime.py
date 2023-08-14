import psutil
import arrow
from typing import Any


async def get_last_boottime(**params: Any):
    try:
        boot_time = arrow.get(psutil.boot_time())
        boot_time_str = boot_time.format("MM/DD/YY hh:mm:ss A")

        days_since_boot = (arrow.now() - boot_time).days

        if days_since_boot == 0:
            days_since_boot_str = "0 days since reboot"
            health_status = "HEALTHY"
        elif days_since_boot == 1:
            days_since_boot_str = "1 day since reboot"
            health_status = "HEALTHY"
        elif days_since_boot <= 7:
            days_since_boot_str = f"{days_since_boot} days since reboot"
            health_status = "HEALTHY"
        elif days_since_boot <= 10:
            days_since_boot_str = f"{days_since_boot} days since reboot"
            health_status = "AT RISK"
        else:
            days_since_boot_str = f"{days_since_boot} days since reboot"
            health_status = "UNHEALTHY"

        if health_status == "HEALTHY":
            rating = "ok"
        elif health_status == "AT RISK":
            rating = "warn"
        else:
            rating = "error"

        description = f"Your machine was last rebooted on {boot_time_str}. "

        return {
            "last_boot_time": boot_time_str,
            "days_since_boot": days_since_boot_str,
            "health_status": health_status,
            "rating": rating,
            "description": description,
        }

    except Exception as e:
        print(e)
