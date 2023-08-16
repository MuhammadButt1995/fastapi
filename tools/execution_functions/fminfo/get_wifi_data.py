import subprocess
import platform
from typing import Dict, Any

QUALITY_SCORES = {"reliable": 3, "decent": 2, "slow": 1}
QUALITY_DESCRIPTIONS = {
    "reliable": "Your connection is stable and dependable for your work environment.",
    "decent": "Your connection is adequate for your work environment, however you may experience occasional slowdowns.",
    "slow": "Your connection may make it challenging to maintain a stable online presence.",
}
QUALITY_RATINGS = {
    "reliable": "ok",
    "decent": "warn",
    "slow": "error",
}
PREFERRED_CHANNELS = [1, 6, 11]  # Generally the least congested channels
SIGNAL_QUALITY_THRESHOLDS = {"reliable": 75, "decent": 50}
RADIO_TYPE_THRESHOLDS = {"reliable": ["802.11ac", "802.11ax"], "decent": ["802.11n"]}
RADIO_TYPE_RATE_THRESHOLDS = {"reliable": 500, "decent": 150}


def extract_key_value_pairs(raw_output: str) -> Dict[str, str]:
    lines = raw_output.split("\n")
    return {
        key.strip(): value.strip()
        for line in lines
        if ": " in line
        for key, value in [line.split(": ", 1)]
    }


def determine_signal_quality(
    value: int, thresholds: Dict[str, int], metric_type: str
) -> str:
    for quality, threshold in thresholds.items():
        if metric_type == "dBm":
            if value > threshold:
                return quality
        else:
            if value >= threshold:
                return quality
    return "slow"


def determine_channel_quality(channel: int) -> str:
    return "reliable" if channel in PREFERRED_CHANNELS else "decent"


def compute_overall_quality(scores: Dict[str, str]) -> str:
    weights = {"signal": 0.6, "radio_type": 0.3, "channel": 0.1}
    overall_score = sum(
        QUALITY_SCORES[scores[key]] * weight
        for key, weight in weights.items()
        if key in scores
    )
    for quality, threshold in {"reliable": 2.5, "decent": 1.5}.items():
        if overall_score > threshold:
            return quality
    return "slow"


def get_transmission_type_by_rate(rate: int) -> str:
    for quality, threshold in RADIO_TYPE_RATE_THRESHOLDS.items():
        if rate >= threshold:
            return quality
    return "slow"


def fetch_windows_wifi_data() -> Dict[str, Any]:
    cmd = ["netsh", "wlan", "show", "interfaces"]
    try:
        cmd_output = subprocess.check_output(cmd).decode("utf-8")
        parsed_output = extract_key_value_pairs(cmd_output)

        signal_strength = int(parsed_output.get("Signal", "0%").rstrip("%"))
        radio_type_string = parsed_output.get("Radio type", "")
        channel = int(parsed_output.get("Channel", "0"))

        scores = {
            "signal": determine_signal_quality(
                signal_strength, SIGNAL_QUALITY_THRESHOLDS, "percentage"
            ),
            "radio_type": next(
                (
                    quality
                    for quality, types in RADIO_TYPE_THRESHOLDS.items()
                    if radio_type_string in types
                ),
                "slow",
            ),
            "channel": determine_channel_quality(channel),
        }

        overall_quality = compute_overall_quality(scores)

        return {
            "signal": {"quality": scores["signal"], "value": signal_strength},
            "radio_type": {"quality": scores["radio_type"], "value": radio_type_string},
            "channel": {"quality": scores["channel"], "value": channel},
            "overall": overall_quality.upper(),
            "description": QUALITY_DESCRIPTIONS[overall_quality],
            "rating": QUALITY_RATINGS[overall_quality],
        }

    except subprocess.CalledProcessError:
        raise Exception(f"Failed to execute command: {' '.join(cmd)}")
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}")


def fetch_macos_wifi_data() -> Dict[str, Any]:
    SIGNAL_QUALITY_THRESHOLDS_DBM = {"reliable": -60, "decent": -70}
    cmd = [
        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport",
        "-I",
    ]

    try:
        cmd_output = subprocess.check_output(cmd).decode("utf-8")
        parsed_output = extract_key_value_pairs(cmd_output)

        signal_strength = int(parsed_output.get("agrCtlRSSI", "-100"))
        last_tx_rate = int(parsed_output.get("lastTxRate", "0"))

        # If the channel contains a comma, split it and consider only the first part
        channel_str = parsed_output.get("channel", "0")
        if "," in channel_str:
            channel_str = channel_str.split(",")[0]

        channel = int(channel_str)

        radio_type = get_transmission_type_by_rate(last_tx_rate)

        scores = {
            "signal": determine_signal_quality(
                signal_strength, SIGNAL_QUALITY_THRESHOLDS_DBM, "dBm"
            ),
            "radio_type": radio_type,
            "channel": determine_channel_quality(channel),
        }

        overall_quality = compute_overall_quality(scores)

        return {
            "signal": {"quality": scores["signal"], "value": signal_strength},
            "radio_type": {
                "quality": scores["radio_type"],
                "value": {"lastTxRate": last_tx_rate},
            },
            "channel": {"quality": scores["channel"], "value": channel},
            "overall": overall_quality.upper(),
            "description": QUALITY_DESCRIPTIONS[overall_quality],
            "rating": QUALITY_RATINGS[overall_quality],
        }

    except subprocess.CalledProcessError:
        raise Exception(f"Failed to execute command: {' '.join(cmd)}")
    except Exception as e:
        raise Exception(f"Unexpected error occurred: {e}")


async def get_wifi_data() -> Dict[str, Any]:
    try:
        os_type = platform.system()
        if os_type == "Windows":
            return fetch_windows_wifi_data()
        elif os_type == "Darwin":
            return fetch_macos_wifi_data()
        else:
            raise NotImplementedError(f"Platform {os_type} not supported.")
    except Exception as e:
        print(f"Error: {e}")
        return {}
