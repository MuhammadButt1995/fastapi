from tools import Tool

def create_and_register_tool(tool_id, name, description, icon, type, tags, strategy, toolbox):
    tool = Tool(name=name, description=description, icon=icon, type=type, tags=tags, strategy=strategy)
    toolbox.register_tool(tool_id, tool)