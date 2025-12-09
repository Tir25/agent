"""Debug visual query routing - wait for all"""
import time
from app.core.router import SemanticRouter
from app.core.registry import ToolRegistry
from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool
from app.services.system.screen_capture import ScreenCaptureTool
from app.services.ai.vision import VisionTool
from app.services.office.word import WordWriterTool
from app.services.office.excel import ExcelReaderTool

# Build registry like main.py
registry = ToolRegistry()
registry.register_tool(VolumeTool())
registry.register_tool(BrightnessTool())
registry.register_tool(AppLauncherTool())
registry.register_tool(WordWriterTool())
registry.register_tool(ExcelReaderTool())
registry.register_tool(ScreenCaptureTool())
registry.register_tool(VisionTool())

router = SemanticRouter(registry)

# Test 1 visual query
query = "Analyze the image in firefox"
print(f"\nQuery: {query}")
result = router.route(query)
print(f"Tool: {result.get('tool_name')}")
print(f"Params: {result.get('parameters')}")
