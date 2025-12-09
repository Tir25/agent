"""
Test Agent - Comprehensive Integration Test

This script tests the full agent pipeline:
1. ToolRegistry with all tools registered
2. Direct tool execution
3. SemanticRouter intent classification
4. End-to-end route_and_execute

Run: python test_agent.py
"""

print("=" * 70)
print("SOVEREIGN AGENT - INTEGRATION TEST")
print("=" * 70)

# =============================================================================
# SETUP: Import and register all tools
# =============================================================================

print("\n[SETUP] Importing tools...")

from app.core.registry import ToolRegistry
from app.core.router import SemanticRouter
from app.utils.result import CommandResult

# System tools
from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool

# Office tools
from app.services.office.word import WordWriterTool
from app.services.office.excel import ExcelReaderTool

print("  ✓ All tools imported")

# Create and populate registry
registry = ToolRegistry()
registry.register_tool(VolumeTool())
registry.register_tool(BrightnessTool())
registry.register_tool(AppLauncherTool())
registry.register_tool(WordWriterTool())
registry.register_tool(ExcelReaderTool())

print(f"  ✓ Registry: {registry}")
print(f"\n{registry.list_tools()}")

# =============================================================================
# TEST 1: Direct Tool Execution (Office)
# =============================================================================

print("\n" + "-" * 70)
print("TEST 1: Direct Tool Execution (Office)")
print("-" * 70)

# Test WordWriterTool
word_tool = registry.get_tool("write_word_doc")
assert word_tool is not None, "write_word_doc tool not found!"

result = word_tool.execute(text="Hello Sovereign Agent!\n\nThis document was created by TEST 1.")
print(f"\nWordWriterTool result:")
print(f"  Success: {result.success}")
print(f"  Data: {result.data}")

if result.success:
    print("  ✓ TEST 1 PASSED: Word document created!")
else:
    print(f"  ⚠ Note: {result.error}")

# =============================================================================
# TEST 2: Router Intent Classification
# =============================================================================

print("\n" + "-" * 70)
print("TEST 2: Router Intent Classification")
print("-" * 70)

router = SemanticRouter(registry)
print(f"Router model: {router.model}")

# Test query
test_query = "Create a Word document saying Hello World"
print(f"\nQuery: '{test_query}'")

route_result = router.route(test_query)
print(f"\nRoute Result:")
print(f"  tool_name: {route_result.get('tool_name')}")
print(f"  parameters: {route_result.get('parameters')}")

if "error" in route_result:
    print(f"  error: {route_result.get('error')}")

# Verify routing
expected_tool = "write_word_doc"
actual_tool = route_result.get("tool_name")

if actual_tool == expected_tool:
    print(f"\n  ✓ TEST 2 PASSED: Correctly routed to '{expected_tool}'")
else:
    print(f"\n  ⚠ TEST 2: Got '{actual_tool}' instead of '{expected_tool}'")

# =============================================================================
# TEST 3: Additional Routing Tests
# =============================================================================

print("\n" + "-" * 70)
print("TEST 3: Additional Routing Tests")
print("-" * 70)

test_cases = [
    ("Set volume to 75%", "set_volume"),
    ("Make brightness 50", "set_brightness"),
    ("Launch Chrome browser", "launch_app"),
    ("Read data from report.xlsx A1 to B10", "read_excel"),
    ("Write a poem in Word", "write_word_doc"),
]

passed = 0
for query, expected in test_cases:
    result = router.route(query)
    actual = result.get("tool_name")
    status = "✓" if actual == expected else "✗"
    if actual == expected:
        passed += 1
    print(f"  {status} '{query[:35]}...' → {actual}")

print(f"\n  Passed: {passed}/{len(test_cases)}")

# =============================================================================
# TEST 4: End-to-End (Route and Execute)
# =============================================================================

print("\n" + "-" * 70)
print("TEST 4: End-to-End (Route and Execute)")
print("-" * 70)

query = "Set the volume to 65 percent"
print(f"Query: '{query}'")

result = router.route_and_execute(query)
print(f"\nExecution Result:")
print(f"  Success: {result.success}")
print(f"  Data: {result.data}")

if result.success and result.data and "volume" in result.data:
    print(f"\n  ✓ TEST 4 PASSED: Volume set to {result.data['volume']}%")
else:
    print(f"\n  ⚠ TEST 4: {result.error if result.error else 'Unexpected result'}")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE")
print("=" * 70)
