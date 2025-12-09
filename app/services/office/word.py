"""
Word Service - Microsoft Word Document Writer

Single-responsibility tool for creating and writing Word documents.
Uses COM interface via pywin32 for Office automation.

Dependencies:
    - pywin32: Windows COM automation library

Thread Safety:
    Uses pythoncom.CoInitialize() to ensure COM works in threaded contexts
    (e.g., inside voice loop).

Usage:
    from app.services.office.word import WordWriterTool
    
    tool = WordWriterTool()
    result = tool.execute(text="Hello World!")  # Creates new doc
    result = tool.execute(text="Content", filename="report.docx")  # Save with name
"""

import os
from pathlib import Path
from typing import Any, Optional

from app.interfaces.tool import BaseTool
from app.utils.result import CommandResult


class WordWriterTool(BaseTool):
    """
    Tool for writing text to Microsoft Word documents.
    
    This tool uses the Windows COM interface to automate Microsoft Word.
    It can create new documents, insert text, and save to file.
    
    Features:
    - Creates visible Word window so user can see the document
    - Thread-safe with COM initialization
    - Automatic file naming if not specified
    
    Example:
        tool = WordWriterTool()
        
        # Write text to a new document
        result = tool.execute(text="Hello World!")
        
        # Write to a specific file
        result = tool.execute(text="Report content", filename="report.docx")
    """
    
    @property
    def name(self) -> str:
        """Unique identifier for this tool."""
        return "write_word_doc"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Writes text to a Word document. Params: text (str), filename (optional str)"
    
    def _run(self, **kwargs: Any) -> CommandResult:
        """
        Execute Word document writing logic.
        
        Args:
            text: The text content to write to the document.
            filename: Optional filename to save as (defaults to auto-generated name).
            
        Returns:
            CommandResult with document info or error.
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
        text = kwargs.get("text", "")
        filename = kwargs.get("filename")
        
        # Validate text
        if not text:
            return CommandResult(
                success=False,
                error="No text provided. Use text='Your content here'"
            )
        
        # Lazy import win32com inside method to keep startup fast
        try:
            import win32com.client as win32
        except ImportError:
            return CommandResult(
                success=False,
                error="win32com not available. Is pywin32 installed?"
            )
        
        word = None
        doc = None
        
        try:
            # Create Word application using EnsureDispatch for better stability
            word = win32.gencache.EnsureDispatch("Word.Application")
            
            # Make Word visible so user can see the document
            word.Visible = True
            
            # Create a new document
            doc = word.Documents.Add()
            
            # Insert the text
            doc.Content.InsertAfter(text)
            
            # Save the document if filename provided
            if filename:
                # Convert to absolute path
                filepath = Path(filename)
                if not filepath.is_absolute():
                    filepath = Path.cwd() / filepath
                
                # Ensure .docx extension
                if not str(filepath).lower().endswith('.docx'):
                    filepath = filepath.with_suffix('.docx')
                
                abs_path = str(filepath.absolute())
                
                # Save as docx format (FileFormat=16 is docx)
                doc.SaveAs2(abs_path, FileFormat=16)
                
                return CommandResult(
                    success=True,
                    data={
                        "filename": abs_path,
                        "chars": len(text),
                        "saved": True
                    }
                )
            else:
                # Document created but not saved yet
                return CommandResult(
                    success=True,
                    data={
                        "chars": len(text),
                        "saved": False,
                        "message": "Document created. Use File > Save to save it."
                    }
                )
                
        except Exception as e:
            # Clean up on error
            try:
                if doc:
                    doc.Close(SaveChanges=False)
                if word:
                    word.Quit()
            except Exception:
                pass
            
            return CommandResult(
                success=False,
                error=f"Word error: {str(e)}"
            )


# =============================================================================
# VERIFICATION
# =============================================================================

if __name__ == "__main__":
    print("Testing WordWriterTool...")
    
    tool = WordWriterTool()
    print(f"Tool name: {tool.name}")
    print(f"Tool description: {tool.description}")
    
    # Test creating a document with text
    result = tool.execute(text="Hello from Sovereign Desktop!\n\nThis document was created automatically.")
    print(f"Result: {result}")
