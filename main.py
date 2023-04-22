from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from observable import Observer
from tools.toolbox import Toolbox
from tools.FMInfo.fminfo import FMInfo
from tools.Internet_Connection_Tool.internet_connection_tool import InternetConnectionTool
from tools.Azure_Connection_Tool.azure_connection_tool import AzureConnectionTool
from tools.Domain_Connection_Tool.domain_connection_tool import DomainConnectionTool

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

internet_connection_tool = InternetConnectionTool()
domain_connection_tool = DomainConnectionTool()
azure_connection_tool = AzureConnectionTool()
fminfo = FMInfo()

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
    

@app.websocket("/internet_connection/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    observer = WebSocketObserver(websocket)
    internet_connection_tool.attach(observer)
    
    try:
        await internet_connection_tool.monitor_status()
    finally:
        internet_connection_tool.detach(observer)

@app.websocket("/domain_connection/")
async def websocket_domain_endpoint(websocket: WebSocket):
    await websocket.accept()
    observer = WebSocketObserver(websocket)
    domain_connection_tool.attach(observer)

    try:
        await domain_connection_tool.monitor_status()
    finally:
        domain_connection_tool.detach(observer)

@app.websocket("/azure_connection/")
async def websocket_domain_endpoint(websocket: WebSocket):
    await websocket.accept()
    observer = WebSocketObserver(websocket)
    azure_connection_tool.attach(observer)

    try:
        await azure_connection_tool.monitor_status()
    finally:
        azure_connection_tool.detach(observer)

@app.websocket("/fminfo_networking/")
async def websocket_fminfo_endpoint(websocket: WebSocket):
    await websocket.accept()
    observer = WebSocketObserver(websocket)
    fminfo.attach(observer)

    try:
        await fminfo.monitor_networking_data()
    finally:
        fminfo.detach(observer)
