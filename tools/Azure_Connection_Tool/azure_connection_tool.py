import platform
import subprocess
from tools.toolbox import BaseTool


class AzureConnectionTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="AzureConnectionTool",
            description="A tool to check if the user and machine are connected to Azure AD.",
            icon="azure_connection_tool.png",
        )

    @staticmethod
    def check_azure_ad_join_status():
        if platform.system() == "Windows":
            result = subprocess.check_output(["dsregcmd", "/status"]).decode("utf-8")
            lines = result.split("\r\n")
            azure_ad_status = {"Machine": {}, "User": {}}

            for line in lines:
                if ": " in line:
                    key, value = line.split(": ", 1)
                    key = key.strip()
                    value = value.strip()

                    if "AzureAdJoined" in key or "WamDefaultSet" in key:
                        azure_ad_status["Machine"][key] = value == "Yes"
                    elif "AzureAdPrt" in key:
                        azure_ad_status["User"][key] = value == "Yes"

            return azure_ad_status

        elif platform.system() == "Darwin":
            # macOS implementation is not provided as Azure AD join is not supported on macOS
            return {"error": "Azure AD join is not supported on macOS"}

    def execute(self):
        return self.check_azure_ad_join_status()
