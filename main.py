from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod
from typing import Callable, Any, Optional, Dict, List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import aiofiles.os
import asyncio
import os
from inflection import camelize
from datetime import datetime
import logging
import time
from pathlib import Path
from enum import Enum
import arrow


from tools.execution_functions import (
    get_wifi_data,
    get_trusted_network_status,
    get_ad_status,
    get_domain_data,
    get_device_data,
    get_disk_usage,
    get_network_adapters,
    get_password_data,
    get_last_boottime,
    get_battery_health,
    get_ssd_health,
    get_network_speed,
    ad_rebind,
    import_bookmarks,
    export_bookmarks,
    restart_zscaler,
    reset_dns,
)


class Tag(Enum):
    BROWSER = "Browser"
    NEW_MACHINE = "New Machine"
    NETWORK = "Network"
    WIFI = "WI-FI"
    IDENTITY_SERVICES = "Identity Services"
    DEVICE = "Device"
    CONFIGURATION = ("Configuration",)


LOG_EXPIRY_SECONDS = 30 * 86400
LOG_DIR = "logs/server"

os.makedirs(os.path.join(os.getcwd(), "logs"), exist_ok=True)


def json_log(level: str, event: str, message: str, error: Optional[str] = None):
    log_obj = {"event": event, "message": message}
    if error:
        log_obj["error"] = str(error)

    log_str = json.dumps(log_obj)

    if level.lower() == "info":
        logger.info(log_str)
    elif level.lower() == "error":
        logger.error(log_str)
    elif level.lower() == "warning":
        logger.warning(log_str)
    else:
        logger.debug(log_str)


# Function to delete old logs
def delete_old_logs():
    now = time.time()
    for filename in os.listdir("logs"):
        if filename.endswith(".log"):
            file_path = os.path.join("logs", filename)
            if os.path.getmtime(file_path) < now - LOG_EXPIRY_SECONDS:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    json_log("warning", "File already deleted or not found", file_path)


# Delete old logs
delete_old_logs()

# Set up logging
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
log_filename = os.path.join(
    LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(log_filename)
handler.setFormatter(formatter)

logger.addHandler(handler)


class Tool(BaseModel, ABC):
    id: str = Field(alias="id")
    type: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        pass

    def serialize(self) -> dict:
        data = self.dict(by_alias=True)
        data.pop("execute_func", None)
        return data


class ExecutableTool(Tool):
    def __init__(self, **data):
        super().__init__(**data, type="Command")

    name: Optional[str] = Field(alias="name", default=None)
    description: Optional[str] = Field(alias="description", default=None)
    icon: Optional[str] = Field(alias="icon", default=None)
    visible: bool = Field(alias="visible", default="True")
    execute_func: Callable[..., Any]
    result_mapping: dict = Field(default_factory=dict)
    tags: Optional[List[Tag]] = []

    @validator("name", "description", "icon", "tags", always=True)
    def check_required_fields(cls, v, values):
        if "visible" in values and values["visible"] is True:
            if v is None:
                raise ValueError("value must be defined when visible is True")
        return v

    async def execute(self, **kwargs):
        return await self.execute_func(**kwargs)

    def serialize(self) -> dict:
        data = super().serialize()
        data.pop("visible", None)
        data.pop("result_mapping", None)
        return data


class ToggleTool(Tool):
    def __init__(self, **data):
        super().__init__(**data, type="Toggle")

    name: str = Field(alias="name")
    description: str = Field(alias="description")
    icon: str = Field(alias="icon")
    state: bool = True
    tags: List[Tag] = []

    async def execute(self, **kwargs):
        self.state = not self.state
        await tool_registry.update_state(self.id, self.state)
        return self.state


class UtilityTool(Tool):
    def __init__(self, **data):
        super().__init__(**data, type="Utility")

    name: str = Field(alias="name")
    description: str = Field(alias="description")
    icon: str = Field(alias="icon")
    route: str
    tags: List[Tag] = []

    async def execute(self, **kwargs):
        return {"route": self.route}


class JsonFileManager:
    def __init__(self):
        self.locks: Dict[str, asyncio.Lock] = {}

    def get_lock(self, filename: str) -> asyncio.Lock:
        if filename not in self.locks:
            self.locks[filename] = asyncio.Lock()
        return self.locks[filename]

    async def read_json(self, filename: str) -> Dict:
        async with self.get_lock(filename):
            async with aiofiles.open(filename, "r") as f:
                data: str = await f.read()
                return json.loads(data)

    async def __write_to_file(self, filename: str, data: Dict[str, Any]) -> None:
        directory: str = os.path.dirname(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data))

    async def write_json(self, filename: str, data: Dict[str, Any]) -> None:
        async with self.get_lock(filename):
            await self.__write_to_file(filename, data)

    async def update_json(self, filename: str, update_dict: Dict[str, Any]) -> None:
        async with self.get_lock(filename):
            data: Dict = {}
            if os.path.exists(filename):
                async with aiofiles.open(filename, "r") as f:
                    data = await f.read()
                    data = json.loads(data)
            data.update(update_dict)
            await self.__write_to_file(filename, data)

    @staticmethod
    def convert_dict_keys_to_camel(dict_obj):
        new_dict = {}
        for key in list(dict_obj.keys()):
            new_key = camelize(key, uppercase_first_letter=False)
            if isinstance(dict_obj[key], dict):
                new_dict[new_key] = JsonFileManager.convert_dict_keys_to_camel(
                    dict_obj[key]
                )
            else:
                new_dict[new_key] = dict_obj[key]
        return new_dict

    @staticmethod
    def get_nested_dict_value(data: Dict[str, Any], keys: str) -> Any:
        keys = keys.split(".")
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None
        return data


class ToolRegistry:
    def __init__(self, json_file: str, json_file_manager: JsonFileManager) -> None:
        self.tools: Dict[str, Tool] = {}
        self.json_file: str = json_file
        self.json_file_manager: JsonFileManager = json_file_manager
        self.states: Dict = {}

    async def add_tool(self, tool: Tool) -> None:
        try:
            json_log("info", "add_tool", f"Adding tool {tool.id}")
            self.tools[tool.id] = tool
            if isinstance(tool, ToggleTool):
                tool.state = self.states.get(tool.id, True)
            json_log("info", "add_tool", f"Tool {tool.id} added successfully")
        except Exception as e:
            json_log("error", "error", f"Error adding tool {tool.id}", str(e))
            raise e

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        return self.tools.get(tool_id)

    async def load_states(self) -> None:
        try:
            json_log("info", "load_states", "Loading states")
            if not os.path.exists(self.json_file):
                self.states = {}
                await self.json_file_manager.write_json(self.json_file, self.states)
            else:
                self.states = await self.json_file_manager.read_json(self.json_file)
            json_log("info", "load_states", "States loaded successfully")
        except Exception as e:
            json_log("error", "error", "Error loading states", str(e))
            raise e

    async def update_state(self, tool_id: str, state: bool) -> None:
        try:
            json_log("info", "update_state", f"Updating state for tool {tool_id}")
            self.states[tool_id] = state
            await self.json_file_manager.write_json(self.json_file, self.states)
            json_log(
                "info", "update_state", f"State for tool {tool_id} updated successfully"
            )
        except Exception as e:
            json_log(
                "error", "error", f"Error updating state for tool {tool_id}", str(e)
            )
            raise e


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

json_file_manager = JsonFileManager()
tool_registry = ToolRegistry("tool_states.json", json_file_manager)


def get_current_timestamp():
    return arrow.now().format("MM/DD/YY hh:mm:ss A")


@app.on_event("startup")
async def startup_event() -> None:
    try:
        json_log("info", "startup", "Loading tool states")
        await tool_registry.load_states()

        json_log("info", "startup", "Adding wifi-details tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="wifi-details",
                visible=False,
                execute_func=get_wifi_data,
                result_mapping={
                    "overall_status": "overall",
                    "radio_quality": "signal.value",
                },
            )
        )

        json_log("info", "startup", "Adding network adapters tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="network-adapters", visible=False, execute_func=get_network_adapters
            )
        )

        json_log("info", "startup", "Adding trusted network status tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="trusted-network-status",
                visible=False,
                execute_func=get_trusted_network_status,
            )
        )

        json_log("info", "startup", "Adding ad status tool")
        await tool_registry.add_tool(
            ExecutableTool(id="ad-status", visible=False, execute_func=get_ad_status)
        )

        json_log("info", "startup", "Adding device data tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="device-data", visible=False, execute_func=get_device_data
            )
        )

        json_log("info", "startup", "Adding domain data tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="domain-data", visible=False, execute_func=get_domain_data
            )
        )

        json_log("info", "startup", "Adding password data tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="password-data", visible=False, execute_func=get_password_data
            )
        )

        json_log("info", "startup", "Adding disk usage tool")
        await tool_registry.add_tool(
            ExecutableTool(id="disk-usage", visible=False, execute_func=get_disk_usage)
        )

        json_log("info", "startup", "Adding battery health tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="battery-health", visible=False, execute_func=get_battery_health
            )
        )

        json_log("info", "startup", "Adding SSD Health tool")
        await tool_registry.add_tool(
            ExecutableTool(id="ssd-health", visible=False, execute_func=get_ssd_health)
        )

        json_log("info", "startup", "Adding Network Speed tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="network-speed", visible=False, execute_func=get_network_speed
            )
        )

        json_log("info", "startup", "Adding Export Bookmarks tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="export-bookmarks", visible=False, execute_func=export_bookmarks
            )
        )

        json_log("info", "startup", "Adding Import Bookmarks tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="import-bookmarks", visible=False, execute_func=import_bookmarks
            )
        )

        json_log("info", "startup", "Adding Reset DNS tool")
        await tool_registry.add_tool(
            ExecutableTool(id="reset-dns", visible=False, execute_func=reset_dns)
        )

        json_log("info", "startup", "Adding toggle low Wi-Fi notifications tool")
        await tool_registry.add_tool(
            ToggleTool(
                id="low-wifi-notifs",
                name="Low Wi-Fi Notifications",
                description="Receive notifications if your Wi-Fi is slow for over 15 minutes. Turn on to stay informed.",
                icon="/wifi-notifs.png",
                tags=[Tag.WIFI, Tag.NETWORK],
            )
        )

        json_log("info", "startup", "Adding toggle AD Rebind tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="ad-rebind",
                visible=True,
                name="AD Rebind",
                description="If your Mac device is out of sync with our on-prem Active Directory, use this to quickly get your device back on track.",
                icon="/aad.png",
                tags=[Tag.IDENTITY_SERVICES],
                execute_func=ad_rebind,
            )
        )

        json_log("info", "startup", "Adding restart ZScaler tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="restart-zscaler",
                visible=True,
                name="Restart ZScaler",
                description="Refreshes the ZScaler security services on your device. Use this if you experience connectivity issues or irregularities with ZScaler",
                icon="/zscaler.png",
                tags=[Tag.NETWORK],
                execute_func=restart_zscaler,
            )
        )

        json_log("info", "startup", "Adding VPN Helper tool")
        await tool_registry.add_tool(
            UtilityTool(
                id="vpn-helper",
                name="VPN Helper",
                route="/toolbox/vpn-helper",
                description="Use VPN Helper when you connect your device to a public Wi-Fi network such as networks in coffee shops, airports, hotels, and other locations.",
                icon="/vpn.png",
                tags=[Tag.NETWORK, Tag.WIFI],
            )
        )

        json_log("info", "startup", "Adding Import/Export Bookmarks tool")
        await tool_registry.add_tool(
            UtilityTool(
                id="bookmarks",
                name="Bookmarks Manager",
                route="/toolbox/bookmarks",
                description="Save your current bookmarks to easily import them on a new machine for Chrome or Safari; Edge bookmarks are auto-synced with the cloud.",
                icon="/bookmark.png",
                tags=[Tag.NEW_MACHINE, Tag.BROWSER],
            )
        )

        json_log("info", "startup", "Adding get last boottime tool")
        await tool_registry.add_tool(
            ExecutableTool(
                id="last-boottime", visible=False, execute_func=get_last_boottime
            )
        )
    except Exception as e:
        json_log("error", "error", "Error during startup", str(e))
        raise e


@app.get("/tools")
async def get_tools() -> Dict[str, Any]:
    try:
        # First, filter the tools
        filtered_tools = [
            tool
            for tool in tool_registry.tools.values()
            if isinstance(tool, ExecutableTool)
            and tool.visible
            or isinstance(tool, (ToggleTool, UtilityTool))
        ]

        # Now, sort the tools alphabetically by their name
        sorted_tools = sorted(filtered_tools, key=lambda tool: tool.name)

        # Serialize the sorted tools
        tools_serialized = [tool.serialize() for tool in sorted_tools]

        json_log("info", "get_tools", f"Returned {len(tools_serialized)} tools")
        return {
            "success": True,
            "data": tools_serialized,
            "timestamp": get_current_timestamp(),
        }
    except Exception as e:
        json_log("error", "error", "Error getting tools", str(e))
        return {"success": False, "error": str(e), "timestamp": get_current_timestamp()}


@app.get("/tools/{tool_id}")
async def execute_tool(tool_id: str, request: Request) -> Dict[str, Any]:
    try:
        params = dict(request.query_params)

        json_log("info", "execute_tool", f"Executing tool {tool_id}")
        tool = tool_registry.get_tool(tool_id)
        if not tool:
            json_log("warning", "warning", f"Tool {tool_id} not found")
            return {"success": False, "error": "Tool not found"}

        # Pass the query parameters to the execute function
        result = await tool.execute(**params)
        if isinstance(result, dict) and tool_id != "network-adapters":
            result = JsonFileManager.convert_dict_keys_to_camel(result)

        if isinstance(tool, ExecutableTool) and tool.result_mapping:
            json_result = {
                k: JsonFileManager.get_nested_dict_value(result, v)
                for k, v in tool.result_mapping.items()
            }
            await json_file_manager.write_json(f"logs/data/{tool.id}.json", json_result)

        return {"success": True, "data": result, "timestamp": get_current_timestamp()}
    except Exception as e:
        json_log("error", "error", f"Error executing tool {tool_id}", str(e))
        return {"success": False, "error": str(e), "timestamp": get_current_timestamp()}
