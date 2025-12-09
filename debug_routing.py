"""Debug script - check routing specifically"""
print("=" * 60)
print("ROUTING DIAGNOSTIC")
print("=" * 60)

# Setup registry
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

print(f"Tools: {len(registry)}")

router = SemanticRouter(registry)

# Test routing
test_queries = [
    "what is a car?",
    "what is recipe for french fries?",
    "set volume to 50",
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    result = router.route(query)
    print(f"  -> tool_name: {result.get('tool_name')}")
    print(f"  -> params: {result.get('parameters')}")

print("\n" + "=" * 60)
