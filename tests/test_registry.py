#!/usr/bin/env python3
"""Test Tool Registry"""

import sys
sys.path.insert(0, ".")

print("=" * 60)
print("TOOL REGISTRY TEST")
print("=" * 60)

from app.core import registry, discover_tools, execute_tool

# Discover all tools
print("\n--- Auto-Discovery ---")
count = discover_tools()
print(f"Discovered {count} tools")

# List tools
print("\n--- Registered Tools ---")
for tool in registry.list_all():
    print(f"  - {tool.name}: {tool.description}")

# Execute by name
print("\n--- Execute by Name ---")
result = execute_tool("set_volume", {"action": "get"})
print(f"  set_volume: {result}")

result = execute_tool("set_brightness", {"action": "get"})
print(f"  set_brightness: {result}")

# Try non-existent tool
result = execute_tool("fake_tool", {})
print(f"  fake_tool: {result}")

# Get tool info for LLM
print("\n--- Tool Info (for LLM) ---")
info = registry.get_tool_info()
for t in info:
    desc = t["description"][:40] if len(t["description"]) > 40 else t["description"]
    print(f"  {t['name']}: {desc}...")

print("\n" + "=" * 60)
print("REGISTRY WORKING!")
print("=" * 60)
