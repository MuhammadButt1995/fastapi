import psutil
import socket
import time
from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getNetworkAdapters(ToolExecutionStrategy):

    def get_network_adapters(self):
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

            return {"active_adapters": active_adapters, "inactive_adapters": inactive_adapters}
        except Exception as e:
            print(e)
            

    
        
    def execute(self):
        return self.get_network_adapters()