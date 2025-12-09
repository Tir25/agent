#!/usr/bin/env python3
"""
The Sovereign Desktop - Dependency Installer

This script handles the complete installation of all dependencies including:
- Upgrading pip to the latest version
- Installing all requirements from requirements.txt
- Running Playwright browser installation
- Handling PyAudio installation with fallback for Windows

Usage:
    python install_dependencies.py [--skip-playwright] [--verbose]

Options:
    --skip-playwright    Skip Playwright browser installation
    --verbose, -v        Show detailed installation output
    --help, -h           Show this help message
"""

import subprocess
import sys
import os
import platform
import argparse
from pathlib import Path
from typing import Tuple, Optional


# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.absolute()
REQUIREMENTS_FILE = SCRIPT_DIR / "requirements.txt"

# Packages that need special handling
SPECIAL_PACKAGES = {
    "pyaudio": {
        "description": "Audio I/O for voice capture",
        "windows_note": "May require Visual C++ Build Tools or pipwin",
    },
    "playwright": {
        "description": "Browser automation",
        "post_install": ["playwright", "install"],
    },
}


# ============================================================================
# Console Output Helpers
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"


def supports_color() -> bool:
    """Check if the terminal supports color output."""
    if os.environ.get("NO_COLOR"):
        return False
    if platform.system() == "Windows":
        return os.environ.get("TERM") or os.environ.get("WT_SESSION")
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = supports_color()


def colorize(text: str, color: str) -> str:
    """Apply color to text if supported."""
    if USE_COLOR:
        return f"{color}{text}{Colors.RESET}"
    return text


def print_banner():
    """Print the application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              🏛️  THE SOVEREIGN DESKTOP                        ║
    ║              Dependency Installation Script                   ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(colorize(banner, Colors.CYAN))


def print_step(message: str, icon: str = "→"):
    """Print a step message."""
    print(f"\n{colorize(icon, Colors.YELLOW)} {message}")


def print_success(message: str):
    """Print a success message."""
    print(f"  {colorize('✓', Colors.GREEN)} {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"  {colorize('⚠', Colors.YELLOW)} {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"  {colorize('✗', Colors.RED)} {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"  {colorize('ℹ', Colors.CYAN)} {message}")


# ============================================================================
# System Detection
# ============================================================================

def get_python_info() -> dict:
    """Get Python environment information."""
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "in_venv": sys.prefix != sys.base_prefix,
    }


def check_virtual_environment():
    """Check if running in a virtual environment."""
    in_venv = sys.prefix != sys.base_prefix
    
    if not in_venv:
        print_warning("Not running in a virtual environment!")
        print_info("It's recommended to use a virtual environment.")
        print_info("Create one with: python -m venv sovereign_agent")
        print()
        
        response = input("  Continue anyway? (y/n): ").strip().lower()
        if response != "y":
            print("\nAborting. Please create and activate a virtual environment first.")
            sys.exit(1)
    else:
        print_success(f"Virtual environment detected: {sys.prefix}")


# ============================================================================
# Command Execution
# ============================================================================

def run_command(
    cmd: list,
    description: str = "",
    capture_output: bool = False,
    verbose: bool = False,
) -> Tuple[bool, str]:
    """
    Run a command and return success status and output.
    
    Args:
        cmd: Command and arguments as a list
        description: Description for logging
        capture_output: Whether to capture output
        verbose: Whether to show detailed output
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    if description:
        print_info(f"{description}...")
    
    try:
        if verbose:
            # Show output in real-time
            result = subprocess.run(
                cmd,
                check=True,
                text=True,
            )
            return True, ""
        else:
            # Capture output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return True, result.stdout
            
    except subprocess.CalledProcessError as e:
        error_output = e.stderr if e.stderr else str(e)
        return False, error_output
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"


def get_pip_command() -> list:
    """Get the pip command for the current environment."""
    return [sys.executable, "-m", "pip"]


# ============================================================================
# Installation Steps
# ============================================================================

def upgrade_pip(verbose: bool = False) -> bool:
    """Upgrade pip to the latest version."""
    print_step("Upgrading pip to latest version...")
    
    cmd = get_pip_command() + ["install", "--upgrade", "pip"]
    success, output = run_command(cmd, "Upgrading pip", verbose=verbose)
    
    if success:
        # Get new pip version
        version_cmd = get_pip_command() + ["--version"]
        _, version_output = run_command(version_cmd, capture_output=True)
        print_success(f"pip upgraded successfully")
        if version_output:
            print_info(version_output.strip())
        return True
    else:
        print_error(f"Failed to upgrade pip: {output}")
        return False


def install_requirements(verbose: bool = False) -> Tuple[bool, list]:
    """
    Install requirements from requirements.txt.
    
    Returns:
        Tuple of (success: bool, failed_packages: list)
    """
    print_step("Installing requirements from requirements.txt...")
    
    if not REQUIREMENTS_FILE.exists():
        print_error(f"Requirements file not found: {REQUIREMENTS_FILE}")
        return False, []
    
    # First, try installing everything at once
    cmd = get_pip_command() + [
        "install",
        "-r", str(REQUIREMENTS_FILE),
        "--no-warn-script-location",
    ]
    
    if not verbose:
        cmd.append("--quiet")
    
    success, output = run_command(
        cmd,
        "Installing all packages",
        verbose=verbose,
    )
    
    if success:
        print_success("All requirements installed successfully")
        return True, []
    else:
        print_warning("Some packages failed to install, trying individually...")
        return install_requirements_individually(verbose)


def install_requirements_individually(verbose: bool = False) -> Tuple[bool, list]:
    """Install requirements one by one to identify failures."""
    failed_packages = []
    
    with open(REQUIREMENTS_FILE, "r") as f:
        lines = f.readlines()
    
    packages = []
    for line in lines:
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        packages.append(line)
    
    for package in packages:
        # Extract package name (without version specifier)
        package_name = package.split(">=")[0].split("==")[0].split("<")[0].strip()
        
        cmd = get_pip_command() + ["install", package]
        if not verbose:
            cmd.append("--quiet")
        
        success, output = run_command(cmd, verbose=verbose)
        
        if success:
            print_success(f"Installed: {package_name}")
        else:
            print_error(f"Failed: {package_name}")
            failed_packages.append(package_name)
    
    return len(failed_packages) == 0, failed_packages


def install_pyaudio_with_fallback(verbose: bool = False) -> bool:
    """
    Install PyAudio with fallback methods for Windows.
    
    PyAudio often fails to install on Windows due to missing PortAudio.
    This function tries multiple approaches.
    """
    print_step("Handling PyAudio installation...")
    
    # Check if already installed
    try:
        import pyaudio
        print_success("PyAudio is already installed")
        return True
    except ImportError:
        pass
    
    # Method 1: Standard pip install
    print_info("Attempting standard pip install...")
    cmd = get_pip_command() + ["install", "pyaudio"]
    success, output = run_command(cmd, verbose=verbose)
    
    if success:
        print_success("PyAudio installed via pip")
        return True
    
    # Method 2: Try pipwin (Windows only)
    if platform.system() == "Windows":
        print_warning("Standard install failed, trying pipwin...")
        
        # Install pipwin
        pipwin_cmd = get_pip_command() + ["install", "pipwin", "--quiet"]
        pipwin_success, _ = run_command(pipwin_cmd)
        
        if pipwin_success:
            # Use pipwin to install pyaudio
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pipwin", "install", "pyaudio"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    print_success("PyAudio installed via pipwin")
                    return True
            except Exception as e:
                print_warning(f"pipwin attempt failed: {e}")
    
    # Method 3: Suggest manual installation
    print_error("PyAudio automatic installation failed")
    print()
    print("  " + colorize("Manual Installation Options:", Colors.BOLD))
    print()
    
    if platform.system() == "Windows":
        print("  Option 1: Install Visual C++ Build Tools")
        print("    - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
        print("    - Select 'Desktop development with C++' workload")
        print("    - Then run: pip install pyaudio")
        print()
        print("  Option 2: Install pre-built wheel")
        print("    - Download from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio")
        print("    - Choose the wheel matching your Python version")
        print("    - Run: pip install <downloaded_wheel_file>.whl")
        print()
        print("  Option 3: Use pipwin")
        print("    - pip install pipwin")
        print("    - pipwin install pyaudio")
    else:
        print("  Install PortAudio development libraries:")
        print("    - Ubuntu/Debian: sudo apt-get install portaudio19-dev")
        print("    - macOS: brew install portaudio")
        print("    - Then run: pip install pyaudio")
    
    print()
    return False


def install_playwright_browsers(verbose: bool = False) -> bool:
    """Run Playwright browser installation."""
    print_step("Installing Playwright browsers...")
    
    # Check if playwright is installed
    try:
        import playwright
    except ImportError:
        print_warning("Playwright not installed, skipping browser installation")
        return False
    
    print_info("This will download Chromium, Firefox, and WebKit browsers")
    print_info("This may take several minutes...")
    
    cmd = [sys.executable, "-m", "playwright", "install"]
    
    success, output = run_command(
        cmd,
        "Installing browsers",
        verbose=True,  # Always show progress for browsers
    )
    
    if success:
        print_success("Playwright browsers installed successfully")
        return True
    else:
        print_error(f"Failed to install Playwright browsers")
        print_info("You can manually run: playwright install")
        return False


def verify_installations() -> dict:
    """Verify that key packages are installed correctly."""
    print_step("Verifying installations...")
    
    packages_to_verify = [
        ("langchain", "Core AI"),
        ("langchain_ollama", "Ollama Integration"),
        ("numpy", "Numerical Computing"),
        ("playwright", "Web Automation"),
        ("pywinauto", "Windows Automation"),
        ("pycaw", "Audio Control"),
        ("vosk", "Speech Recognition"),
        ("pyttsx3", "Text-to-Speech"),
    ]
    
    results = {}
    
    for package, description in packages_to_verify:
        try:
            __import__(package)
            print_success(f"{description}: {package}")
            results[package] = True
        except ImportError:
            print_error(f"{description}: {package} - NOT INSTALLED")
            results[package] = False
    
    # Special check for pyaudio
    try:
        import pyaudio
        print_success(f"Audio I/O: pyaudio")
        results["pyaudio"] = True
    except ImportError:
        print_warning(f"Audio I/O: pyaudio - NOT INSTALLED (voice features limited)")
        results["pyaudio"] = False
    
    return results


# ============================================================================
# Main
# ============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Install dependencies for The Sovereign Desktop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--skip-playwright",
        action="store_true",
        help="Skip Playwright browser installation",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed installation output",
    )
    
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify installations, don't install anything",
    )
    
    return parser.parse_args()


def main():
    """Main installation routine."""
    args = parse_args()
    
    print_banner()
    
    # Show Python info
    py_info = get_python_info()
    print_step("Python Environment")
    print_info(f"Python: {sys.version.split()[0]}")
    print_info(f"Executable: {sys.executable}")
    print_info(f"Platform: {py_info['platform']} ({py_info['architecture']})")
    
    # Check virtual environment
    check_virtual_environment()
    
    if args.verify_only:
        results = verify_installations()
        success_count = sum(results.values())
        total_count = len(results)
        print()
        print(f"  Verified: {success_count}/{total_count} packages installed")
        return 0 if success_count == total_count else 1
    
    # Upgrade pip
    if not upgrade_pip(verbose=args.verbose):
        print_warning("Continuing despite pip upgrade failure...")
    
    # Install requirements
    success, failed = install_requirements(verbose=args.verbose)
    
    # Handle PyAudio specially if it failed
    if "pyaudio" in failed:
        install_pyaudio_with_fallback(verbose=args.verbose)
        failed.remove("pyaudio")
    
    # Install Playwright browsers
    if not args.skip_playwright:
        install_playwright_browsers(verbose=args.verbose)
    else:
        print_info("Skipping Playwright browser installation (--skip-playwright)")
    
    # Verify installations
    results = verify_installations()
    
    # Summary
    print()
    print(colorize("  ══════════════════════════════════════════════════════════", Colors.GREEN))
    
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        print(colorize("  ✓ All dependencies installed successfully!", Colors.GREEN))
    else:
        print(colorize(f"  ⚠ {success_count}/{total_count} packages installed", Colors.YELLOW))
        if failed:
            print(colorize(f"    Failed packages: {', '.join(failed)}", Colors.RED))
    
    print(colorize("  ══════════════════════════════════════════════════════════", Colors.GREEN))
    print()
    
    print("  Next steps:")
    print(f"    1. Activate the environment: {colorize('.\\sovereign_agent\\Scripts\\Activate.ps1', Colors.CYAN)}")
    print(f"    2. Start the agent: {colorize('python main.py', Colors.CYAN)}")
    print()
    
    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
