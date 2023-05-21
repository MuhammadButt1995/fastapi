from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from observable import Observer
from tools.toolbox import Toolbox
from tools.FMInfo.fminfo import FMInfo
from tools.Internet_Connection_Tool.internet_connection_tool import InternetConnectionTool
from tools.Internet_Details_Tool.internet_details_tool import InternetDetailsTool
from tools.AD_Connection_Tool.ad_connection_tool import ADConnectionTool
from tools.Domain_Connection_Tool.domain_connection_tool import DomainConnectionTool
from observable import Observable

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
toolbox.register_tool(InternetDetailsTool)
toolbox.register_tool(ADConnectionTool)
toolbox.register_tool(DomainConnectionTool)

class WebSocketObserver(Observer):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def update(self, data: any):
        await self.websocket.send_json(data)

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
    
@app.websocket("/tools/{tool_name}/ws")
async def common_websocket_endpoint(tool_name: str, websocket: WebSocket):
    await websocket.accept()
    observer = WebSocketObserver(websocket)

    try:
        tool_class = toolbox.get_tool(tool_name)
        tool_instance = tool_class()
    except KeyError:
        await websocket.send_json({"status": "error", "message": f"Tool '{tool_name}' not found"})
        await websocket.close()
        return

    if not isinstance(tool_instance, Observable):
        await websocket.send_json({"status": "error", "message": f"Tool '{tool_name}' is not observable"})
        await websocket.close()
        return

    tool_instance.add_observer(observer)

    try:
        await tool_instance.monitor_status()
    finally:
        tool_instance.remove_observer(observer)
        await websocket.close()