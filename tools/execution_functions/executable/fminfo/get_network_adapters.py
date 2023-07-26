import psutil
import socket
from typing import Any


async def get_network_adapters(**params: Any):
    try:
        active_adapters = {}
        inactive_adapters = {}

        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    if psutil.net_if_stats()[interface].isup:
                        active_adapters[interface] = addr.address
                    else:
                        inactive_adapters[interface] = addr.address

        return {
            "active_adapters": active_adapters,
            "inactive_adapters": inactive_adapters,
        }
    except Exception as e:
        print(e)
