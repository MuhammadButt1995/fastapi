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
    r"vEthernet \(.*\)$": "Virtual Ethernet",
}


def get_intuitive_interface_name(interface: str) -> str:
    """Returns a user-friendly name for the network interface."""
    for pattern, description in interface_patterns.items():
        if re.match(pattern, interface):
            return f"{interface} ({description})"
    return interface


def fetch_ip_for_interface(interface_name: str) -> str:
    """Retrieve the IP address assigned to the specified interface."""
    try:
        address_list = psutil.net_if_addrs().get(interface_name, [])
        for address_info in address_list:
            if address_info.family == socket.AF_INET:
                return address_info.address
    except Exception:
        return None
    return None


def interface_is_active(interface_name: str) -> bool:
    """Determine if the specified interface is currently active."""
    try:
        return psutil.net_if_stats()[interface_name].isup
    except Exception:
        return False


def get_active_interfaces_with_ips() -> Dict[str, str]:
    """Collect all active network interfaces along with their IP addresses."""
    active_interfaces = {}
    for interface_name in psutil.net_if_addrs():
        if interface_is_active(interface_name):
            ip_address = fetch_ip_for_interface(interface_name)
            if ip_address:  # Only consider interfaces with an assigned IP address
                user_friendly_name = get_intuitive_interface_name(interface_name)
                active_interfaces[user_friendly_name] = ip_address
    return active_interfaces


def order_interfaces_by_priority(interfaces: Dict[str, str]) -> Dict[str, str]:
    """Reorder the interfaces, prioritizing common user interfaces like Wi-Fi and Ethernet."""
    primary_interface_labels = [
        get_intuitive_interface_name(name) for name in ["Wi-Fi", "Ethernet"]
    ]
    return {
        key: interfaces[key] for key in primary_interface_labels if key in interfaces
    } | interfaces


async def get_network_adapters(**params: Any) -> Dict[str, Dict[str, str]]:
    """Main function to get and order active network interfaces."""
    try:
        active_interfaces = get_active_interfaces_with_ips()
        ordered_active_interfaces = order_interfaces_by_priority(active_interfaces)
        return {"active_adapters": ordered_active_interfaces}
    except Exception as e:
        return {"error": str(e)}
