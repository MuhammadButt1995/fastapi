import platform
import subprocess
import asyncio
from tools.base_tool.base_tool import BaseTool
from observable import Observable
from tools.tool_type import ToolType
from tools.tags import Tag

class WiFiDetailsTool(BaseTool, Observable):
    def __init__(self):
        super().__init__(
            name="WiFi Details",
            description="Get live data about the details of your WiFi connection.",
             tool_type=ToolType.AUTO_ENABLED,
            tags=[Tag.INTERNET],
            icon="Wifi"
        )
        Observable.__init__(self)

    def parse_wifi_details(self, raw_output):
        lines = raw_output.split("\n")
        wifi_details = {}

        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                key = key.strip()
                value = value.strip()
                wifi_details[key] = value

        return wifi_details

    def get_wifi_details(self):
        if platform.system() == "Windows":
            cmd_output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"]).decode("utf-8")
            parsed_output = self.parse_wifi_details(cmd_output)
            signal_strength = int(parsed_output.get('Signal', '0%').rstrip('%'))
            radio_type = parsed_output.get('Radio type', '')
            channel = int(parsed_output.get('Channel', '0'))

            # Assess signal strength
            if signal_strength > 75:
                signal_quality = 'reliable'
            elif signal_strength > 50:
                signal_quality = 'decent'
            else:
                signal_quality = 'slow'

            # Assess link quality based on radio type
            if 'ac' in radio_type or 'ax' in radio_type:
                link_quality = 'reliable'
            elif 'n' in radio_type:
                link_quality = 'decent'
            else:
                link_quality = 'slow'

            # Assess channel quality
            if channel in [1, 6, 11]:  # These are generally the least congested channels
                channel_quality = 'reliable'
            else:
                channel_quality = 'decent'  # Other channels might be more congested

            # Combine assessments to give overall quality
            quality_scores = {'reliable': 3, 'decent': 2, 'slow': 1}
            overall_score = (0.6 * quality_scores[signal_quality] + 0.3 * quality_scores[link_quality] + 0.1 * quality_scores[channel_quality])
            if overall_score > 2.5:
                overall_quality = 'reliable'
            elif overall_score > 1.5:
                overall_quality = 'decent'
            else:
                overall_quality = 'slow'

            return {
                "details": {
                "signal": {"quality": signal_quality, "value": signal_strength}, 
                "link": {"quality": link_quality, "value": radio_type if platform.system() == "Windows" else {"lastTxRate": last_tx_rate, "maxRate": max_rate}}, 
                "channel": {"quality": channel_quality, "value": channel}, 
                "overall": overall_quality
                }
            }

        elif platform.system() == "Darwin":
            result = subprocess.check_output(["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"])
            parsed_output = self.parse_wifi_details(result.decode("utf-8").strip())
            signal_strength = int(parsed_output.get('agrCtlRSSI', '-100'))
            channel = int(parsed_output.get('channel', '0'))
            last_tx_rate = int(parsed_output.get('lastTxRate', '0'))
            max_rate = int(parsed_output.get('maxRate', '0'))

            # Assess signal strength
            if signal_strength > -50:
                signal_quality = 'reliable'
            elif signal_strength > -75:
                signal_quality = 'decent'
            else:
                signal_quality = 'slow'

            # Assess link quality based on last transmission rate and maximum rate
            if last_tx_rate >= 0.8 * max_rate:
                link_quality = 'reliable'
            elif last_tx_rate >= 0.5 * max_rate:
                link_quality = 'decent'
            else:
                link_quality = 'slow'

            # Assess channel quality
            if channel in [1, 6, 11]:  # These are generally the least congested channels
                channel_quality = 'reliable'
            else:
                channel_quality = 'decent'  # Other channels might be more congested

            # Combine assessments to give overall quality
            quality_scores = {'reliable': 3, 'decent': 2, 'slow': 1}
            overall_score = (0.6 * quality_scores[signal_quality] + 0.3 * quality_scores[link_quality] + 0.1 * quality_scores[channel_quality])
            if overall_score > 2.5:
                overall_quality = 'reliable'
            elif overall_score > 1.5:
                overall_quality = 'decent'
            else:
                overall_quality = 'slow'

            return {
                "details": {
                "signal": {"quality": signal_quality, "value": signal_strength}, 
                "link": {"quality": link_quality, "value": radio_type if platform.system() == "Windows" else {"lastTxRate": last_tx_rate, "maxRate": max_rate}}, 
                "channel": {"quality": channel_quality, "value": channel}, 
                "overall": overall_quality
                }
            }


    def execute(self):
        return self.get_wifi_details()

    async def monitor_status(self):
        previous_state = None
        while True:
            current_state = self.execute()
            if current_state != previous_state:
                previous_state = current_state
                await self.notify_all(current_state)
            await asyncio.sleep(5)  # Adjust the interval as needed