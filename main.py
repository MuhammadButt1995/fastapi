from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import asyncio
import logging
from tools import *
from utils import *


# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set uo Toolbox
toolbox = Toolbox()

# Define tools
tools = {
    "LDAPStatus": {"name": "LADP Data", "description": "Get LDAP details", "icon": "LDAP_icon", "type": ToolType.DATA, "tags": [Tag.IDS], "strategy": getLDAPData},
    "DeviceData": {"name": "My Device Data", "description": "Get current details", "icon": "device_icon", "type": ToolType.DATA, "tags": [Tag.DEVICE], "strategy": getDeviceData},
    "NetworkAdapters": {"name": "Network Adapters", "description": "Get Network Adapters", "icon": "adapters_icon", "type": ToolType.DATA, "tags": [Tag.NETWORK], "strategy": getNetworkAdapters},
    "WifiData": {"name": "Wi-Fi Data Metrics", "description": "Get live Wi-Fi data metrics.", "icon": "wifi_icon", "type": ToolType.DATA, "tags": [Tag.NETWORK], "strategy": getWifiData},
    "ADStatus": {"name": "AD Status", "description": "Get current status to AD/Azure AD", "icon": "AD_icon", "type": ToolType.DATA, "tags": [Tag.IDS], "strategy": getADStatus},
    "TrustedNetworkStatus": {"name": "Trusted Network Status", "description": "Get current network ZPA/VPN status", "icon": "AD_icon", "type": ToolType.DATA, "tags": [Tag.IDS], "strategy": getTrustedNetworkStatus},


    "VPNHelper": {"name": "VPN Helper", "description": "Connect to captive portals", "icon": "AD_icon", "type": ToolType.WIDGET, "tags": [Tag.NETWORK], "strategy": getTrustedNetworkStatus},
    "WifiNotifications": {"name": "Low Wi-Fi Notifications", "description": "Get send alerts when we detect you've been on an unstable wif-fi network.", "icon": "AD_icon", "type": ToolType.SWITCH, "tags": [Tag.NETWORK, Tag.INTERNET], "strategy": getTrustedNetworkStatus},
    "AD-Rebind": {"name": "AD-Rebind", "description": "Automatically get rebound to AD", "icon": "AD_icon", "type": ToolType.ACTION, "tags": [Tag.NETWORK], "strategy": getTrustedNetworkStatus},
   
    
}

# Register tools
for tool_id, properties in tools.items():
    create_and_register_tool(tool_id, properties["name"], properties["description"], properties["icon"], properties["type"], properties["tags"], properties["strategy"], toolbox)


@app.get("/tools/")
async def list_tools():
    return toolbox.list_tools()

@app.get("/tools/execute/{tool_name}/")
async def execute_tool(tool_name: str, method: Optional[str] = None):
    tool: Tool = toolbox.tools.get(tool_name)

    if tool:
        try:
            if method:
                strategy_instance = tool.strategy()
                return strategy_instance.execute(method)
            else:
                strategy_instance = tool.strategy()
                return strategy_instance.execute()
        except Exception as e:
            logging.error(f"Error executing tool {tool.name}: {e}")
            return {"success": False, "response": e}
    else:
        raise HTTPException(status_code=404, detail="Tool not found")
