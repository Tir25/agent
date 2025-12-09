"""
Office Operations Module

Provides COM-based automation for Microsoft Office applications:
- Word: Document creation, text appending, formatting
- Excel: Data reading/writing, cell manipulation

Uses win32com.client with EnsureDispatch for early binding and proper object access.
All operations include comprehensive error handling to prevent agent crashes.

Requirements:
    - Microsoft Office installed (Word, Excel)
    - pywin32 package

Example:
    >>> from actuators.office_ops import append_text_to_doc, read_excel_data
    >>> append_text_to_doc("Hello World!", "output.docx")
    >>> data = read_excel_data("data.xlsx", "A1:C10")
"""

import logging
import os
import gc
import time
from pathlib import Path
from typing import Optional, List, Any, Dict, Union

logger = logging.getLogger(__name__)

# Constants for Word
WD_ALIGN_PARAGRAPH_LEFT = 0
WD_ALIGN_PARAGRAPH_CENTER = 1
WD_ALIGN_PARAGRAPH_RIGHT = 2

# Try to import COM libraries
try:
    import win32com.client
    from win32com.client import gencache, Dispatch
    import pywintypes
    import pythoncom
    COM_AVAILABLE = True
except ImportError:
    COM_AVAILABLE = False
    logger.warning("win32com not installed - Office automation unavailable")


def _release_com_object(obj):
    """
    Forcefully release a COM object to prevent file locks.
    
    This ensures proper cleanup even when exceptions occur.
    """
    if obj is None:
        return
    try:
        # Try to release the COM object
        if hasattr(obj, 'Release'):
            obj.Release()
    except Exception:
        pass
    try:
        # Delete the reference
        del obj
    except Exception:
        pass
    # Force garbage collection to release COM references
    gc.collect()


def _cleanup_com(app, doc_or_workbook=None, force_quit: bool = False):
    """
    Properly clean up COM objects to prevent file locks.
    
    Args:
        app: Word.Application or Excel.Application
        doc_or_workbook: Document or Workbook to close
        force_quit: If True, always quit the application
    """
    try:
        if doc_or_workbook is not None:
            try:
                doc_or_workbook.Close(SaveChanges=False)
            except Exception:
                pass
            _release_com_object(doc_or_workbook)
            
        if app is not None:
            try:
                # Check if we should quit
                should_quit = force_quit
                if not force_quit:
                    try:
                        # For Word
                        if hasattr(app, 'Documents'):
                            should_quit = app.Documents.Count == 0
                        # For Excel
                        elif hasattr(app, 'Workbooks'):
                            should_quit = app.Workbooks.Count == 0
                    except Exception:
                        should_quit = True
                        
                if should_quit:
                    app.Quit()
            except Exception:
                pass
            _release_com_object(app)
            
    except Exception:
        pass
    finally:
        # Final garbage collection
        gc.collect()
        # Small delay to allow COM to fully release
        time.sleep(0.1)


def _ensure_absolute_path(filename: str) -> str:
    """Convert relative path to absolute path."""
    path = Path(filename)
    if not path.is_absolute():
        path = Path.cwd() / path
    return str(path)


def _get_word_app(visible: bool = True) -> Optional[Any]:
    """
    Get or create a Word application instance.
    
    Args:
        visible: Whether to make Word visible.
        
    Returns:
        Word.Application COM object, or None if unavailable.
    """
    if not COM_AVAILABLE:
        logger.error("COM libraries not available")
        return None
        
    try:
        # Try EnsureDispatch first for early binding
        try:
            word = gencache.EnsureDispatch("Word.Application")
        except Exception:
            # Fallback to late binding if gencache fails
            word = Dispatch("Word.Application")
        word.Visible = visible
        word.DisplayAlerts = False  # Suppress dialogs
        return word
    except pywintypes.com_error as e:
        logger.error(f"Failed to start Word: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error starting Word: {e}")
        return None


def _get_excel_app(visible: bool = True) -> Optional[Any]:
    """
    Get or create an Excel application instance.
    
    Args:
        visible: Whether to make Excel visible.
        
    Returns:
        Excel.Application COM object, or None if unavailable.
    """
    if not COM_AVAILABLE:
        logger.error("COM libraries not available")
        return None
        
    try:
        # Try EnsureDispatch first for early binding
        try:
            excel = gencache.EnsureDispatch("Excel.Application")
        except Exception:
            # Fallback to late binding if gencache fails
            excel = Dispatch("Excel.Application")
        excel.Visible = visible
        excel.DisplayAlerts = False  # Suppress dialogs
        return excel
    except pywintypes.com_error as e:
        logger.error(f"Failed to start Excel: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error starting Excel: {e}")
        return None


# ============================================================================
# Word Automation
# ============================================================================

def append_text_to_doc(
    text: str,
    filename: Optional[str] = None,
    visible: bool = True,
    close_after: bool = True,
    add_newline: bool = True,
) -> Dict[str, Any]:
    """
    Append text to a Word document.
    
    If the file exists, opens it and appends text to the end.
    If the file doesn't exist, creates a new document and adds the text.
    
    Args:
        text: The text to append to the document.
        filename: Path to the Word document (.docx). 
                  If None, creates a new unsaved document.
        visible: Whether to make Word visible (True recommended for debugging).
        close_after: Whether to close the document after saving.
        add_newline: Whether to add a newline after the text.
        
    Returns:
        Dictionary with result:
        - success: True if text was appended successfully
        - filename: Path to the saved file (if saved)
        - error: Error message if failed
        
    Example:
        >>> result = append_text_to_doc("Hello World!", "output.docx")
        >>> print(result)
        {'success': True, 'filename': 'C:\\...\\output.docx'}
        
        >>> append_text_to_doc("Meeting notes...", "notes.docx")
        >>> append_text_to_doc("More notes...", "notes.docx")  # Appends to existing
    """
    result = {"success": False, "filename": None, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available (pywin32 not installed)"
        return result
        
    word = None
    doc = None
    
    try:
        # Get Word application
        word = _get_word_app(visible=visible)
        if word is None:
            result["error"] = "Failed to start Microsoft Word"
            return result
            
        # Open existing file or create new document
        if filename:
            abs_path = _ensure_absolute_path(filename)
            
            if os.path.exists(abs_path):
                # Open existing document
                doc = word.Documents.Open(abs_path)
                logger.info(f"Opened existing document: {abs_path}")
            else:
                # Create new document
                doc = word.Documents.Add()
                logger.info(f"Created new document (will save to: {abs_path})")
        else:
            # Create new document without saving
            doc = word.Documents.Add()
            logger.info("Created new unsaved document")
            
        # Move to end of document
        doc.Content.InsertAfter(text)
        
        if add_newline:
            doc.Content.InsertAfter("\n")
            
        logger.info(f"Appended {len(text)} characters to document")
        
        # Save the document
        if filename:
            abs_path = _ensure_absolute_path(filename)
            
            # Determine save format
            if abs_path.lower().endswith('.docx'):
                # Word 2007+ format
                doc.SaveAs2(abs_path, FileFormat=16)  # wdFormatDocumentDefault
            elif abs_path.lower().endswith('.doc'):
                # Word 97-2003 format
                doc.SaveAs2(abs_path, FileFormat=0)  # wdFormatDocument
            elif abs_path.lower().endswith('.pdf'):
                # PDF format
                doc.SaveAs2(abs_path, FileFormat=17)  # wdFormatPDF
            else:
                # Default to .docx
                if not abs_path.lower().endswith('.docx'):
                    abs_path += '.docx'
                doc.SaveAs2(abs_path, FileFormat=16)
                
            result["filename"] = abs_path
            logger.info(f"Saved document: {abs_path}")
            
        result["success"] = True
        
    except pywintypes.com_error as e:
        error_msg = f"COM error: {e}"
        result["error"] = error_msg
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        result["error"] = error_msg
        logger.error(error_msg)
    finally:
        # Clean up with proper COM release
        if close_after:
            _cleanup_com(word, doc, force_quit=True)
        else:
            _cleanup_com(None, None)  # Just gc.collect()
            
    return result


def create_word_document(
    content: str,
    filename: str,
    title: Optional[str] = None,
    visible: bool = True,
) -> Dict[str, Any]:
    """
    Create a new Word document with the given content.
    
    Args:
        content: The main text content of the document.
        filename: Path to save the document (.docx).
        title: Optional title (will be formatted as heading).
        visible: Whether to make Word visible.
        
    Returns:
        Dictionary with result (success, filename, error).
        
    Example:
        >>> create_word_document(
        ...     content="This is my document content.",
        ...     filename="report.docx",
        ...     title="My Report"
        ... )
    """
    result = {"success": False, "filename": None, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    word = None
    doc = None
    
    try:
        word = _get_word_app(visible=visible)
        if word is None:
            result["error"] = "Failed to start Microsoft Word"
            return result
            
        # Create new document
        doc = word.Documents.Add()
        
        # Add title if provided
        if title:
            title_para = doc.Paragraphs.Add()
            title_para.Range.Text = title
            title_para.Range.Style = "Heading 1"
            title_para.Range.InsertParagraphAfter()
            
        # Add content
        doc.Content.InsertAfter(content)
        
        # Save
        abs_path = _ensure_absolute_path(filename)
        if not abs_path.lower().endswith('.docx'):
            abs_path += '.docx'
        doc.SaveAs2(abs_path, FileFormat=16)
        
        result["success"] = True
        result["filename"] = abs_path
        logger.info(f"Created document: {abs_path}")
        
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(word, doc, force_quit=True)
            
    return result


def read_word_document(filename: str) -> Dict[str, Any]:
    """
    Read the full text content of a Word document.
    
    Args:
        filename: Path to the Word document.
        
    Returns:
        Dictionary with:
        - success: True if read successfully
        - content: Full text content of the document
        - paragraphs: Number of paragraphs
        - error: Error message if failed
    """
    result = {"success": False, "content": None, "paragraphs": 0, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    word = None
    doc = None
    
    try:
        word = _get_word_app(visible=False)
        if word is None:
            result["error"] = "Failed to start Microsoft Word"
            return result
            
        abs_path = _ensure_absolute_path(filename)
        
        if not os.path.exists(abs_path):
            result["error"] = f"File not found: {abs_path}"
            return result
            
        doc = word.Documents.Open(abs_path, ReadOnly=True)
        
        result["content"] = doc.Content.Text
        result["paragraphs"] = doc.Paragraphs.Count
        result["success"] = True
        
        logger.info(f"Read document: {abs_path} ({result['paragraphs']} paragraphs)")
        
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(word, doc, force_quit=True)
            
    return result


# ============================================================================
# Excel Automation
# ============================================================================

def read_excel_data(
    filename: str,
    cell_range: str,
    sheet: Optional[Union[str, int]] = None,
    as_dataframe: bool = False,
) -> Dict[str, Any]:
    """
    Read data from an Excel file.
    
    Args:
        filename: Path to the Excel file (.xlsx, .xls).
        cell_range: Range of cells to read (e.g., "A1:C10", "A1", "A:C").
        sheet: Sheet name or index (1-based). Defaults to active sheet.
        as_dataframe: If True and pandas is available, return as DataFrame.
        
    Returns:
        Dictionary with:
        - success: True if read successfully
        - data: 2D list of cell values, or DataFrame if as_dataframe=True
        - rows: Number of rows read
        - cols: Number of columns read
        - error: Error message if failed
        
    Example:
        >>> result = read_excel_data("data.xlsx", "A1:C10")
        >>> print(result["data"])
        [['Name', 'Age', 'City'], ['Alice', 30, 'NYC'], ...]
        
        >>> result = read_excel_data("data.xlsx", "A1:D100", as_dataframe=True)
        >>> df = result["data"]  # pandas DataFrame
    """
    result = {"success": False, "data": None, "rows": 0, "cols": 0, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    excel = None
    workbook = None
    
    try:
        excel = _get_excel_app(visible=False)
        if excel is None:
            result["error"] = "Failed to start Microsoft Excel"
            return result
            
        abs_path = _ensure_absolute_path(filename)
        
        if not os.path.exists(abs_path):
            result["error"] = f"File not found: {abs_path}"
            return result
            
        # Open workbook
        workbook = excel.Workbooks.Open(abs_path, ReadOnly=True)
        
        # Select sheet
        if sheet is None:
            ws = workbook.ActiveSheet
        elif isinstance(sheet, int):
            ws = workbook.Sheets(sheet)
        else:
            ws = workbook.Sheets(sheet)
            
        # Get range
        data_range = ws.Range(cell_range)
        
        # Read values
        values = data_range.Value
        
        # Handle single cell vs range
        if values is None:
            data = [[None]]
        elif isinstance(values, tuple):
            # Multiple rows
            data = [list(row) if isinstance(row, tuple) else [row] for row in values]
        else:
            # Single value
            data = [[values]]
            
        result["data"] = data
        result["rows"] = len(data)
        result["cols"] = len(data[0]) if data else 0
        result["success"] = True
        
        logger.info(f"Read {result['rows']}x{result['cols']} from {abs_path}")
        
        # Convert to DataFrame if requested
        if as_dataframe and result["success"]:
            try:
                import pandas as pd
                result["data"] = pd.DataFrame(data[1:], columns=data[0])
            except ImportError:
                logger.warning("pandas not installed, returning as list")
                
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(excel, workbook, force_quit=True)
            
    return result


def write_excel_cell(
    filename: str,
    cell: str,
    value: Any,
    sheet: Optional[Union[str, int]] = None,
    create_if_missing: bool = True,
    visible: bool = True,
) -> Dict[str, Any]:
    """
    Write a value to a specific cell in an Excel file.
    
    Args:
        filename: Path to the Excel file (.xlsx).
        cell: Cell address (e.g., "A1", "B5", "AA100").
        value: Value to write (string, number, date, etc.).
        sheet: Sheet name or index (1-based). Defaults to active sheet.
        create_if_missing: If True, create file if it doesn't exist.
        visible: Whether to make Excel visible.
        
    Returns:
        Dictionary with:
        - success: True if written successfully
        - filename: Path to the file
        - cell: Cell that was written to
        - error: Error message if failed
        
    Example:
        >>> write_excel_cell("report.xlsx", "A1", "Sales Report")
        >>> write_excel_cell("report.xlsx", "B2", 12345.67)
        >>> write_excel_cell("report.xlsx", "C3", "=SUM(B1:B10)")  # Formula
    """
    result = {"success": False, "filename": None, "cell": cell, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    excel = None
    workbook = None
    
    try:
        excel = _get_excel_app(visible=visible)
        if excel is None:
            result["error"] = "Failed to start Microsoft Excel"
            return result
            
        abs_path = _ensure_absolute_path(filename)
        
        if os.path.exists(abs_path):
            # Open existing workbook
            workbook = excel.Workbooks.Open(abs_path)
        elif create_if_missing:
            # Create new workbook
            workbook = excel.Workbooks.Add()
            logger.info(f"Creating new workbook: {abs_path}")
        else:
            result["error"] = f"File not found: {abs_path}"
            return result
            
        # Select sheet
        if sheet is None:
            ws = workbook.ActiveSheet
        elif isinstance(sheet, int):
            ws = workbook.Sheets(sheet)
        else:
            ws = workbook.Sheets(sheet)
            
        # Write value
        ws.Range(cell).Value = value
        
        # Save
        if not abs_path.lower().endswith(('.xlsx', '.xls')):
            abs_path += '.xlsx'
            
        workbook.SaveAs(abs_path, FileFormat=51)  # xlOpenXMLWorkbook
        
        result["success"] = True
        result["filename"] = abs_path
        
        logger.info(f"Wrote '{value}' to {cell} in {abs_path}")
        
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(excel, workbook, force_quit=True)
            
    return result


def write_excel_range(
    filename: str,
    start_cell: str,
    data: List[List[Any]],
    sheet: Optional[Union[str, int]] = None,
    create_if_missing: bool = True,
    visible: bool = True,
) -> Dict[str, Any]:
    """
    Write a 2D array of data to Excel starting at a specific cell.
    
    Args:
        filename: Path to the Excel file.
        start_cell: Top-left cell of the range (e.g., "A1").
        data: 2D list of values to write.
        sheet: Sheet name or index.
        create_if_missing: If True, create file if it doesn't exist.
        visible: Whether to make Excel visible.
        
    Returns:
        Dictionary with result (success, filename, error).
        
    Example:
        >>> data = [
        ...     ["Name", "Age", "City"],
        ...     ["Alice", 30, "NYC"],
        ...     ["Bob", 25, "LA"],
        ... ]
        >>> write_excel_range("output.xlsx", "A1", data)
    """
    result = {"success": False, "filename": None, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    if not data or not data[0]:
        result["error"] = "Data cannot be empty"
        return result
        
    excel = None
    workbook = None
    
    try:
        excel = _get_excel_app(visible=visible)
        if excel is None:
            result["error"] = "Failed to start Microsoft Excel"
            return result
            
        abs_path = _ensure_absolute_path(filename)
        
        if os.path.exists(abs_path):
            workbook = excel.Workbooks.Open(abs_path)
        elif create_if_missing:
            workbook = excel.Workbooks.Add()
        else:
            result["error"] = f"File not found: {abs_path}"
            return result
            
        # Select sheet
        if sheet is None:
            ws = workbook.ActiveSheet
        elif isinstance(sheet, int):
            ws = workbook.Sheets(sheet)
        else:
            ws = workbook.Sheets(sheet)
            
        # Calculate end cell
        rows = len(data)
        cols = len(data[0])
        
        # Get start cell reference
        start = ws.Range(start_cell)
        end = ws.Cells(start.Row + rows - 1, start.Column + cols - 1)
        target_range = ws.Range(start, end)
        
        # Write data
        target_range.Value = data
        
        # Save
        if not abs_path.lower().endswith(('.xlsx', '.xls')):
            abs_path += '.xlsx'
            
        workbook.SaveAs(abs_path, FileFormat=51)
        
        result["success"] = True
        result["filename"] = abs_path
        
        logger.info(f"Wrote {rows}x{cols} data to {abs_path}")
        
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(excel, workbook, force_quit=True)
            
    return result


def get_excel_info(filename: str) -> Dict[str, Any]:
    """
    Get information about an Excel workbook.
    
    Args:
        filename: Path to the Excel file.
        
    Returns:
        Dictionary with:
        - success: True if info retrieved
        - sheets: List of sheet names
        - active_sheet: Name of active sheet
        - error: Error message if failed
    """
    result = {"success": False, "sheets": [], "active_sheet": None, "error": None}
    
    if not COM_AVAILABLE:
        result["error"] = "COM libraries not available"
        return result
        
    excel = None
    workbook = None
    
    try:
        excel = _get_excel_app(visible=False)
        if excel is None:
            result["error"] = "Failed to start Microsoft Excel"
            return result
            
        abs_path = _ensure_absolute_path(filename)
        
        if not os.path.exists(abs_path):
            result["error"] = f"File not found: {abs_path}"
            return result
            
        workbook = excel.Workbooks.Open(abs_path, ReadOnly=True)
        
        result["sheets"] = [workbook.Sheets(i).Name for i in range(1, workbook.Sheets.Count + 1)]
        result["active_sheet"] = workbook.ActiveSheet.Name
        result["success"] = True
        
        logger.info(f"Excel info: {len(result['sheets'])} sheets")
        
    except pywintypes.com_error as e:
        result["error"] = f"COM error: {e}"
        logger.error(result["error"])
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.error(result["error"])
    finally:
        _cleanup_com(excel, workbook, force_quit=True)
            
    return result
