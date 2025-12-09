"""
Office Services Package

Single-responsibility tools for Microsoft Office:
- word: Word document writer (NEW - uses _run pattern)
- excel: Excel reader (NEW - uses _run pattern)

Legacy tools (backwards compatibility):
- word_writer: Legacy Word operations
- excel_reader: Legacy Excel reading
"""

# New modular architecture tools
from .word import WordWriterTool
from .excel import ExcelReaderTool

# Legacy tools for backwards compatibility
from .word_writer import WordWriterTool as LegacyWordWriterTool
from .excel_reader import ExcelReaderTool as LegacyExcelReaderTool

__all__ = [
    # New modular architecture
    "WordWriterTool",
    "ExcelReaderTool",
    # Legacy (backwards compatibility)
    "LegacyWordWriterTool",
    "LegacyExcelReaderTool",
]
