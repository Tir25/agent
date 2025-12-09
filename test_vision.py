"""Quick test for VisionTool"""
from app.services.system.screen_capture import ScreenCaptureTool
from app.services.ai.vision import VisionTool

print("=" * 60)
print("VISION TOOL TEST")
print("=" * 60)

# Step 1: Capture screenshot
print("\n[1] Capturing screenshot...")
capture = ScreenCaptureTool()
capture_result = capture.execute()

if not capture_result.success:
    print(f"✗ Screenshot failed: {capture_result.error}")
    exit(1)

image_path = capture_result.data["path"]
print(f"✓ Screenshot saved: {image_path}")
print(f"  Size: {capture_result.data['width']}x{capture_result.data['height']}")

# Step 2: Analyze with Vision
print("\n[2] Analyzing with llama3.2-vision...")
vision = VisionTool()
print(f"  Model: {vision.model}")

result = vision.execute(
    image_path=image_path,
    query="What do you see in this screenshot? Describe the main elements in 2-3 sentences."
)

if result.success:
    print(f"\n✓ Analysis complete!")
    print(f"\nResponse:")
    print("-" * 40)
    print(result.data["response"])
    print("-" * 40)
else:
    print(f"\n✗ Failed: {result.error}")

print("\n" + "=" * 60)
