import subprocess
import platform
from datetime import datetime
import re
from typing import Any
from utils.user_env import get_logged_in_username


async def get_password_data(**params: Any):
    try:
        user = get_logged_in_username()
        if platform.system() == "Windows":
            password_expires_output = (
                subprocess.check_output(
                    'net user %s /domain | findstr /C:"Password expires"' % user,
                    shell=True,
                )
                .decode()
                .strip()
            )
            password_expires_str = (
                re.search(r"Password expires(.*)", password_expires_output)
                .group(1)
                .strip()
            )
            password_expires_datetime = datetime.strptime(
                password_expires_str, "%m/%d/%Y %I:%M:%S %p"
            )
            days_left = (password_expires_datetime - datetime.now()).days
            days_left = "Today" if days_left == 0 else days_left
            days_or_day = "day" if days_left == 1 else "days"

            if days_left == "Today":
                rating = "error"
            elif days_left < 7:
                rating = "error"
            elif days_left < 14:
                rating = "warn"
            else:
                rating = "ok"

            password_expires = {
                "days_left": f"{days_left} {days_or_day}",
                "datetime": password_expires_datetime.strftime(
                    "%a, %b %d, %Y %I:%M %p"
                ),
                "description": f"You have until {password_expires_datetime.strftime('%a, %b %d, %Y %I:%M %p')} to change your password",
                "rating": rating,
            }

            return password_expires

        elif platform.system() == "Darwin":  # Mac
            return password_expires

    except Exception as e:
        print(e)
        days_left = 420
        days_or_day = "day" if days_left == 1 else "days"
        return {
            "days_left": f"{days_left} {days_or_day}"
            if days_left != "Today"
            else f"{days_left}",
            "datetime": "test_datetime",
            "description": f"You have until {datetime.now().strftime('%a, %b %d, %Y %I:%M %p')} to change your password",
            "rating": "ok",
        }
