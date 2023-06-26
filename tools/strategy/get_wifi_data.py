import subprocess
import platform

from tools.models.tool_execution_strategy import ToolExecutionStrategy

class getWifiData(ToolExecutionStrategy):

    def __init__(self):
        self.quality_scores = {'reliable': 3, 'decent': 2, 'slow': 1}

    def __parse_wifi_data(self, raw_output):
        lines = raw_output.split("\n")
        wifi_details = {}

        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip()
                value = value.strip()
                wifi_details[key] = value

        return wifi_details

    def __assess_signal_quality(self, signal_strength):
        if signal_strength > 75:
            return 'reliable'
        elif signal_strength > 50:
            return 'decent'
        else:
            return 'slow'

    def __assess_radio_type(self, radio_type):
        if 'ac' in radio_type or 'ax' in radio_type:
            return 'reliable'
        elif 'n' in radio_type:
            return 'decent'
        else:
            return 'slow'

    def __assess_channel_quality(self, channel):
        if channel in [1, 6, 11]:  # These are generally the least congested channels
            return 'reliable'
        else:
            return 'decent'  # Other channels might be more congested

    def __assess_overall_quality(self, signal_quality, radio_type, channel_quality):
        overall_score = (0.6 * self.quality_scores[signal_quality] + 0.3 * self.quality_scores[radio_type] + 0.1 * self.quality_scores[channel_quality])
        if overall_score > 2.5:
            return 'reliable'
        elif overall_score > 1.5:
            return 'decent'
        else:
            return 'slow'
        
    def __assess_channel_quality(self, channel):
        if channel in [1, 6, 11]:  # These are generally the least congested channels
            return 'reliable'
        else:
            return 'decent'  # Other channels might be more congested
        
    def __get_wifi_data(self):
        if platform.system() == "Windows":
            cmd_output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("utf-8")
            parsed_output = self.__parse_wifi_data(cmd_output)
            signal_strength = int(parsed_output.get('Signal', '0%').rstrip('%'))
            radio_type = parsed_output.get('Radio type', '')
            channel = int(parsed_output.get('Channel', '0'))

            signal_quality = self.__assess_signal_quality(signal_strength)
            radio_type_quality = self.__assess_radio_type(radio_type)
            channel_quality = self.__assess_channel_quality(channel)
            overall_quality = self.__assess_overall_quality(signal_quality, radio_type_quality, channel_quality)

            return {
                "details": {
                    "signal": {"quality": signal_quality, "value": signal_strength}, 
                    "radio_type": {"quality": radio_type_quality, "value": radio_type}, 
                    "channel": {"quality": channel_quality, "value": channel}, 
                    "overall": overall_quality.upper()
                }
            }
        
        elif platform.system() == "Darwin":
            result = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"])
            parsed_output = self.__parse_wifi_data(result.decode("utf-8").strip())
            signal_strength = int(parsed_output.get('agrCtlRSSI', '-100'))
            channel = int(parsed_output.get('channel', '0'))
            last_tx_rate = int(parsed_output.get('lastTxRate', '0'))
            max_rate = int(parsed_output.get('maxRate', '0'))

            signal_quality = self.__assess_signal_quality(signal_strength)
            radio_type = self.__assess_radio_type(last_tx_rate / max_rate)
            channel_quality = self.__assess_channel_quality(channel)
            overall_quality = self.__assess_overall_quality(signal_quality, radio_type, channel_quality)

            return {
                "details": {
                    "signal": {"quality": signal_quality, "value": signal_strength}, 
                    "radio_type": {"quality": radio_type, "value": {"lastTxRate": last_tx_rate, "maxRate": max_rate}}, 
                    "channel": {"quality": channel_quality, "value": channel}, 
                    "overall": overall_quality.upper()
                }
            }
        
    def execute(self):
        return self.__get_wifi_data()