"""
Excel Reader Tool - Microsoft Excel Read Operations

Single-responsibility tool for reading Excel data.
Dependencies: pywin32 (COM automation)
"""

import os
import gc
import time
from pathlib import Path
from app.interfaces import BaseTool
from app.utils import Result

# Lazy imports for COM
_com_available = None
_excel_dispatch = None


def _init_com():
    """Initialize COM on first use."""
    global _com_available, _excel_dispatch
    if _com_available is not None:
        return _com_available
    try:
        from win32com.client import Dispatch
        _excel_dispatch = Dispatch
        _com_available = True
    except ImportError:
        _com_available = False
    return _com_available


def _cleanup(app, workbook):
    """Clean up COM objects."""
    try:
        if workbook:
            workbook.Close(SaveChanges=False)
    except Exception:
        pass
    try:
        if app:
            app.Quit()
    except Exception:
        pass
    gc.collect()
    time.sleep(0.1)


class ExcelReaderTool(BaseTool):
    """Tool for reading data from Microsoft Excel."""
    
    @property
    def name(self) -> str:
        return "excel_read"
    
    @property
    def description(self) -> str:
        return "Reads data from an Excel file cell or range"
    
    def execute(self, params: dict) -> Result:
        """
        Execute Excel read operation.
        
        Params:
            filename: Path to Excel file (.xlsx)
            range: Cell or range (e.g., 'A1', 'A1:C10')
            sheet: Sheet name or index (optional)
        """
        if not _init_com():
            return Result.fail("Excel automation not available (pywin32 missing)")
        
        filename = params.get("filename")
        cell_range = params.get("range", "A1")
        sheet = params.get("sheet")
        
        if not filename:
            return Result.fail("Filename required")
        
        abs_path = str(Path(filename).absolute())
        
        if not os.path.exists(abs_path):
            return Result.fail(f"File not found: {abs_path}")
        
        excel = None
        workbook = None
        
        try:
            excel = _excel_dispatch("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            
            workbook = excel.Workbooks.Open(abs_path, ReadOnly=True)
            
            if sheet:
                ws = workbook.Sheets(sheet)
            else:
                ws = workbook.ActiveSheet
            
            values = ws.Range(cell_range).Value
            
            # Convert to list format
            if values is None:
                data = [[None]]
            elif isinstance(values, tuple):
                data = [list(r) if isinstance(r, tuple) else [r] for r in values]
            else:
                data = [[values]]
            
            return Result.ok({
                "data": data,
                "rows": len(data),
                "cols": len(data[0]) if data else 0
            })
            
        except Exception as e:
            return Result.fail(f"Excel error: {e}")
        finally:
            _cleanup(excel, workbook)
