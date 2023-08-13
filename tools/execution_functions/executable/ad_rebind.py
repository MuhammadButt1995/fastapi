from typing import Any
import time


async def ad_rebind(**params: Any):
    print("performing rebind script")

    time.sleep(2)

    return {
        "success": "Yes",
    }
