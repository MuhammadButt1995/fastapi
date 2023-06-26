import os
import subprocess
import platform
from datetime import datetime

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getLDAPData(ToolExecutionStrategy):

    def get_LDAP_data(self):
        try:

            if platform.system() == 'Windows':
                domain = os.environ.get('USERDOMAIN')
                user = os.environ.get('USERNAME')
                last_logon_output = subprocess.check_output('net user %s /domain | findstr /C:"Last logon"' % user, shell=True).decode().strip()
                last_logon = re.search(r'Last logon(.*)', last_logon_output).group(1).strip()
                password_expires_output = subprocess.check_output('net user %s /domain | findstr /C:"Password expires"' % user, shell=True).decode().strip()
                password_expires_str = re.search(r'Password expires(.*)', password_expires_output).group(1).strip()
                password_expires_datetime = datetime.strptime(password_expires_str, '%m/%d/%Y %I:%M %p')
                days_left = (password_expires_datetime - datetime.now()).days
                days_left = 'Today' if days_left == 0 else days_left
                password_expires = {
                    'days_left': days_left,
                    'datetime': password_expires_datetime.strftime('%a, %b %d, %Y %I:%M %p')
                }
            elif platform.system() == 'Darwin':  # Mac
                domain = subprocess.check_output('dsconfigad -show | grep "Active Directory Domain"', shell=True).decode().strip()
                user = subprocess.check_output('whoami', shell=True).decode().strip()
                last_logon = subprocess.check_output('last | grep %s | head -1' % user, shell=True).decode().strip()
                password_expires = 'Not available'
            else:
                domain = 'example.com'
                user = 'unknown'
                last_logon = 'unknown'
                password_expires = 'Not available'

            return {
                "domain": domain,
                "user": user,
                "last_logon": last_logon,
                "password_expires": password_expires,
            }
        
        except Exception as e:
            return {}

    def execute(self):
        return self.get_LDAP_data()