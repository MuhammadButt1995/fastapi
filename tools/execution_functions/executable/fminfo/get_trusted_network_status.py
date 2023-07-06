import subprocess
import platform
import winreg
from typing import Any, Optional, Dict

status = {
    "ZPA": "You are connected to ZPA.",
    "VPN": "You are connected to VPN.",
    "NOT CONNECTED": "Please connect to either ZScaler ZPA or Citrix VPN to get onto a trusted network.",
}


async def get_trusted_network_status(params: Optional[Dict[str, Any]] = None):
    system = platform.system()

    if system == "Windows":
        try:
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
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
                    "status": "NOT CONNECTED",
                    "description": status["NOT CONNECTED"],
                    "rating": "warn",
                }

        except FileNotFoundError:
            return {
                "status": "NOT CONNECTED",
                "description": status["NOT CONNECTED"],
                "rating": "warn",
            }

    elif system == "Darwin":
        target_url = "zsproxy.company.com"
        output = subprocess.check_output(
            "dscl /Search -read /Users/$(whoami)", shell=True, text=True
        )

        if "OriginalNodeName" in output:
            return {"status": "ZPA", "description": status["ZPA"], "rating": "ok"}
        else:
            flush_command = "sudo killall -HUP mDNSResponder > /dev/null"
            ping_command = (
                f"ping -c 1 {target_url} > /dev/null && echo True || echo False"
            )
            command = f"{flush_command} && {ping_command}"
            output = subprocess.check_output(command, shell=True, text=True).strip()
            if output.lower() == "true":
                return {"status": "VPN", "description": status["VPN"], "rating": "ok"}
            else:
                return {
                    "status": "NOT CONNECTED",
                    "description": status["NOT CONNECTED"],
                    "rating": "warn",
                }
