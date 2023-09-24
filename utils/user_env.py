import subprocess
import platform
import os
import re


def get_logged_in_username():
    """Returns the logged-in username based on the OS."""
    system = platform.system()

    if system == "Windows":
        try:
            result = subprocess.check_output(
                'query user | findstr /C:"Active" | findstr /V "services"',
                shell=True,
                stderr=subprocess.STDOUT,
            ).decode("utf-8")

            # Use regular expression to extract the username
            match = re.search(r">\s*(\w+)", result)
            if match:
                return match.group(1)
            else:
                raise Exception(
                    "Unable to parse username from the command output on Windows."
                )
        except subprocess.CalledProcessError:
            raise Exception(
                "Error executing the command to fetch the logged-in user on Windows."
            )

    elif system == "Darwin":
        try:
            result = subprocess.check_output(
                "who | grep console | awk '{print $1}'", shell=True
            ).decode("utf-8")
            return result.strip()
        except subprocess.CalledProcessError:
            raise Exception(
                "Error executing the command to fetch the logged-in user on macOS."
            )


def get_user_env_var(username, var_name):
    """Returns the value of an environment variable for the given user."""
    # As fetching environment variables for another user is challenging,
    # we are assuming the env variable is the same for the root and the user for simplicity.
    value = os.environ.get(var_name)
    if value is None:
        raise Exception(
            f"Environment variable {var_name} not found for user {username}."
        )
    return value
