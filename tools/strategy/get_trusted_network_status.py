import subprocess
import platform
import winreg

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getTrustedNetworkStatus(ToolExecutionStrategy):

    def get_trusted_network_status(self):
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
                    return {"status": "ZPA"}
                elif znw_state == "TRUSTED":
                    return {"status": "VPN"}
                else:
                    return {"status": "not_connected"}
                
            except FileNotFoundError:
                return {"status": "not_connected"}

        elif system == "Darwin":
            target_url = "zsproxy.company.com"
            output = subprocess.check_output("dscl /Search -read /Users/$(whoami)", shell=True, text=True)
            if "OriginalNodeName" in output:
                return {"status": "ZPA"}
            else:
                flush_command = "sudo killall -HUP mDNSResponder > /dev/null"
                ping_command = f'ping -c 1 {target_url} > /dev/null && echo True || echo False'
                command = f'{flush_command} && {ping_command}'
                output = subprocess.check_output(command, shell=True, text=True).strip()
                if output.lower() == "true":
                    return {"status": "VPN"}
                else:
                    return {"status": "not_connected"}

            

    
        
    def execute(self):
        return self.get_trusted_network_status()