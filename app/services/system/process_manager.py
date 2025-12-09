"""
Process Manager Tool - Application Launch/Close

Single-responsibility tool for managing applications.
Dependencies: psutil, subprocess (stdlib)
"""

import subprocess
import shutil
from app.interfaces import BaseTool
from app.utils import Result

# Lazy import psutil
_psutil = None


def _init_psutil():
    """Initialize psutil on first use."""
    global _psutil
    if _psutil is not None:
        return True
    try:
        import psutil
        _psutil = psutil
        return True
    except ImportError:
        return False


class ProcessManagerTool(BaseTool):
    """Tool for launching and closing applications."""
    
    @property
    def name(self) -> str:
        return "manage_app"
    
    @property
    def description(self) -> str:
        return "Launches or closes applications by name"
    
    def execute(self, params: dict) -> Result:
        """
        Execute app management.
        
        Params:
            action: 'open' or 'close'
            app: Application name or path
            force: Force kill when closing (default: False)
        """
        action = params.get("action", "open")
        app_name = params.get("app")
        
        if not app_name:
            return Result.fail("App name required")
        
        if action == "open":
            return self._open_app(app_name, params.get("args"))
        elif action == "close":
            return self._close_app(app_name, params.get("force", False))
        else:
            return Result.fail(f"Unknown action: {action}")
    
    def _open_app(self, app_name: str, args: list = None) -> Result:
        """Launch an application."""
        try:
            # Try to find executable
            exe = shutil.which(app_name)
            if exe:
                cmd = [exe] + (args or [])
            else:
                # Use shell start
                cmd = ["cmd", "/c", "start", "", app_name]
            
            proc = subprocess.Popen(cmd, shell=False)
            return Result.ok({"pid": proc.pid, "app": app_name})
        except Exception as e:
            return Result.fail(f"Failed to open {app_name}: {e}")
    
    def _close_app(self, app_name: str, force: bool) -> Result:
        """Close an application."""
        if not _init_psutil():
            return Result.fail("psutil not available")
        
        app_lower = app_name.lower()
        closed = 0
        
        for proc in _psutil.process_iter(['name', 'pid']):
            try:
                if app_lower in proc.info['name'].lower():
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    closed += 1
            except Exception:
                continue
        
        if closed > 0:
            return Result.ok({"closed": closed, "app": app_name})
        return Result.fail(f"No process found matching: {app_name}")
