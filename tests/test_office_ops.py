#!/usr/bin/env python3
"""
Office Operations - Isolated Test

Tests Word and Excel COM operations with unique filenames.
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Unique filenames to avoid conflicts
unique_id = str(uuid.uuid4())[:8]
doc_path = os.path.join(tempfile.gettempdir(), f"sovereign_doc_{unique_id}.docx")
xlsx_path = os.path.join(tempfile.gettempdir(), f"sovereign_xlsx_{unique_id}.xlsx")

print("=" * 60)
print("Office Operations - Production-Grade COM Test")
print("=" * 60)

from actuators.office_ops import (
    append_text_to_doc, 
    read_word_document, 
    write_excel_cell, 
    read_excel_data,
    COM_AVAILABLE
)

print(f"\nCOM Available: {COM_AVAILABLE}")

# Word Test
print(f"\n--- Word Test ---")
print(f"File: {os.path.basename(doc_path)}")

result = append_text_to_doc("Hello from Sovereign Desktop!", doc_path, visible=False)
if result["success"]:
    print("  [PASS] Write document")
else:
    print(f"  [FAIL] Write document: {result['error']}")

if result["success"]:
    read_result = read_word_document(doc_path)
    if read_result["success"] and "Sovereign" in read_result["content"]:
        print("  [PASS] Read document")
    else:
        print(f"  [FAIL] Read document: {read_result.get('error', 'content mismatch')}")

# Excel Test
print(f"\n--- Excel Test ---")
print(f"File: {os.path.basename(xlsx_path)}")

result = write_excel_cell(xlsx_path, "A1", "Sovereign Test", visible=False)
if result["success"]:
    print("  [PASS] Write cell")
else:
    print(f"  [FAIL] Write cell: {result['error']}")

if result["success"]:
    read_result = read_excel_data(xlsx_path, "A1")
    if read_result["success"] and read_result["data"][0][0] == "Sovereign Test":
        print("  [PASS] Read cell")
    else:
        print(f"  [FAIL] Read cell: {read_result.get('error', 'data mismatch')}")

# Cleanup
print("\n--- Cleanup ---")
for f in [doc_path, xlsx_path]:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"  [OK] Deleted {os.path.basename(f)}")
    except Exception as e:
        print(f"  [WARN] Could not delete {os.path.basename(f)}: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
