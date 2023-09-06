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
            domain_output = (
                subprocess.check_output(
                    'dsconfigad -show | grep "Active Directory Domain"', shell=True
                )
                .decode()
                .strip()
            )
            domain = domain_output.split("=")[-1].strip()
            user = subprocess.check_output("whoami", shell=True).decode().strip()
            last_logon_output = (
                subprocess.check_output("last | grep %s | head -1" % user, shell=True)
                .decode()
                .strip()
            )
            print(
                f"Debug: last_logon_output='{last_logon_output}'"
            )  # Debugging statement
            # Extracting required data using regex
            match = re.search(
                r"(\w{3}\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2})", last_logon_output
            )
            if match:
                last_logon_str = match.group(1)
                # Parse the datetime but without year information
                last_logon_datetime = datetime.strptime(
                    last_logon_str, "%a %b %d %H:%M"
                )

                # Set the year to the current year
                current_year = datetime.now().year
                last_logon_datetime = last_logon_datetime.replace(year=current_year)

                # Format it as a string
                last_logon = last_logon_datetime.strftime("%a, %b %d, %Y %I:%M %p")
            else:
                raise ValueError("Unexpected format for 'last' command output")

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
