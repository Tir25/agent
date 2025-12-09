"""
Comprehensive Regression Test Suite
====================================

Tests all capabilities of the Sovereign Agent with various complexity levels:
1. Simple commands
2. Complex natural language
3. Edge cases and error handling
4. Parameter extraction accuracy
5. End-to-end execution

Run: python test_regression.py
"""

import time
import json

print("=" * 80)
print("SOVEREIGN AGENT - COMPREHENSIVE REGRESSION TEST")
print("=" * 80)
print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# =============================================================================
# SETUP
# =============================================================================

from app.core.registry import ToolRegistry
from app.core.router import SemanticRouter
from app.utils.result import CommandResult

from app.services.system.volume import VolumeTool
from app.services.system.brightness import BrightnessTool
from app.services.system.launcher import AppLauncherTool
from app.services.office.word import WordWriterTool
from app.services.office.excel import ExcelReaderTool

# Create registry
registry = ToolRegistry()
registry.register_tool(VolumeTool())
registry.register_tool(BrightnessTool())
registry.register_tool(AppLauncherTool())
registry.register_tool(WordWriterTool())
registry.register_tool(ExcelReaderTool())

# Create router
router = SemanticRouter(registry)

print(f"\nTools Registered: {len(registry)}")
print(f"Model: {router.model}\n")

# =============================================================================
# TEST CATEGORIES
# =============================================================================

# Category 1: VOLUME CONTROL
volume_tests = [
    # (query, expected_tool, expected_param_key, expected_value_or_None)
    ("Set volume to 50", "set_volume", "level", 50),
    ("Volume 75%", "set_volume", "level", 75),
    ("Turn the volume up to 80 percent", "set_volume", "level", 80),
    ("Make it louder, set to 90", "set_volume", "level", 90),
    ("Mute the audio", "set_volume", "mute", True),
    ("Unmute sound", "set_volume", "mute", False),
    ("What's the current volume?", "set_volume", "action", "get"),
    ("Lower volume to 30", "set_volume", "level", 30),
]

# Category 2: BRIGHTNESS CONTROL
brightness_tests = [
    ("Set brightness to 60", "set_brightness", "level", 60),
    ("Brightness 40%", "set_brightness", "level", 40),
    ("Make screen brighter, 100 percent", "set_brightness", "level", 100),
    ("Dim the display to 20", "set_brightness", "level", 20),
    ("Screen brightness 75", "set_brightness", "level", 75),
    ("Get current brightness level", "set_brightness", "action", "get"),
]

# Category 3: APP LAUNCHER
launcher_tests = [
    ("Open Notepad", "launch_app", "app_name", "notepad"),
    ("Launch Chrome", "launch_app", "app_name", "chrome"),
    ("Start calculator", "launch_app", "app_name", "calculator"),
    ("Open Microsoft Word", "launch_app", "app_name", None),  # Any app name ok
    ("Launch the file explorer", "launch_app", "app_name", None),
    ("Open Visual Studio Code", "launch_app", "app_name", None),
    ("Start PowerShell", "launch_app", "app_name", None),
]

# Category 4: WORD DOCUMENTS
word_tests = [
    ("Write hello world in Word", "write_word_doc", "text", None),
    ("Create a Word document with my notes", "write_word_doc", "text", None),
    ("Type a letter in Word saying Dear Sir", "write_word_doc", "text", None),
    ("Open Word and write Meeting Notes", "write_word_doc", "text", None),
    ("Create document: Project Update Report", "write_word_doc", "text", None),
]

# Category 5: EXCEL READING
excel_tests = [
    ("Read Excel file report.xlsx", "read_excel", "filename", None),
    ("Open spreadsheet data.xlsx and read A1 to B10", "read_excel", "range", None),
    ("Get data from sales.xlsx range C1:D20", "read_excel", "filename", None),
    ("Read cells A1 to Z100 from budget.xlsx", "read_excel", "range", None),
]

# Category 6: GENERAL CHAT (should NOT route to tools)
chat_tests = [
    ("What's the weather today?", "general_chat", None, None),
    ("Tell me a joke", "general_chat", None, None),
    ("Who is the president?", "general_chat", None, None),
    ("What time is it?", "general_chat", None, None),
    ("Thank you for your help", "general_chat", None, None),
    ("Hello, how are you?", "general_chat", None, None),
]

# Category 7: EDGE CASES
edge_tests = [
    ("", "general_chat", None, None),  # Empty query
    ("asdfghjkl", "general_chat", None, None),  # Gibberish
    ("Set volume brightness app Word Excel", "general_chat", None, None),  # Confusing - should go to chat
    ("Please help me with my computer", "general_chat", None, None),
]

# =============================================================================
# RUN TESTS
# =============================================================================

def run_test_category(name, tests, verbose=True):
    """Run a category of tests and return results."""
    print(f"\n{'=' * 80}")
    print(f"CATEGORY: {name}")
    print(f"{'=' * 80}")
    
    passed = 0
    failed = 0
    results = []
    
    for i, test in enumerate(tests, 1):
        query = test[0]
        expected_tool = test[1]
        param_key = test[2] if len(test) > 2 else None
        expected_value = test[3] if len(test) > 3 else None
        
        # Route the query
        result = router.route(query)
        actual_tool = result.get("tool_name")
        params = result.get("parameters", {})
        
        # Check tool match
        tool_match = actual_tool == expected_tool
        
        # Check param if specified
        param_match = True
        if param_key and expected_value is not None:
            actual_value = params.get(param_key)
            param_match = actual_value == expected_value
        
        success = tool_match and param_match
        
        if success:
            passed += 1
            status = "✓"
        else:
            failed += 1
            status = "✗"
        
        if verbose:
            query_short = query[:40] + "..." if len(query) > 40 else query
            print(f"  {status} [{i:02d}] '{query_short}'")
            print(f"       → Tool: {actual_tool} (expected: {expected_tool})")
            if param_key:
                print(f"       → Param '{param_key}': {params.get(param_key)} (expected: {expected_value})")
        
        results.append({
            "query": query,
            "expected_tool": expected_tool,
            "actual_tool": actual_tool,
            "params": params,
            "success": success
        })
    
    print(f"\n  Summary: {passed}/{len(tests)} passed ({100*passed/len(tests):.0f}%)")
    return {"passed": passed, "failed": failed, "results": results}

# Run all categories
all_results = {}

all_results["Volume Control"] = run_test_category("VOLUME CONTROL", volume_tests)
all_results["Brightness Control"] = run_test_category("BRIGHTNESS CONTROL", brightness_tests)
all_results["App Launcher"] = run_test_category("APP LAUNCHER", launcher_tests)
all_results["Word Documents"] = run_test_category("WORD DOCUMENTS", word_tests)
all_results["Excel Reading"] = run_test_category("EXCEL READING", excel_tests)
all_results["General Chat"] = run_test_category("GENERAL CHAT (No Tool)", chat_tests)
all_results["Edge Cases"] = run_test_category("EDGE CASES", edge_tests)

# =============================================================================
# EXECUTION TESTS
# =============================================================================

print(f"\n{'=' * 80}")
print("CATEGORY: EXECUTION TESTS (Live Actions)")
print(f"{'=' * 80}")

execution_tests = [
    ("Set volume to 55", {"volume": 55}),
    ("Set brightness to 70", {"brightness": 70}),
]

exec_passed = 0
for query, expected_data in execution_tests:
    print(f"\n  Executing: '{query}'")
    result = router.route_and_execute(query)
    print(f"    Success: {result.success}")
    print(f"    Data: {result.data}")
    
    if result.success:
        data_match = all(result.data.get(k) == v for k, v in expected_data.items())
        if data_match:
            exec_passed += 1
            print(f"    ✓ Execution verified!")
        else:
            print(f"    ✗ Data mismatch")
    else:
        print(f"    ✗ Execution failed: {result.error}")

print(f"\n  Summary: {exec_passed}/{len(execution_tests)} executions successful")

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print(f"\n{'=' * 80}")
print("FINAL REGRESSION TEST SUMMARY")
print(f"{'=' * 80}")

total_passed = sum(r["passed"] for r in all_results.values())
total_failed = sum(r["failed"] for r in all_results.values())
total_tests = total_passed + total_failed

for category, result in all_results.items():
    pct = 100 * result["passed"] / (result["passed"] + result["failed"])
    bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
    print(f"  {category:25} [{bar}] {result['passed']:2}/{result['passed']+result['failed']:2} ({pct:5.1f}%)")

print(f"\n  {'TOTAL':25} {total_passed}/{total_tests} ({100*total_passed/total_tests:.1f}%)")
print(f"\n  Execution Tests: {exec_passed}/{len(execution_tests)}")

if total_passed == total_tests and exec_passed == len(execution_tests):
    print("\n  🎉 ALL TESTS PASSED!")
else:
    print(f"\n  ⚠ Some tests failed - review results above")

print(f"\nCompleted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
