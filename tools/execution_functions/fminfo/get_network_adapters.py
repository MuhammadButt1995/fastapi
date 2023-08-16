import psutil
import socket
import re
from typing import Any, Dict


# Dictionary to provide intuitive meanings for both Mac and Windows interfaces
interface_patterns = {
    r"lo[0-9]*$": "Local Loopback",
    r"en[0-9]*$": "Primary Network Interface",
    r"utun[0-9]*$": "VPN/Tunnel Interface",
    r"Ethernet": "Wired Connection",
    r"Wi-Fi": "Wireless Connection",
    r"Loopback Pseudo-Interface [0-9]*$": "Local Loopback",
    r"vEthernet \(.*\)$": "Virtual Ethernet"
}


def get_intuitive_interface_name(interface: str) -> str:
    """Returns a user-friendly name for the network interface."""
    for pattern, description in interface_patterns.items():
        if re.match(pattern, interface):
            return f"{interface} ({description})"
    return interface


async def get_network_adapters(**params: Any) -> Dict[str, Dict[str, str]]:
    try:
        active_adapters = {}

        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET and psutil.net_if_stats()[interface].isup:
                    label = get_intuitive_interface_name(interface)
                    active_adapters[label] = addr.address

        return {
            "active_adapters": active_adapters
        }
    except Exception as e:
        return {"error": str(e)}