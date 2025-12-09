"""
Excel Service - Microsoft Excel Reader

Single-responsibility tool for reading data from Excel spreadsheets.
Uses COM interface via pywin32 for Office automation.

Dependencies:
    - pywin32: Windows COM automation library

Thread Safety:
    Uses pythoncom.CoInitialize() to ensure COM works in threaded contexts
    (e.g., inside voice loop).

Usage:
    from app.services.office.excel import ExcelReaderTool
    
    tool = ExcelReaderTool()
    result = tool.execute(filename="data.xlsx", range="A1:B10")
"""

from pathlib import Path
from typing import Any, List, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


class ExcelReaderTool(BaseTool):
    """
    Tool for reading data from Microsoft Excel spreadsheets.
    
    This tool uses the Windows COM interface to automate Microsoft Excel.
    It opens workbooks read-only to avoid file locks and extracts data
    from specified ranges.
    
    Features:
    - Read-only mode to avoid file locks
    - Thread-safe with COM initialization
    - Returns data as list of lists for easy processing
    
    Example:
        tool = ExcelReaderTool()
        
        # Read a specific range
        result = tool.execute(filename="report.xlsx", range="A1:D10")
        
        # Access the data
        if result.success:
            for row in result.data["values"]:
                print(row)
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        return "read_excel"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Reads data from a specific range. Params: filename (str), range (e.g., 'A1:B10')"
    
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute Excel reading logic.
        
        Args:
            filename: Path to the Excel file (.xlsx or .xls).
            range: Cell range to read (e.g., 'A1:B10', 'Sheet1!A1:C5').
            sheet: Optional sheet name (defaults to active sheet).
            
        Returns:
            CommandResult with data values or error.
        """
        # Initialize COM for thread safety (required for voice loop)
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            return CommandResult(
                success=False,
                error="pythoncom not available. Is pywin32 installed?"
            )
        except Exception:
            pass  # Already initialized
        
        # Get parameters
        filename = kwargs.get("filename")
        cell_range = kwargs.get("range")
        sheet_name = kwargs.get("sheet")
        
        # Validate filename
        if not filename:
            return CommandResult(
                success=False,
                error="No filename provided. Use filename='path/to/file.xlsx'"
            )
        
        # Validate range
        if not cell_range:
            return CommandResult(
                success=False,
                error="No range provided. Use range='A1:B10'"
            )
        
        # Convert to absolute path
        filepath = Path(filename)
        if not filepath.is_absolute():
            filepath = Path.cwd() / filepath
        
        abs_path = str(filepath.absolute())
        
        # Check file exists
        if not filepath.exists():
            return CommandResult(
                success=False,
                error=f"File not found: {abs_path}"
            )
        
        # Lazy import win32com inside method to keep startup fast
        try:
            import win32com.client as win32
        except ImportError:
            return CommandResult(
                success=False,
                error="win32com not available. Is pywin32 installed?"
            )
        
        excel = None
        workbook = None
        
        try:
            # Create Excel application using EnsureDispatch for better stability
            excel = win32.gencache.EnsureDispatch("Excel.Application")
            
            # Keep Excel invisible for reading operations
            excel.Visible = False
            excel.DisplayAlerts = False
            
            # Open workbook read-only to avoid file locks
            workbook = excel.Workbooks.Open(
                abs_path,
                ReadOnly=True,
                UpdateLinks=False
            )
            
            # Get the sheet
            if sheet_name:
                try:
                    sheet = workbook.Sheets(sheet_name)
                except Exception:
                    return CommandResult(
                        success=False,
                        error=f"Sheet not found: {sheet_name}"
                    )
            else:
                sheet = workbook.ActiveSheet
            
            # Get the range
            try:
                data_range = sheet.Range(cell_range)
            except Exception as e:
                return CommandResult(
                    success=False,
                    error=f"Invalid range '{cell_range}': {str(e)}"
                )
            
            # Extract values
            values = data_range.Value
            
            # Convert to list of lists
            if values is None:
                result_data: List[List[Any]] = [[]]
            elif isinstance(values, tuple):
                # Multiple rows/columns
                result_data = [list(row) if isinstance(row, tuple) else [row] for row in values]
            else:
                # Single cell
                result_data = [[values]]
            
            # Get range info
            rows = len(result_data)
            cols = len(result_data[0]) if result_data and result_data[0] else 0
            
            return CommandResult(
                success=True,
                data={
                    "values": result_data,
                    "rows": rows,
                    "cols": cols,
                    "range": cell_range,
                    "filename": abs_path
                }
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Excel error: {str(e)}"
            )
            
        finally:
            # Clean up COM objects
            try:
                if workbook:
                    workbook.Close(SaveChanges=False)
            except Exception:
                pass
            try:
                if excel:
                    excel.Quit()
            except Exception:
                pass


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing ExcelReaderTool...")
    
    tool = ExcelReaderTool()
    print(f"Tool name: {tool.name}")
    print(f"Tool description: {tool.description}")
    
    # Test with a non-existent file (should handle gracefully)
    result = tool.execute(filename="nonexistent.xlsx", range="A1:B10")
    print(f"Result (no file): {result}")
