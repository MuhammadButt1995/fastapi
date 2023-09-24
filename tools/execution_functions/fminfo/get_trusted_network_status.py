import platform
import time
from typing import Any, Optional, Dict
from pathlib import Path
import plistlib
import winreg
import os
import win32security
import win32profile
from utils.user_env import get_logged_in_username

# Global status dictionary for connection states
status = {
    "ZPA": "You are connected to ZPA.",
    "VPN": "You are connected to VPN.",
    "DISCONNECTED": "Please connect to either ZScaler ZPA or Citrix VPN to get onto a trusted network.",
}

async def windows_connection_status() -> Dict[str, Any]:
    RETRY_COUNT = 3
    logged_in_user = get_logged_in_username()

    for _ in range(RETRY_COUNT):
        try:
            # Get the SID for the logged-in user
            user_sid, _, _ = win32security.LookupAccountName("", logged_in_user)
            sid_string = win32security.ConvertSidToStringSid(user_sid)

            # Connecting to the registry using the user's SID
            registry = winreg.ConnectRegistry(None, winreg.HKEY_USERS)
            zscaler_key_path = os.path.join(sid_string, r"SOFTWARE\Zscaler\App")
            zscaler_key = winreg.OpenKey(registry, zscaler_key_path)
            
            zpa_state, _ = winreg.QueryValueEx(zscaler_key, "ZPA_State")
            znw_state, _ = winreg.QueryValueEx(zscaler_key, "ZNW_State")
            winreg.CloseKey(zscaler_key)
            winreg.CloseKey(registry)

            # Checking the Zscaler's state and returning the appropriate status
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

        except (FileNotFoundError, OSError, winreg.error, IndexError):
            continue

    return {
        "status": "DISCONNECTED",
        "description": status["DISCONNECTED"],
        "rating": "warn",
    }

async def macos_connection_status() -> Dict[str, Any]:
    RETRY_COUNT = 3
    SLEEP_TIME = 0.2
    log_dir = Path("/Library/Application Support/Zscaler")

    for _ in range(RETRY_COUNT):
        try:
            # Reading the ztstatus log file
            log_files = list(log_dir.glob("ztstatus_*.log"))
            if not log_files:
                raise FileNotFoundError("No Zscaler log files found.")

            with log_files[0].open("rb") as f:
                plist_content = plistlib.load(f)

            # Checking the zpn value and returning the appropriate status
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

async def get_trusted_network_status(
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    system = platform.system()

    if system == "Windows":
        return await windows_connection_status()
    else:
        return await macos_connection_status()