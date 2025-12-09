#!/usr/bin/env python3
"""
The Sovereign Desktop - Installation Verification Script

This script tests all installed components to ensure the environment is properly set up.
"""

import sys
import platform
from pathlib import Path

# Colors for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def success(msg):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {msg}")

def fail(msg, error=""):
    print(f"  {Colors.RED}✗{Colors.RESET} {msg}")
    if error:
        print(f"    {Colors.YELLOW}Error: {error}{Colors.RESET}")

def info(msg):
    print(f"  {Colors.CYAN}ℹ{Colors.RESET} {msg}")

def header(msg):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  {msg}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

def test_section(title):
    print(f"\n{Colors.BOLD}→ {title}{Colors.RESET}")

# ============================================================================
# Test Python Environment
# ============================================================================

def test_python_environment():
    test_section("Python Environment")
    
    results = {}
    
    # Python version
    version = platform.python_version()
    if tuple(map(int, version.split('.')[:2])) >= (3, 11):
        success(f"Python version: {version}")
        results['python_version'] = True
    else:
        fail(f"Python version: {version} (3.11+ required)")
        results['python_version'] = False
    
    # Platform
    info(f"Platform: {platform.system()} {platform.release()}")
    info(f"Executable: {sys.executable}")
    
    # Virtual environment check
    in_venv = sys.prefix != sys.base_prefix
    if in_venv:
        success(f"Running in virtual environment")
    else:
        info("Not running in virtual environment (optional)")
    results['venv'] = in_venv
    
    return results

# ============================================================================
# Test Core AI Packages
# ============================================================================

def test_core_ai():
    test_section("Core AI Packages")
    
    results = {}
    
    # LangChain
    try:
        import langchain
        success(f"langchain: {langchain.__version__}")
        results['langchain'] = True
    except ImportError as e:
        fail("langchain: NOT INSTALLED", str(e))
        results['langchain'] = False
    
    # LangChain Ollama
    try:
        import langchain_ollama
        success(f"langchain-ollama: {langchain_ollama.__version__}")
        results['langchain_ollama'] = True
    except ImportError as e:
        fail("langchain-ollama: NOT INSTALLED", str(e))
        results['langchain_ollama'] = False
    
    # NumPy
    try:
        import numpy
        success(f"numpy: {numpy.__version__}")
        results['numpy'] = True
    except ImportError as e:
        fail("numpy: NOT INSTALLED", str(e))
        results['numpy'] = False
    
    return results

# ============================================================================
# Test Web Automation Packages
# ============================================================================

def test_web_automation():
    test_section("Web Automation Packages")
    
    results = {}
    
    # Browser-Use
    try:
        import browser_use
        success(f"browser-use: {getattr(browser_use, '__version__', 'installed')}")
        results['browser_use'] = True
    except ImportError as e:
        fail("browser-use: NOT INSTALLED", str(e))
        results['browser_use'] = False
    
    # Playwright
    try:
        import playwright
        try:
            from playwright._repo_version import version as pw_version
        except ImportError:
            pw_version = "installed"
        success(f"playwright: {pw_version}")
        results['playwright'] = True
        
        # Check if browsers are installed
        from playwright.sync_api import sync_playwright
        info("Testing Playwright browser...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("about:blank")
                browser.close()
            success("Playwright Chromium: Browser works!")
            results['playwright_browser'] = True
        except Exception as e:
            fail("Playwright browser test failed", str(e))
            results['playwright_browser'] = False
            
    except ImportError as e:
        fail("playwright: NOT INSTALLED", str(e))
        results['playwright'] = False
    
    return results

# ============================================================================
# Test Windows Actuators
# ============================================================================

def test_windows_actuators():
    test_section("Windows Actuators")
    
    results = {}
    
    # PyWinAuto
    try:
        import pywinauto
        success(f"pywinauto: {pywinauto.__version__}")
        results['pywinauto'] = True
    except ImportError as e:
        fail("pywinauto: NOT INSTALLED", str(e))
        results['pywinauto'] = False
    
    # PyWin32
    try:
        import win32api
        import win32con
        import win32gui
        success("pywin32: Installed (win32api, win32con, win32gui)")
        results['pywin32'] = True
    except ImportError as e:
        fail("pywin32: NOT INSTALLED", str(e))
        results['pywin32'] = False
    
    # PyCaw (Audio control)
    try:
        from pycaw.pycaw import AudioUtilities
        success("pycaw: Installed")
        results['pycaw'] = True
    except ImportError as e:
        fail("pycaw: NOT INSTALLED", str(e))
        results['pycaw'] = False
    
    # Screen Brightness Control
    try:
        import screen_brightness_control
        success(f"screen-brightness-control: {screen_brightness_control.__version__}")
        results['screen_brightness'] = True
    except ImportError as e:
        fail("screen-brightness-control: NOT INSTALLED", str(e))
        results['screen_brightness'] = False
    
    # Comtypes
    try:
        import comtypes
        success(f"comtypes: {comtypes.__version__}")
        results['comtypes'] = True
    except ImportError as e:
        fail("comtypes: NOT INSTALLED", str(e))
        results['comtypes'] = False
    
    # PSUtil
    try:
        import psutil
        success(f"psutil: {psutil.__version__}")
        results['psutil'] = True
    except ImportError as e:
        fail("psutil: NOT INSTALLED", str(e))
        results['psutil'] = False
    
    # PyGetWindow
    try:
        import pygetwindow
        success(f"pygetwindow: {pygetwindow.__version__}")
        results['pygetwindow'] = True
    except ImportError as e:
        fail("pygetwindow: NOT INSTALLED", str(e))
        results['pygetwindow'] = False
    
    return results

# ============================================================================
# Test Voice/Interface Packages
# ============================================================================

def test_voice_interface():
    test_section("Voice/Interface Packages")
    
    results = {}
    
    # Vosk (Speech Recognition)
    try:
        import vosk
        success("vosk: Installed")
        results['vosk'] = True
    except ImportError as e:
        fail("vosk: NOT INSTALLED", str(e))
        results['vosk'] = False
    
    # Pyttsx3 (Text to Speech)
    try:
        import pyttsx3
        success("pyttsx3: Installed")
        results['pyttsx3'] = True
    except ImportError as e:
        fail("pyttsx3: NOT INSTALLED", str(e))
        results['pyttsx3'] = False
    
    # PyAudio
    try:
        import pyaudio
        success(f"pyaudio: {pyaudio.__version__}")
        results['pyaudio'] = True
    except ImportError as e:
        fail("pyaudio: NOT INSTALLED (voice input limited)", str(e))
        info("To install: pip install pipwin && pipwin install pyaudio")
        results['pyaudio'] = False
    
    return results

# ============================================================================
# Test Supporting Libraries
# ============================================================================

def test_supporting_libs():
    test_section("Supporting Libraries")
    
    results = {}
    
    packages = [
        ("httpx", "httpx"),
        ("yaml", "pyyaml"),
        ("PIL", "Pillow"),
        ("mss", "mss"),
        ("pyautogui", "pyautogui"),
        ("pynput", "pynput"),
        ("pyperclip", "pyperclip"),
        ("dotenv", "python-dotenv"),
    ]
    
    for module, package in packages:
        try:
            mod = __import__(module)
            version = getattr(mod, '__version__', 'installed')
            success(f"{package}: {version}")
            results[package] = True
        except ImportError as e:
            fail(f"{package}: NOT INSTALLED", str(e))
            results[package] = False
    
    return results

# ============================================================================
# Test Ollama Connection
# ============================================================================

def test_ollama():
    test_section("Ollama LLM Service")
    
    results = {}
    
    try:
        import httpx
        
        # Check if Ollama is running
        try:
            response = httpx.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                success("Ollama service: Running")
                results['ollama_running'] = True
                
                # List models
                data = response.json()
                models = data.get('models', [])
                if models:
                    info(f"Available models: {len(models)}")
                    for model in models[:5]:  # Show first 5
                        print(f"      - {model.get('name', 'unknown')}")
                    if len(models) > 5:
                        print(f"      ... and {len(models) - 5} more")
                else:
                    info("No models installed. Run: ollama pull llama3.2-vision")
                results['ollama_models'] = len(models) > 0
            else:
                fail(f"Ollama service returned status {response.status_code}")
                results['ollama_running'] = False
        except httpx.ConnectError:
            fail("Ollama service: NOT RUNNING")
            info("Start Ollama with: ollama serve")
            results['ollama_running'] = False
            
    except ImportError:
        fail("Cannot test Ollama (httpx not installed)")
        results['ollama_running'] = False
    
    return results

# ============================================================================
# Test Project Structure
# ============================================================================

def test_project_structure():
    test_section("Project Structure")
    
    results = {}
    project_root = Path(__file__).parent
    
    required_dirs = [
        "core",
        "perception",
        "actuators",
        "interfaces",
        "utils",
    ]
    
    required_files = [
        "main.py",
        "config.yaml",
        "requirements.txt",
        "README.md",
        ".env.example",
    ]
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.is_dir():
            success(f"Directory: {dir_name}/")
            results[f'dir_{dir_name}'] = True
        else:
            fail(f"Directory: {dir_name}/ NOT FOUND")
            results[f'dir_{dir_name}'] = False
    
    # Check files
    for file_name in required_files:
        file_path = project_root / file_name
        if file_path.is_file():
            success(f"File: {file_name}")
            results[f'file_{file_name}'] = True
        else:
            fail(f"File: {file_name} NOT FOUND")
            results[f'file_{file_name}'] = False
    
    return results

# ============================================================================
# Main
# ============================================================================

def main():
    header("The Sovereign Desktop - Installation Verification")
    print(f"\n  Testing all components...\n")
    
    all_results = {}
    
    # Run all tests
    all_results.update(test_python_environment())
    all_results.update(test_core_ai())
    all_results.update(test_web_automation())
    all_results.update(test_windows_actuators())
    all_results.update(test_voice_interface())
    all_results.update(test_supporting_libs())
    all_results.update(test_ollama())
    all_results.update(test_project_structure())
    
    # Summary
    header("Verification Summary")
    
    passed = sum(1 for v in all_results.values() if v is True)
    failed = sum(1 for v in all_results.values() if v is False)
    total = passed + failed
    
    print(f"\n  {Colors.GREEN}Passed: {passed}/{total}{Colors.RESET}")
    if failed > 0:
        print(f"  {Colors.RED}Failed: {failed}/{total}{Colors.RESET}")
        print(f"\n  {Colors.YELLOW}Some components are missing. The agent may have limited functionality.{Colors.RESET}")
    else:
        print(f"\n  {Colors.GREEN}✓ All components installed successfully!{Colors.RESET}")
    
    # Critical checks
    critical = ['langchain', 'langchain_ollama', 'playwright', 'pywin32']
    critical_passed = all(all_results.get(c, False) for c in critical)
    
    if critical_passed:
        print(f"\n  {Colors.GREEN}✓ All critical components are available{Colors.RESET}")
        print(f"\n  {Colors.BOLD}Ready to run:{Colors.RESET} python main.py")
    else:
        print(f"\n  {Colors.RED}✗ Some critical components are missing{Colors.RESET}")
        print(f"  Please install missing packages before running the agent.")
    
    print()
    return 0 if critical_passed else 1


if __name__ == "__main__":
    sys.exit(main())
