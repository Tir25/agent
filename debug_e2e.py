"""End-to-end test simulating main.py flow"""
print("=" * 60)
print("END-TO-END FLOW TEST")
print("=" * 60)

# Setup exactly like main.py
from app.core.registry import ToolRegistry
from app.core.router import SemanticRouter
from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool
from app.services.system.screen_capture import ScreenCaptureTool
from app.services.ai.vision import VisionTool
from app.services.ai.chat import ChatTool
from app.services.office.word import WordWriterTool
from app.services.office.excel import ExcelReaderTool

registry = ToolRegistry()
registry.register_tool(VolumeTool())
registry.register_tool(BrightnessTool())
registry.register_tool(AppLauncherTool())
registry.register_tool(WordWriterTool())
registry.register_tool(ExcelReaderTool())
registry.register_tool(ScreenCaptureTool())
registry.register_tool(VisionTool())
registry.register_tool(ChatTool())

router = SemanticRouter(registry)

print(f"Tools: {len(registry)}")

# Simulate process_command
user_query = "what is a car?"
print(f"\nUser query: '{user_query}'")

# Step 1: Route
decision = router.route(user_query)
tool_name = decision.get("tool_name")
parameters = decision.get("parameters", {})

print(f"Routed to: {tool_name}")
print(f"Parameters: {parameters}")

# Step 2: Handle based on tool_name
if tool_name == "general_chat":
    print("\n>>> Handling as general_chat")
    
    # Get the ChatTool
    chat_tool = registry.get_tool("general_chat")
    print(f"ChatTool found: {chat_tool is not None}")
    
    if chat_tool:
        print(f"Executing with query='{user_query}'")
        result = chat_tool.execute(query=user_query)
        print(f"Result.success: {result.success}")
        
        if result.success:
            response = result.data.get("response", "No response")
            print(f"\n=== RESPONSE ===")
            print(response)
        else:
            print(f"Error: {result.error}")
    else:
        print("ChatTool NOT found in registry!")
else:
    print(f"Not handled as general_chat, was: {tool_name}")

print("\n" + "=" * 60)
