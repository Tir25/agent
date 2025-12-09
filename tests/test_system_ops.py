#!/usr/bin/env python3
"""
System Operations Module - Comprehensive Test Suite

Tests all functions in actuators/system_ops.py
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Colors for output
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def ok(msg): print(f"  {C.GREEN}✓{C.RESET} {msg}")
def fail(msg): print(f"  {C.RED}✗{C.RESET} {msg}")
def info(msg): print(f"  {C.CYAN}ℹ{C.RESET} {msg}")
def header(msg): print(f"\n{C.BOLD}→ {msg}{C.RESET}")

results = {"passed": 0, "failed": 0}

def test(name, condition):
    if condition:
        ok(name)
        results["passed"] += 1
    else:
        fail(name)
        results["failed"] += 1

# ============================================================================
print(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.RESET}")
print(f"{C.BOLD}  System Operations Module - Test Suite{C.RESET}")
print(f"{C.CYAN}{'='*60}{C.RESET}")

# ============================================================================
# Audio Controller Tests
# ============================================================================
header("AudioController Tests")

from actuators.system_ops import AudioController

audio = AudioController()
test("AudioController initialized", audio.is_available)

if audio.is_available:
    vol = audio.get_volume()
    test("get_volume() returns number", isinstance(vol, (int, float)))
    
    muted = audio.is_muted()
    test("is_muted() returns bool", isinstance(muted, bool))
    
    # Test volume change (save, change, restore)
    original = vol
    success = audio.set_master_volume(45)
    new_vol = audio.get_volume()
    test("set_master_volume() works", success and 44 <= new_vol <= 46)
    
    # Restore
    audio.set_master_volume(original)
    test("Volume restored", abs(audio.get_volume() - original) < 2)
    
    # Test mute (save, mute, unmute, restore)
    original_mute = muted
    audio.mute_master_volume(True)
    test("mute_master_volume(True) works", audio.is_muted() == True)
    audio.mute_master_volume(False)
    test("mute_master_volume(False) works", audio.is_muted() == False)
    
    # Get sessions
    sessions = audio.get_audio_sessions()
    test("get_audio_sessions() returns list", isinstance(sessions, list))
    info(f"Active sessions: {len(sessions)}")

# ============================================================================
# Display Control Tests
# ============================================================================
header("Display Control Tests")

from actuators.system_ops import get_brightness, set_brightness, get_displays

brightness = get_brightness()
test("get_brightness() works", brightness is not None)
info(f"Current brightness: {brightness}%")

displays = get_displays()
test("get_displays() returns list", isinstance(displays, list))
info(f"Detected displays: {len(displays)}")

# ============================================================================
# Application Management Tests  
# ============================================================================
header("Application Management Tests")

from actuators.system_ops import (
    launch_app, close_app, focus_window, 
    list_windows, get_running_processes
)

# List windows
windows = list_windows()
test("list_windows() works", isinstance(windows, list) and len(windows) > 0)
info(f"Open windows: {len(windows)}")

# Get processes
procs = get_running_processes()
test("get_running_processes() works", isinstance(procs, list) and len(procs) > 0)
info(f"Running processes: {len(procs)}")

# Filter processes
chrome = get_running_processes("chrome")
test("Process filter works", isinstance(chrome, list))
info(f"Chrome processes: {len(chrome)}")

# Test launch app (notepad)
info("Testing launch_app('notepad')...")
result = launch_app("notepad")
test("launch_app() returns dict", isinstance(result, dict))
test("launch_app('notepad') succeeded", result.get("success") == True)

if result.get("success"):
    time.sleep(1)  # Wait for notepad to open
    
    # Test focus
    focus_result = focus_window("Notepad")
    test("focus_window() works", focus_result.get("success") == True)
    
    # Close it
    close_result = close_app("notepad")
    test("close_app() works", close_result.get("success") == True)

# ============================================================================
# Summary
# ============================================================================
print(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.RESET}")
print(f"{C.BOLD}  Test Summary{C.RESET}")
print(f"{C.CYAN}{'='*60}{C.RESET}")

total = results["passed"] + results["failed"]
print(f"\n  {C.GREEN}Passed: {results['passed']}/{total}{C.RESET}")
if results["failed"] > 0:
    print(f"  {C.RED}Failed: {results['failed']}/{total}{C.RESET}")
else:
    print(f"\n  {C.GREEN}{C.BOLD}✓ All tests passed!{C.RESET}")

sys.exit(0 if results["failed"] == 0 else 1)
