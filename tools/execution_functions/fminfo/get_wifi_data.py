import subprocess
import platform
from typing import Dict, Any

QUALITY_SCORES = {"reliable": 3, "decent": 2, "slow": 1}
DESCRIPTIONS = {
    "reliable": "Your connection is stable and dependable for your work environment.",
    "decent": "Your connection is adequate for your work environment, however you may experience occasional slowdowns.",
    "slow": "Your connection may make it challenging to maintain a stable online presence.",
}
RATINGS = {
    "reliable": "ok",
    "decent": "warn",
    "slow": "error",
}


def parse_wifi_data(raw_output: str) -> Dict[str, str]:
    lines = raw_output.split("\n")
    wifi_details = {}
    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            wifi_details[key.strip()] = value.strip()
    return wifi_details


def assess_signal_quality(signal_strength: int) -> str:
    if signal_strength > 75:
        return "reliable"
    elif signal_strength > 50:
        return "decent"
    else:
        return "slow"


def assess_radio_type(radio_type: str) -> str:
    if "ac" in radio_type or "ax" in radio_type:
        return "reliable"
    elif "n" in radio_type:
        return "decent"
    else:
        return "slow"


def assess_channel_quality(channel: int) -> str:
    if channel in [1, 6, 11]:  # Generally the least congested channels
        return "reliable"
    else:
        return "decent"


def assess_overall_quality(
    signal_quality: str, radio_type: str, channel_quality: str
) -> str:
    overall_score = (
        0.6 * QUALITY_SCORES[signal_quality]
        + 0.3 * QUALITY_SCORES[radio_type]
        + 0.1 * QUALITY_SCORES[channel_quality]
    )
    if overall_score > 2.5:
        return "reliable"
    elif overall_score > 1.5:
        return "decent"
    else:
        return "slow"


def get_wifi_data_windows() -> Dict[str, Any]:
    try:
        cmd_output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"]
        ).decode("utf-8")
        parsed_output = parse_wifi_data(cmd_output)
        signal_strength = int(parsed_output.get("Signal", "0%").rstrip("%"))
        radio_type = parsed_output.get("Radio type", "")
        channel = int(parsed_output.get("Channel", "0"))

        signal_quality = assess_signal_quality(signal_strength)
        radio_type_quality = assess_radio_type(radio_type)
        channel_quality = assess_channel_quality(channel)
        overall_quality = assess_overall_quality(
            signal_quality, radio_type_quality, channel_quality
        )

        return {
            "signal": {
                "quality": signal_quality,
                "value": signal_strength,
            },
            "radio_type": {
                "quality": radio_type_quality,
                "value": radio_type,
            },
            "channel": {"quality": channel_quality, "value": channel},
            "overall": overall_quality.upper(),
            "description": DESCRIPTIONS[overall_quality],
            "rating": RATINGS[overall_quality],
        }

    except subprocess.CalledProcessError:
        raise Exception("Failed to retrieve WiFi data on Windows.")
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}")


def get_wifi_data_darwin() -> Dict[str, Any]:
    try:
        result = subprocess.check_output(
            [
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I",
            ]
        )
        parsed_output = parse_wifi_data(result.decode("utf-8").strip())
        signal_strength = int(parsed_output.get("agrCtlRSSI", "-100"))
        channel = int(parsed_output.get("channel", "0"))
        last_tx_rate = int(parsed_output.get("lastTxRate", "0"))
        max_rate = int(parsed_output.get("maxRate", "0"))

        signal_quality = assess_signal_quality(signal_strength)
        radio_type = assess_radio_type(last_tx_rate / max_rate)
        channel_quality = assess_channel_quality(channel)
        overall_quality = assess_overall_quality(
            signal_quality, radio_type, channel_quality
        )

        return {
            "details": {
                "signal": {
                    "quality": signal_quality,
                    "value": signal_strength,
                },
                "radio_type": {
                    "quality": radio_type,
                    "value": {"lastTxRate": last_tx_rate, "maxRate": max_rate},
                },
                "channel": {"quality": channel_quality, "value": channel},
                "overall": overall_quality.upper(),
                "description": DESCRIPTIONS[overall_quality],
            }
        }

    except subprocess.CalledProcessError:
        raise Exception("Failed to retrieve WiFi data on macOS.")
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}")


async def get_wifi_data() -> Dict[str, Any]:
    try:
        if platform.system() == "Windows":
            return get_wifi_data_windows()
        elif platform.system() == "Darwin":
            return get_wifi_data_darwin()
        else:
            raise NotImplementedError(f"Platform {platform.system()} not supported.")
    except Exception as e:
        # Handle or log the exception as needed
        print(f"Error: {e}")
        return {}
