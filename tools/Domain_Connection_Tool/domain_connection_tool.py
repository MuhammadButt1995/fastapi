import platform
import subprocess
import re
from tools.base_tool.base_tool import BaseTool


class DomainConnectionTool(BaseTool):
    def __init__(self):
        super().__init__('DomainConnectionTool', 'Check if connected to ZPA or VPN', 'domain_connection_tool.png')

    @staticmethod
    def check_zscaler_connection(system):
        zscaler_process_pattern = re.compile(r'Zscaler')

        if system == 'Windows':
            process_output = subprocess.check_output('tasklist /SVC /FO CSV', shell=True, text=True)
            netstat_output = subprocess.check_output('netstat -b -n', shell=True, text=True)
        elif system == 'Darwin':
            process_output = subprocess.check_output('ps aux', shell=True, text=True)
            netstat_output = subprocess.check_output('netstat -n -p TCP', shell=True, text=True)
        else:
            return False

        if zscaler_process_pattern.search(process_output) and zscaler_process_pattern.search(netstat_output):
            return True

        return False

    @staticmethod
    def execute():
        system = platform.system()
        connection_status = {"zscaler_authenticated": False}

        if system == "Windows" or system == "Darwin":
            connection_status["zscaler_authenticated"] = DomainConnectionTool.check_zscaler_connection(system)

        return connection_status