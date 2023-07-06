from abc import ABC
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, Callable
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import asyncio
import json
import os
from datetime import datetime
from threading import Lock
import time
from humps import camelize

from tools.execution_functions import (
    get_wifi_data,
    get_ad_status,
    get_disk_usage,
    get_device_data,
    get_domain_data,
    get_password_data,
    get_network_adapters,
    get_trusted_network_status,
)


# Function to delete old logs
def delete_old_logs():
    now = time.time()
    for filename in os.listdir("logs"):
        if filename.endswith(".log"):
            file_path = os.path.join("logs", filename)
            if os.path.getmtime(file_path) < now - 30 * 86400:
                os.remove(file_path)


# Delete old logs
delete_old_logs()

# Set up logging
log_filename = datetime.now().strftime("logs/%Y-%m-%d_%H-%M-%S.log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(log_filename)
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_FILE = "tool_state.json"

if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        saved_state: Dict[str, Any] = json.load(f)
else:
    saved_state: Dict[str, Any] = {}

tool_tasks: Dict[str, asyncio.Task] = {}
tool_results: Dict[str, Any] = {}

lock = Lock()


def convert_dict_keys_to_camel_case(data):
    if isinstance(data, dict):
        return {
            camelize(key): convert_dict_keys_to_camel_case(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_dict_keys_to_camel_case(item) for item in data]
    else:
        return data


@app.middleware("http")
async def log_middleware(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool: "Tool"):
        self.tools[tool.id] = tool

    def get_tool(self, tool_id: str) -> "Tool":
        tool = self.tools.get(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool


tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return tool_registry


class Tool(ABC, BaseModel):
    id: str
    name: Optional[str]
    description: Optional[str]
    icon: Optional[str]
    visible: bool
    execute_func: Callable = None
    save_results: Optional[bool] = False

    @validator("id", pre=True, always=True)
    def check_id(cls, v):
        if not v:
            raise ValueError("id is required")
        return v

    @validator("name", "description", "icon", pre=True, always=True)
    def check_visible(cls, v, values):
        if values.get("visible") and not v:
            raise ValueError(
                "name, description, and icon are required when visible is True"
            )
        return v

    async def execute(
        self,
        params: Optional[Dict[str, Any]] = None,
        background_tasks: BackgroundTasks = None,
    ) -> Dict[str, Any]:
        if self.execute_func:
            result = await self.execute_func(params)
            if self.save_results and result.get("success", False):
                background_tasks.add_task(self.save_result, result)
            return result
        else:
            raise NotImplementedError

    def save_state(self):
        with lock:
            saved_state[self.id] = self.dict(exclude={"execute_func"})
            with open(STATE_FILE, "w") as f:
                json.dump(saved_state, f)

    def save_result(self, result: Dict[str, Any]):
        if self.save_results and result.get("success", False):
            with lock:
                if self.id not in tool_results:
                    tool_results[self.id] = []
                tool_results[self.id].append(
                    {"datetime": datetime.now().isoformat(), "data": result.get("data")}
                )


class ExecutableTool(Tool):
    async def execute(
        self,
        params: Optional[Dict[str, Any]] = None,
        background_tasks: BackgroundTasks = None,
    ) -> Dict[str, Any]:
        return await super().execute(params, background_tasks)


class ToggleTool(Tool):
    state: bool = True
    reexecute_interval: int

    def __init__(self, **data):
        super().__init__(**data)
        self.state = saved_state.get(self.id, {}).get("state", True)
        if self.state:
            tool_tasks[self.id] = asyncio.create_task(self.run())

    async def run(self):
        while self.state:
            result = await self.execute()
            self.save_result(result)
            await asyncio.sleep(self.reexecute_interval / 1000)

    def toggle(self):
        self.state = not self.state
        if self.state:
            tool_tasks[self.id] = asyncio.create_task(self.run())
        else:
            if self.id in tool_tasks:
                tool_tasks[self.id].cancel()
                del tool_tasks[self.id]


class WidgetTool(Tool):
    route: str


async def wifi_notification_func(
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    wifi_signal_results = tool_results.get("wifi-details")
    print("running wifi-signal")
    print(wifi_signal_results)
    if wifi_signal_results and wifi_signal_results[-1]["data"]["overall"] == "low":
        pass
    elif not wifi_signal_results:
        return {"success": False, "error": "No wifi signal results available"}
    return {"success": True}


tool_registry.register(
    ExecutableTool(
        id="wifi-details",
        visible=False,
        execute_func=get_wifi_data,
        save_results=True,
    )
)

tool_registry.register(
    ExecutableTool(
        id="ad-status",
        visible=False,
        execute_func=get_ad_status,
    )
)

tool_registry.register(
    ExecutableTool(
        id="device-data",
        visible=False,
        execute_func=get_device_data,
    )
)

tool_registry.register(
    ExecutableTool(
        id="disk-usage",
        visible=False,
        execute_func=get_disk_usage,
    )
)


tool_registry.register(
    ExecutableTool(
        id="password-data",
        visible=False,
        execute_func=get_password_data,
    )
)

tool_registry.register(
    ExecutableTool(
        id="domain-data",
        visible=False,
        execute_func=get_domain_data,
    )
)

tool_registry.register(
    ExecutableTool(
        id="network-adapters", visible=False, execute_func=get_network_adapters
    )
)

tool_registry.register(
    ExecutableTool(
        id="trusted-network-status",
        visible=False,
        execute_func=get_trusted_network_status,
    )
)


tool_registry.register(
    ToggleTool(
        id="low-wifi-notifs",
        name="Low Wi-Fi Notifications",
        description="You'll get an notification when your Wi-Fi signal hasn't been reliable for over a period of 30 consecutive minutes.",
        icon="notification_icon",
        visible=True,
        execute_func=wifi_notification_func,
        reexecute_interval=5000,
    )
)


@app.get("/tools")
async def get_tools(tool_registry: ToolRegistry = Depends(get_tool_registry)):
    return convert_dict_keys_to_camel_case(
        {
            name: tool.dict(exclude={"execute_func"})
            for name, tool in tool_registry.tools.items()
            if tool.visible
        }
    )


@app.get("/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    params: Optional[Dict[str, Any]] = None,
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    background_tasks: BackgroundTasks = None,
):
    tool = tool_registry.get_tool(tool_name)
    result = await tool.execute(params, background_tasks)
    camelized_result = convert_dict_keys_to_camel_case(result)
    return JSONResponse(camelized_result)


@app.get("/tools/{tool_name}/toggle")
async def toggle_tool(
    tool_name: str,
    tool_registry: ToolRegistry = Depends(get_tool_registry),
    background_tasks: BackgroundTasks = None,
):
    tool = tool_registry.get_tool(tool_name)
    if not isinstance(tool, ToggleTool):
        raise HTTPException(status_code=404, detail="Toggle tool not found")
    tool.toggle()
    background_tasks.add_task(tool.save_state)
    return {"success": True}


@app.on_event("startup")
async def startup_event():
    for tool in tool_registry.tools.values():
        if isinstance(tool, ToggleTool) and tool.state:
            await tool.execute()


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"Error: {exc.detail}")
    return JSONResponse(
        success=False,
        status_code=exc.status_code,
        data={"detail": exc.detail},
    )
