"""
App Launcher Service - Application Launching

Single-responsibility tool for launching applications by name.
This service is fully isolated and uses multiple fallback strategies.

Strategies (in order):
    1. AppOpener library (if available)
    2. Windows Start Menu search via subprocess
    3. Direct executable path

Usage:
    from app.services.system.launcher import AppLauncherTool
    
    tool = AppLauncherTool()
    result = tool.execute(app_name="notepad")  # Launch Notepad
    result = tool.execute(app_name="chrome")   # Launch Chrome
    result = tool.execute(path="C:/Program Files/App/app.exe")  # Launch by path
"""

import subprocess
import shutil
from pathlib import Path
from typing import Any, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


def _get_appopener() -> Any:
    """
    Get the AppOpener module.
    
    Returns fresh import each time to avoid caching issues.
    
    Returns:
        AppOpener module if available, None otherwise.
    """
    try:
        import AppOpener
        return AppOpener
    except ImportError:
        return None


# Common application name mappings for Windows
_APP_ALIASES: dict[str, list[str]] = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "explorer": ["explorer.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "chrome": ["chrome.exe", "google chrome"],
    "firefox": ["firefox.exe"],
    "edge": ["msedge.exe", "microsoft edge"],
    "word": ["winword.exe", "microsoft word"],
    "excel": ["excel.exe", "microsoft excel"],
    "powerpoint": ["powerpnt.exe", "microsoft powerpoint"],
    "outlook": ["outlook.exe", "microsoft outlook"],
    "vscode": ["code.exe", "visual studio code"],
    "spotify": ["spotify.exe"],
    "discord": ["discord.exe"],
    "slack": ["slack.exe"],
    "teams": ["teams.exe", "microsoft teams"],
}


def _launch_with_appopener(app_name: str) -> Optional[CommandResult]:
    """
    Attempt to launch app using AppOpener.
    
    Args:
        app_name: Name of the application to launch.
        
    Returns:
        CommandResult if successful, None if AppOpener not available.
    """
    appopener = _get_appopener()
    
    if appopener is None:
        return None
    
    try:
        appopener.open(app_name, throw_error=True)
        return CommandResult(
            success=True,
            data={"app": app_name, "method": "appopener"}
        )
    except Exception as e:
        return CommandResult(
            success=False,
            error=f"AppOpener failed to launch '{app_name}': {str(e)}"
        )


def _launch_with_subprocess(app_name: str) -> CommandResult:
    """
    Attempt to launch app using subprocess.
    
    Args:
        app_name: Name of the application or executable.
        
    Returns:
        CommandResult indicating success or failure.
    """
    # Check aliases first
    executables = _APP_ALIASES.get(app_name.lower(), [app_name])
    
    for exe in executables:
        # Check if it's in PATH
        exe_path = shutil.which(exe)
        if exe_path:
            try:
                subprocess.Popen(
                    [exe_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return CommandResult(
                    success=True,
                    data={"app": app_name, "path": exe_path, "method": "subprocess"}
                )
            except Exception:
                continue
    
    # Try Windows 'start' command
    try:
        subprocess.Popen(
            f'start "" "{app_name}"',
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return CommandResult(
            success=True,
            data={"app": app_name, "method": "start_command"}
        )
    except Exception as e:
        return CommandResult(
            success=False,
            error=f"Failed to launch '{app_name}': {str(e)}"
        )


def _launch_by_path(path: str) -> CommandResult:
    """
    Launch an application by its file path.
    
    Args:
        path: Full path to the executable.
        
    Returns:
        CommandResult indicating success or failure.
    """
    exe_path = Path(path)
    
    if not exe_path.exists():
        return CommandResult(
            success=False,
            error=f"Executable not found: {path}"
        )
    
    if not exe_path.is_file():
        return CommandResult(
            success=False,
            error=f"Path is not a file: {path}"
        )
    
    try:
        subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return CommandResult(
            success=True,
            data={"app": exe_path.name, "path": str(exe_path), "method": "direct_path"}
        )
    except Exception as e:
        return CommandResult(
            success=False,
            error=f"Failed to launch '{path}': {str(e)}"
        )


class AppLauncherTool(BaseTool):
    """
    Tool for launching applications by name or path.
    
    This tool uses multiple strategies to launch applications:
    1. AppOpener library (if installed)
    2. Subprocess with Windows executable search
    3. Direct file path execution
    
    Example:
        tool = AppLauncherTool()
        
        # Launch by name
        result = tool.execute(app_name="notepad")
        result = tool.execute(app_name="chrome")
        
        # Launch by path
        result = tool.execute(path="C:/Program Files/MyApp/app.exe")
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        return "launch_app"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Launches an application by name (e.g., 'chrome', 'notepad') or by file path"
    
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute application launch logic.
        
        Args:
            app_name: Name of the application to launch (optional)
            path: Full path to the executable (optional)
            
        Returns:
            CommandResult with launch status or error.
        """
        app_name = kwargs.get("app_name")
        path = kwargs.get("path")
        
        # Validate input
        if not app_name and not path:
            return CommandResult(
                success=False,
                error="No application specified. Use app_name='<name>' or path='<path>'"
            )
        
        # Launch by path if provided
        if path:
            return _launch_by_path(path)
        
        # Try AppOpener first (best for name-based launching)
        result = _launch_with_appopener(app_name)
        if result is not None:
            return result
        
        # Fallback to subprocess
        return _launch_with_subprocess(app_name)
