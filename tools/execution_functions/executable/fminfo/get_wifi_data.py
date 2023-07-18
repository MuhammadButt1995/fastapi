import asyncio
import subprocess
import platform
from typing import Optional, Dict, Any

quality_scores = {"reliable": 3, "decent": 2, "slow": 1}


def __parse_wifi_data(raw_output):
    lines = raw_output.split("\n")
    wifi_details = {}

    for line in lines:
        if ": " in line:
            key, value = line.split(": ", 1)
            key = key.strip()
            value = value.strip()
            wifi_details[key] = value

    return wifi_details


def __assess_signal_quality(signal_strength):
    if signal_strength > 75:
        return "reliable"
    elif signal_strength > 50:
        return "decent"
    else:
        return "slow"


def __assess_radio_type(radio_type):
    if "ac" in radio_type or "ax" in radio_type:
        return "reliable"
    elif "n" in radio_type:
        return "decent"
    else:
        return "slow"


def __assess_channel_quality(channel):
    if channel in [
        1,
        6,
        11,
    ]:  # These are generally the least congested channels
        return "reliable"
    else:
        return "decent"  # Other channels might be more congested


def __assess_overall_quality(signal_quality, radio_type, channel_quality):
    overall_score = (
        0.6 * quality_scores[signal_quality]
        + 0.3 * quality_scores[radio_type]
        + 0.1 * quality_scores[channel_quality]
    )
    if overall_score > 2.5:
        return "reliable"
    elif overall_score > 1.5:
        return "decent"
    else:
        return "slow"


async def async_check_output(*args):
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode, args, output=stdout, stderr=stderr
        )

    return stdout.decode()


async def get_wifi_data(params: Optional[Dict[str, Any]] = None):
    if platform.system() == "Windows":
        cmd_output = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"]
        ).decode("utf-8")
        parsed_output = __parse_wifi_data(cmd_output)
        signal_strength = int(parsed_output.get("Signal", "0%").rstrip("%"))
        radio_type = parsed_output.get("Radio type", "")
        channel = int(parsed_output.get("Channel", "0"))

        signal_quality = __assess_signal_quality(signal_strength)
        radio_type_quality = __assess_radio_type(radio_type)
        channel_quality = __assess_channel_quality(channel)
        overall_quality = __assess_overall_quality(
            signal_quality, radio_type_quality, channel_quality
        )

        description = {
            "reliable": "Your connection is stable and dependable for your work environment.",
            "decent": "Your connection is adequate for your work environment, however you may experience occasional slowdowns.",
            "slow": "Your connection may make it challenging to maintain a stable online presence.",
        }[overall_quality]

        rating = {
            "reliable": "ok",
            "decent": "warn",
            "slow": "error",
        }[overall_quality]

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
            "description": description,
            "rating": rating,
        }

    elif platform.system() == "Darwin":
        result = subprocess.check_output(
            [
                "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
                "-I",
            ]
        )
        parsed_output = __parse_wifi_data(result.decode("utf-8").strip())
        signal_strength = int(parsed_output.get("agrCtlRSSI", "-100"))
        channel = int(parsed_output.get("channel", "0"))
        last_tx_rate = int(parsed_output.get("lastTxRate", "0"))
        max_rate = int(parsed_output.get("maxRate", "0"))

        signal_quality = __assess_signal_quality(signal_strength)
        radio_type = __assess_radio_type(last_tx_rate / max_rate)
        channel_quality = __assess_channel_quality(channel)
        overall_quality = __assess_overall_quality(
            signal_quality, radio_type, channel_quality
        )

        description = {
            "reliable": "Your connection is stable and dependable for your work environment.",
            "decent": "Your connection is adequate for your work environment, however you may experience occasional slowdowns.",
            "slow": "Your connection may make it challenging to maintain a stable online presence.",
        }[overall_quality]

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
                "description": description,
            }
        }