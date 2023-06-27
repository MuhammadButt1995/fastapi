import os
import subprocess
import platform
from datetime import datetime

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getLDAPData(ToolExecutionStrategy):

    def get_password_data(self):
        try:
            if platform.system() == 'Windows':
                password_expires_output = subprocess.check_output('net user %s /domain | findstr /C:"Password expires"' % user, shell=True).decode().strip()
                password_expires_str = re.search(r'Password expires(.*)', password_expires_output).group(1).strip()
                password_expires_datetime = datetime.strptime(password_expires_str, '%m/%d/%Y %I:%M:%S %p')
                days_left = (password_expires_datetime - datetime.now()).days
                days_left = 'Today' if days_left == 0 else days_left
                days_or_day = "day" if days_left == 1 else "days"
                password_expires = {
                    'days_left': f'{days_left} {days_or_day}',
                    'datetime': password_expires_datetime.strftime('%a, %b %d, %Y %I:%M %p')
                }

                return {password_expires}

            elif platform.system() == 'Darwin':  # Mac
                return {password_expires}
        
        except Exception as e:
            days_left = 420
            days_or_day = "day" if days_left == 1 else "days"
            return {
                            'days_left': f'{days_left} {days_or_day}' if days_left != "Today" else f'{days_left}',
                            'datetime':"test_datetime"
                            }
                        
            

    def get_domain_data(self):
        try:
            if platform.system() == 'Windows':
                domain = os.environ.get('USERDOMAIN')
                user = os.environ.get('USERNAME')
                last_logon_output = subprocess.check_output('net user %s /domain | findstr /C:"Last logon"' % user, shell=True).decode().strip()
                last_logon_str = re.search(r'Last logon(.*)', last_logon_output).group(1).strip()
                last_logon = datetime.strptime(last_logon_str, '%m/%d/%Y %I:%M:%S %p').strftime('%a, %b %d, %Y %I:%M %p')
              
            elif platform.system() == 'Darwin':  # Mac
                domain = subprocess.check_output('dsconfigad -show | grep "Active Directory Domain"', shell=True).decode().strip()
                user = subprocess.check_output('whoami', shell=True).decode().strip()
                last_logon_output = subprocess.check_output('last | grep %s | head -1' % user, shell=True).decode().strip()
                # Assuming the last_logon_output is in the format 'Mon Sep 24 13:35' - adjust if necessary
                last_logon = datetime.strptime(last_logon_output, '%a %b %d %H:%M').strftime('%a, %b %d, %Y %I:%M %p')
               
            return {
                "Logged_on_Domain": domain,
                "Logged_on_User": user,
                "Last_Logon_Time": last_logon,
            }
        
        except Exception as e:
            return {
                'Logged_on_Domain': 'test domain',
                "Logged_on_User": 'test user',
                "Last_Logon_Time": 'test logon',
            }
        
    

    def execute(self, method):

        methods = {
            "get_password": self.get_password_data(),
            "get_domain_data": self.get_domain_data()
        }

        return methods[method]