import speedtest
import os
from typing import Any


async def get_network_speed(**params: Any):
    is_on_vpn = params.get("is_on_vpn")

    if is_on_vpn.lower() == "true":
        proxy = "127.0.0.1:9000"
        os.environ["http_proxy"] = proxy
        os.environ["https_proxy"] = proxy

    s = speedtest.Speedtest(secure=True)

    s.get_best_server()
    s.download()
    s.upload()

    res = s.results.dict()

    # convert speed from bps to Mbps and round to 2 decimal places
    res["download"] = round(res["download"] / 10**6, 2)
    res["upload"] = round(res["upload"] / 10**6, 2)

    return {
        "download_speed": f'{res["download"]} Mbps',
        "upload_speed": f'{res["upload"]} Mbps',
        "ping": f'{res["ping"]} ms',
    }
