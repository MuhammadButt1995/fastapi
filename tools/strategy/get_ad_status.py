import subprocess
import platform
import re

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getADStatus(ToolExecutionStrategy):

    def get_ad_status(self):
        system = platform.system()

        if system == "Windows":
            result = subprocess.check_output("dsregcmd /status", shell=True, text=True)
            azure_ad_joined = re.search(r"AzureAdJoined\s+:\s+(\w+)", result)
            domain_joined = re.search(r"DomainJoined\s+:\s+(\w+)", result)

            status = {
                "azure_ad_joined": azure_ad_joined.group(1) == "YES" if azure_ad_joined else False,
                "domain_joined": domain_joined.group(1) == "YES" if domain_joined else False,
            }

            status["is_connected"] = status["azure_ad_joined"] and status["domain_joined"]

            return status

        elif system == "Darwin":
            status = {
                "ad_bind": True
            }
            
            status["is_connected"] = status["ad_bind"]

            return status
            

    
        
    def execute(self):
        return self.get_ad_status()