"""
Word Writer Tool - Microsoft Word Operations

Single-responsibility tool for Word document creation and text appending.
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
_word_dispatch = None


def _init_com():
    """Initialize COM on first use."""
    global _com_available, _word_dispatch
    if _com_available is not None:
        return _com_available
    try:
        from win32com.client import Dispatch
        _word_dispatch = Dispatch
        _com_available = True
    except ImportError:
        _com_available = False
    return _com_available


def _cleanup(app, doc):
    """Clean up COM objects."""
    try:
        if doc:
            doc.Close(SaveChanges=False)
    except Exception:
        pass
    try:
        if app:
            app.Quit()
    except Exception:
        pass
    gc.collect()
    time.sleep(0.1)


class WordWriterTool(BaseTool):
    """Tool for writing to Microsoft Word documents."""
    
    @property
    def name(self) -> str:
        return "word_write"
    
    @property
    def description(self) -> str:
        return "Creates or appends text to a Word document"
    
    def execute(self, params: dict) -> Result:
        """
        Execute Word write operation.
        
        Params:
            text: Text to write/append
            filename: Path to document (.docx)
            append: If True, append to existing doc (default: True)
        """
        if not _init_com():
            return Result.fail("Word automation not available (pywin32 missing)")
        
        text = params.get("text", "")
        filename = params.get("filename")
        append = params.get("append", True)
        
        if not filename:
            return Result.fail("Filename required")
        
        abs_path = str(Path(filename).absolute())
        word = None
        doc = None
        
        try:
            word = _word_dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
            
            if append and os.path.exists(abs_path):
                doc = word.Documents.Open(abs_path)
            else:
                doc = word.Documents.Add()
            
            doc.Content.InsertAfter(text + "\n")
            doc.SaveAs2(abs_path, FileFormat=16)
            
            return Result.ok({"filename": abs_path, "chars": len(text)})
            
        except Exception as e:
            return Result.fail(f"Word error: {e}")
        finally:
            _cleanup(word, doc)
