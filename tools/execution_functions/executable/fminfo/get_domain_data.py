import os
import subprocess
import platform
from datetime import datetime
import re
from typing import Any


async def get_domain_data(**params: Any):
    try:
        if platform.system() == "Windows":
            domain = os.environ.get("USERDOMAIN")
            user = os.environ.get("USERNAME")
            last_logon_output = (
                subprocess.check_output(
                    'net user %s /domain | findstr /C:"Last logon"' % user,
                    shell=True,
                )
                .decode()
                .strip()
            )
            last_logon_str = (
                re.search(r"Last logon(.*)", last_logon_output).group(1).strip()
            )
            last_logon = datetime.strptime(
                last_logon_str, "%m/%d/%Y %I:%M:%S %p"
            ).strftime("%a, %b %d, %Y %I:%M %p")

        elif platform.system() == "Darwin":  # Mac
            domain = (
                subprocess.check_output(
                    'dsconfigad -show | grep "Active Directory Domain"', shell=True
                )
                .decode()
                .strip()
            )
            user = subprocess.check_output("whoami", shell=True).decode().strip()
            last_logon_output = (
                subprocess.check_output("last | grep %s | head -1" % user, shell=True)
                .decode()
                .strip()
            )
            # Assuming the last_logon_output is in the format 'Mon Sep 24 13:35' - adjust if necessary
            last_logon = datetime.strptime(
                last_logon_output, "%a %b %d %H:%M"
            ).strftime("%a, %b %d, %Y %I:%M %p")

        return {
            "Logged_on_Domain": domain,
            "Logged_on_User": user,
            "Last_Logon_Time": last_logon,
        }

    except Exception as e:
        print(e)
        return {
            "Logged_on_Domain": "test domain",
            "Logged_on_User": "test user",
            "Last_Logon_Time": "test logon",
        }
