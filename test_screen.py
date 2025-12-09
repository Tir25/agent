"""Quick test for ScreenCaptureTool"""
from app.services.system.screen_capture import ScreenCaptureTool
from pathlib import Path

tool = ScreenCaptureTool()
print(f"Name: {tool.name}")
print(f"Description: {tool.description}")

result = tool.execute()

if result.success:
    print(f"\n✓ Screenshot captured!")
    print(f"  Path: {result.data['path']}")
    print(f"  Size: {result.data['width']}x{result.data['height']}")
    print(f"  Monitor: {result.data['monitor']}")
    
    # Verify file exists
    path = Path(result.data['path'])
    if path.exists():
        size_kb = path.stat().st_size / 1024
        print(f"  File Size: {size_kb:.1f} KB")
else:
    print(f"\n✗ Failed: {result.error}")
