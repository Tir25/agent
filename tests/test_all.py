#!/usr/bin/env python3
"""
The Sovereign Desktop - Comprehensive Test Suite

Tests all implemented modules to verify complete functionality.
"""

import sys
import time
import tempfile
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Colors
class C:
    G = "\033[92m"  # Green
    R = "\033[91m"  # Red
    Y = "\033[93m"  # Yellow
    B = "\033[96m"  # Cyan
    W = "\033[0m"   # Reset
    BOLD = "\033[1m"

results = {"passed": 0, "failed": 0, "skipped": 0}

def ok(msg): 
    print(f"  {C.G}✓{C.W} {msg}")
    results["passed"] += 1

def fail(msg): 
    print(f"  {C.R}✗{C.W} {msg}")
    results["failed"] += 1

def skip(msg): 
    print(f"  {C.Y}○{C.W} {msg}")
    results["skipped"] += 1

def info(msg): 
    print(f"  {C.B}ℹ{C.W} {msg}")

def header(msg): 
    print(f"\n{C.BOLD}{'='*60}{C.W}")
    print(f"{C.BOLD}  {msg}{C.W}")
    print(f"{'='*60}")

def section(msg): 
    print(f"\n{C.BOLD}→ {msg}{C.W}")

# ============================================================================
header("THE SOVEREIGN DESKTOP - FULL TEST SUITE")
# ============================================================================

temp_dir = tempfile.gettempdir()

# ============================================================================
# 1. CORE MODULES
# ============================================================================
section("Core Modules")

try:
    from core import LLMEngine, SemanticRouter, ContextManager, IntentRouter, IntentCategory
    ok("core imports successful (including IntentRouter)")
except Exception as e:
    fail(f"core imports: {e}")

try:
    ctx = ContextManager()
    ctx.add_message("user", "test message")
    msgs = ctx.get_messages()
    if len(msgs) > 0:
        ok("ContextManager works")
    else:
        fail("ContextManager: no messages")
except Exception as e:
    fail(f"ContextManager: {e}")

# IntentRouter test
try:
    from core.router import IntentRouter
    router = IntentRouter()
    result = router.route_intent_sync("Set volume to 50%")
    if result.category == IntentCategory.SYSTEM_CONTROL:
        ok(f"IntentRouter works (action: {result.action})")
    else:
        fail(f"IntentRouter: unexpected category {result.category}")
except Exception as e:
    fail(f"IntentRouter: {e}")

# ============================================================================
# 2. PERCEPTION MODULES  
# ============================================================================
section("Perception Modules")

try:
    from perception import ScreenCapture, VisionProcessor, OCREngine
    ok("perception imports successful")
except Exception as e:
    fail(f"perception imports: {e}")

try:
    from perception.vision import ScreenCapture
    sc = ScreenCapture()
    screenshot = sc.capture_full()
    if screenshot is not None:
        ok(f"ScreenCapture works ({screenshot.width}x{screenshot.height})")
    else:
        fail("ScreenCapture returned None")
except Exception as e:
    fail(f"ScreenCapture: {e}")

# ============================================================================
# 3. ACTUATORS - SYSTEM OPS
# ============================================================================
section("Actuators - System Operations")

try:
    from actuators.system_ops import (
        AudioController, get_brightness, set_brightness,
        launch_app, close_app, focus_window, 
        list_windows, get_running_processes
    )
    ok("system_ops imports successful")
except Exception as e:
    fail(f"system_ops imports: {e}")

# Audio
try:
    audio = AudioController()
    if audio.is_available:
        vol = audio.get_volume()
        ok(f"AudioController works (volume: {vol}%)")
    else:
        skip("AudioController not available")
except Exception as e:
    fail(f"AudioController: {e}")

# Display
try:
    brightness = get_brightness()
    if brightness is not None:
        ok(f"get_brightness works ({brightness}%)")
    else:
        skip("Brightness control not available")
except Exception as e:
    fail(f"get_brightness: {e}")

# Windows
try:
    windows = list_windows()
    ok(f"list_windows works ({len(windows)} windows)")
except Exception as e:
    fail(f"list_windows: {e}")

# Processes
try:
    procs = get_running_processes()
    ok(f"get_running_processes works ({len(procs)} processes)")
except Exception as e:
    fail(f"get_running_processes: {e}")

# App Launch/Close
try:
    result = launch_app("notepad")
    if result["success"]:
        time.sleep(0.5)
        close_result = close_app("notepad")
        if close_result["success"]:
            ok("launch_app/close_app work")
        else:
            fail(f"close_app failed: {close_result['error']}")
    else:
        fail(f"launch_app failed: {result['error']}")
except Exception as e:
    fail(f"launch_app/close_app: {e}")

# ============================================================================
# 4. ACTUATORS - OFFICE OPS
# ============================================================================
section("Actuators - Office Operations")

try:
    from actuators.office_ops import (
        append_text_to_doc, read_word_document,
        write_excel_cell, read_excel_data, COM_AVAILABLE
    )
    ok("office_ops imports successful")
    info(f"COM Available: {COM_AVAILABLE}")
except Exception as e:
    fail(f"office_ops imports: {e}")

if COM_AVAILABLE:
    # Word Test
    try:
        doc_path = os.path.join(temp_dir, "sovereign_test.docx")
        result = append_text_to_doc("Test from Sovereign Desktop", doc_path, visible=False)
        if result["success"]:
            ok("Word append_text_to_doc works")
            # Try reading it back
            read_result = read_word_document(doc_path)
            if read_result["success"] and "Test from Sovereign" in read_result["content"]:
                ok("Word read_word_document works")
            else:
                fail(f"read_word_document: {read_result.get('error', 'content mismatch')}")
        else:
            fail(f"append_text_to_doc: {result['error']}")
    except Exception as e:
        fail(f"Word operations: {e}")

    # Excel Test
    try:
        xlsx_path = os.path.join(temp_dir, "sovereign_test.xlsx")
        result = write_excel_cell(xlsx_path, "A1", "Sovereign Test", visible=False)
        if result["success"]:
            ok("Excel write_excel_cell works")
            # Try reading it back
            read_result = read_excel_data(xlsx_path, "A1")
            if read_result["success"] and read_result["data"][0][0] == "Sovereign Test":
                ok("Excel read_excel_data works")
            else:
                fail(f"read_excel_data: {read_result.get('error', 'data mismatch')}")
        else:
            fail(f"write_excel_cell: {result['error']}")
    except Exception as e:
        fail(f"Excel operations: {e}")
else:
    skip("Word operations (COM not available)")
    skip("Excel operations (COM not available)")

# ============================================================================
# 5. ACTUATORS - WINDOWS CONTROL
# ============================================================================
section("Actuators - Windows Control")

try:
    from actuators.windows_control import WindowsController
    ok("WindowsController import successful")
except Exception as e:
    fail(f"WindowsController import: {e}")

try:
    wc = WindowsController()
    ok("WindowsController instantiated")
except Exception as e:
    fail(f"WindowsController instantiation: {e}")

# ============================================================================
# 6. ACTUATORS - BROWSER AGENT
# ============================================================================
section("Actuators - Browser Agent")

try:
    from actuators.browser_agent import BrowserAgent
    ok("BrowserAgent import successful")
except Exception as e:
    fail(f"BrowserAgent import: {e}")

# ============================================================================
# 7. INTERFACES
# ============================================================================
section("Interfaces")

try:
    from interfaces import TextToSpeech, SpeechToText, VoiceLoop
    ok("interfaces imports successful")
except Exception as e:
    fail(f"interfaces imports: {e}")

# ============================================================================
# 8. UTILS
# ============================================================================
section("Utils")

try:
    from utils import Config, load_config, setup_logging, get_logger
    ok("utils imports successful")
except Exception as e:
    fail(f"utils imports: {e}")

try:
    config = load_config()
    ok(f"load_config works")
except Exception as e:
    fail(f"load_config: {e}")

# ============================================================================
# 9. LLM CONNECTION
# ============================================================================
section("LLM Connection (Ollama)")

try:
    import httpx
    response = httpx.get("http://localhost:11434/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get("models", [])
        ok(f"Ollama running ({len(models)} models)")
        
        # Check for required models
        model_names = [m["name"] for m in models]
        if any("llama3.2" in n for n in model_names):
            ok("llama3.2 model available")
        else:
            skip("llama3.2 model not found")
    else:
        fail(f"Ollama returned status {response.status_code}")
except httpx.ConnectError:
    fail("Ollama not running")
except Exception as e:
    fail(f"Ollama check: {e}")

# Quick LLM inference test
try:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3.2:3b", temperature=0)
    response = llm.invoke("Say 'test passed' in exactly 2 words")
    if response and len(response.content) > 0:
        ok(f"LLM inference works")
    else:
        fail("LLM returned empty response")
except Exception as e:
    fail(f"LLM inference: {e}")

# ============================================================================
# SUMMARY
# ============================================================================
header("TEST SUMMARY")

total = results["passed"] + results["failed"] + results["skipped"]
print(f"\n  {C.G}Passed:  {results['passed']}{C.W}")
print(f"  {C.R}Failed:  {results['failed']}{C.W}")
print(f"  {C.Y}Skipped: {results['skipped']}{C.W}")
print(f"  Total:   {total}")

if results["failed"] == 0:
    print(f"\n  {C.G}{C.BOLD}✓ ALL TESTS PASSED!{C.W}")
    sys.exit(0)
else:
    print(f"\n  {C.R}Some tests failed - review above{C.W}")
    sys.exit(1)
