"""
Browser Tool Comprehensive Test Suite

Tests web browsing capabilities with different complexity levels:
1. Simple: Open a website
2. Medium: Search and read content
3. Complex: Multi-step navigation

Note: Each test will open a visible browser window
"""

import time
from app.services.web.browser import BrowserTool

def run_test(name: str, task: str, expected_time: int = 60):
    """Run a single browser test."""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"Task: {task}")
    print(f"Expected time: ~{expected_time}s")
    print("="*60)
    
    tool = BrowserTool(headless=False)
    start = time.time()
    
    result = tool.execute(task_description=task)
    
    elapsed = time.time() - start
    
    print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Time: {elapsed:.1f}s")
    
    if result.success:
        response = result.data.get("result", "No result")
        # Truncate long responses
        if len(response) > 500:
            response = response[:500] + "..."
        print(f"Response: {response}")
        print(f"Steps: {result.data.get('steps', 'Unknown')}")
    else:
        print(f"Error: {result.error}")
    
    return result.success

def main():
    print("="*60)
    print("BROWSER TOOL COMPREHENSIVE TEST")
    print("="*60)
    print("\nThis will open browser windows for each test.")
    print("Press Ctrl+C to abort at any time.")
    
    tests = [
        # Level 1: Simple - Just open a page
        (
            "SIMPLE - Open Google",
            "Go to google.com and confirm the page loaded",
            30
        ),
        
        # Level 2: Medium - Search
        (
            "MEDIUM - Google Search",
            "Go to google.com and search for 'Python programming language'",
            45
        ),
        
        # Level 3: Medium - Read content
        (
            "MEDIUM - Wikipedia",
            "Go to wikipedia.org and search for 'Artificial Intelligence' and tell me the first paragraph",
            60
        ),
        
        # Level 4: Complex - Multi-step
        (
            "COMPLEX - News Headlines",
            "Go to news.ycombinator.com and tell me the top 3 headlines",
            90
        ),
    ]
    
    results = []
    
    for name, task, timeout in tests:
        input(f"\n>>> Press ENTER to start test: {name}")
        
        try:
            success = run_test(name, task, timeout)
            results.append((name, success))
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            break
        except Exception as e:
            print(f"\n\nTest crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
