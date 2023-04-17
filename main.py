from typing import List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import platform
import json

from tools.toolbox import Toolbox
from tools.FMInfo.fminfo import FMInfo
from tools.Internet_Connection_Tool.internet_connection_tool import InternetConnectionTool
from tools.Azure_Connection_Tool.azure_connection_tool import AzureConnectionTool
from tools.Domain_Connection_Tool.domain_connection_tool import DomainConnectionTool



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_update(self, data: str):
        for connection in self.active_connections:
            await connection.send_text(data)


connection_manager = ConnectionManager()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

toolbox = Toolbox()

toolbox.register_tool(FMInfo)
toolbox.register_tool(InternetConnectionTool)
toolbox.register_tool(AzureConnectionTool)
toolbox.register_tool(DomainConnectionTool)


@app.get("/tools")
def get_tools():
    return toolbox.list_tools()

@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, request: Request):
    try:
        query_params = request.query_params._dict
        result = toolbox.execute_tool(tool_name, **query_params)
        return {"status": "success", "result": result}
    except KeyError:
        return {"status": "error", "message": f"Tool '{tool_name}' not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)

async def network_change_listener():
    system = platform.system()

    async def notify_clients():
        networking_data = toolbox.tools["FMInfo"].get_networking_data()
        await connection_manager.send_update(json.dumps(networking_data))

    if system == "Windows":
        import win32event
        import win32file
        import win32con

        h_directory = win32file.CreateFileW(
            r"\\.\pipe", 
            win32con.GENERIC_READ, 
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
            None, 
            win32con.OPEN_EXISTING, 
            win32con.FILE_FLAG_BACKUP_SEMANTICS | win32con.FILE_FLAG_OVERLAPPED, 
            None
        )

        async def poll_network_changes():
            while True:
                result = win32event.WaitForSingleObjectEx(h_directory, 5000, True)
                if result == win32con.WAIT_OBJECT_0:
                    await notify_clients()

        await poll_network_changes()

    elif system == "Darwin":
        from AppKit import NSWorkspace
        from PyObjCTools import AppHelper
        from objc import pyobjc_unicode
        import Foundation

        class NetworkObserver(Foundation.NSObject):
            def handleNetworkChange_(self, notification):
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(asyncio.create_task, notify_clients())

        workspace = NSWorkspace.sharedWorkspace()
        nc = workspace.notificationCenter()
        observer = NetworkObserver.new()

        nc.addObserver_selector_name_object_(observer, 'handleNetworkChange:', pyobjc_unicode("NSWorkspaceDidChangeAirPortSettingsNotification"), None)

        AppHelper.runConsoleEventLoop(installInterrupt=True)
        
    else:
        raise NotImplementedError("The network change listener is not implemented for this platform.")

if __name__ == "__main__":
    import uvicorn

    # Start the network change listener
    asyncio.ensure_future(network_change_listener())

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)