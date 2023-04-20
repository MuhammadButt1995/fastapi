from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


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
