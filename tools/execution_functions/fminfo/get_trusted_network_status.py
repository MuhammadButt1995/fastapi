import platform
import time
from typing import Any, Optional, Dict
from pathlib import Path
import plistlib

# Import functions from user_env.py
from user_env import get_logged_in_username, get_user_env_var

# Global status dictionary for connection states
status = {
    "ZPA": "You are connected to ZPA.",
    "VPN": "You are connected to VPN.",
    "DISCONNECTED": "Please connect to either ZScaler ZPA or Citrix VPN to get onto a trusted network.",
}

# Conditionally import winreg if on Windows
if platform.system() == "Windows":
    import winreg


# Windows-specific function to determine connection status
async def windows_connection_status() -> Dict[str, Any]:
    RETRY_COUNT = 3

    for _ in range(RETRY_COUNT):
        try:
            # Fetch the logged-in username
            logged_in_user = get_logged_in_username()

            # Connecting to the registry based on logged-in user
            registry = winreg.ConnectRegistry(
                f"\\\\{logged_in_user}", winreg.HKEY_CURRENT_USER
            )
            zscaler_key = winreg.OpenKey(registry, r"SOFTWARE\Zscaler\App")
            zpa_state, _ = winreg.QueryValueEx(zscaler_key, "ZPA_State")
            znw_state, _ = winreg.QueryValueEx(zscaler_key, "ZNW_State")
            winreg.CloseKey(zscaler_key)
            winreg.CloseKey(registry)

            if zpa_state == "TUNNEL_FORWARDING":
                return {"status": "ZPA", "description": status["ZPA"], "rating": "ok"}
            elif znw_state == "TRUSTED":
                return {"status": "VPN", "description": status["VPN"], "rating": "ok"}
            else:
                return {
                    "status": "DISCONNECTED",
                    "description": status["DISCONNECTED"],
                    "rating": "warn",
                }

        except (FileNotFoundError, OSError, winreg.error):
            continue

    return {
        "status": "DISCONNECTED",
        "description": status["DISCONNECTED"],
        "rating": "warn",
    }


# macOS-specific function to determine connection status
async def macos_connection_status() -> Dict[str, Any]:
    RETRY_COUNT = 3
    SLEEP_TIME = 0.2

    # Fetch the home directory of the logged-in user
    logged_in_user = get_logged_in_username()
    log_dir = Path(f"/Users/{logged_in_user}/Library/Application Support/Zscaler")

    for _ in range(RETRY_COUNT):
        try:
            log_files = list(log_dir.glob("ztstatus_*.log"))
            if not log_files:
                raise FileNotFoundError("No Zscaler log files found.")

            with log_files[0].open("rb") as f:
                plist_content = plistlib.load(f)

            zpn_val = int(plist_content.get("zpn"))
            if zpn_val == 4:
                return {"status": "ZPA", "description": status["ZPA"], "rating": "ok"}
            elif zpn_val == 3:
                return {"status": "VPN", "description": status["VPN"], "rating": "ok"}
            else:
                return {
                    "status": "DISCONNECTED",
                    "description": status["DISCONNECTED"],
                    "rating": "warn",
                }

        except (FileNotFoundError, OSError, plistlib.InvalidFileException, ValueError):
            time.sleep(SLEEP_TIME)
            continue

    return {
        "status": "DISCONNECTED",
        "description": status["DISCONNECTED"],
        "rating": "warn",
    }


# Main function
async def get_trusted_network_status(
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    system = platform.system()

    if system == "Windows":
        return await windows_connection_status()
    else:
        return await macos_connection_status()
