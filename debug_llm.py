"""Debug script - check if ChatTool is registered and working"""
import os
import sys

print("=" * 60)
print("LLM INTEGRATION DIAGNOSTIC")
print("=" * 60)

# Step 1: Check if ChatTool can be imported
print("\n[1] ChatTool Import...")
try:
    from app.services.ai.chat import ChatTool
    print("    ✓ ChatTool imported successfully")
except Exception as e:
    print(f"    ✗ Import failed: {e}")
    sys.exit(1)

# Step 2: Check if ChatTool can be instantiated
print("\n[2] ChatTool Instantiation...")
try:
    chat_tool = ChatTool()
    print(f"    ✓ ChatTool created")
    print(f"    Name: {chat_tool.name}")
    print(f"    Model: {chat_tool.model}")
except Exception as e:
    print(f"    ✗ Instantiation failed: {e}")
    sys.exit(1)

# Step 3: Check Registry
print("\n[3] Registry Registration...")
from app.core.registry import ToolRegistry
from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool
from app.services.system.screen_capture import ScreenCaptureTool
from app.services.ai.vision import VisionTool
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

print(f"    Tools registered: {len(registry)}")
chat_in_registry = registry.get_tool("general_chat")
print(f"    ChatTool in registry: {chat_in_registry is not None}")

# Step 4: Check Router
print("\n[4] Router Classification...")
from app.core.router import SemanticRouter
router = SemanticRouter(registry)

test_query = "what is a car?"
print(f"    Query: '{test_query}'")
result = router.route(test_query)
print(f"    Routed to: {result.get('tool_name')}")
print(f"    Parameters: {result.get('parameters')}")

# Step 5: Execute ChatTool directly
print("\n[5] Direct ChatTool Execution...")
if chat_in_registry:
    exec_result = chat_in_registry.execute(query="What is a car?")
    print(f"    Success: {exec_result.success}")
    if exec_result.success:
        response = exec_result.data.get("response", "")
        print(f"    Response: {response[:100]}...")
    else:
        print(f"    Error: {exec_result.error}")
else:
    print("    ✗ ChatTool not in registry!")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
