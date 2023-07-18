import psutil
import arrow
from typing import Any, Optional, Dict


async def get_last_boottime(params: Optional[Dict[str, Any]] = None):
    try:
        boot_time = arrow.get(psutil.boot_time())
        boot_time_str = boot_time.format("MM/DD/YY hh:mm:ss A")

        days_since_boot = (arrow.now() - boot_time).days

        if days_since_boot == 0:
            days_since_boot = "TODAY"
        elif days_since_boot == 1:
            days_since_boot = "1 day ago"
        else:
            days_since_boot = f"{days_since_boot} days ago"

        if (
            days_since_boot == "TODAY"
            or days_since_boot == "1 day ago"
            or int(days_since_boot.split()[0]) <= 7
        ):
            rating = "ok"
        elif "1 day ago" < days_since_boot < "10 days ago":
            rating = "warn"
        else:
            rating = "error"

        description = (
            f"Your machine was last rebooted on {boot_time_str}. "
        )

        return {
            "last_boot_time": boot_time_str,
            "days_since_boot": days_since_boot,
            "rating": rating,
            "description": description,
        }

    except Exception as e:
        print(e)
