"""
Browser Agent - Web Automation

Provides web browser automation capabilities using Playwright.
Supports navigation, interaction, and data extraction.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BrowserState:
    """Current browser state."""
    url: str
    title: str
    is_loading: bool
    cookies: List[dict]


@dataclass
class ElementInfo:
    """Information about a page element."""
    selector: str
    tag_name: str
    text: str
    attributes: Dict[str, str]
    is_visible: bool
    bounding_box: Optional[Dict[str, float]] = None


class BrowserAgent:
    """
    Web browser automation agent using Playwright.
    
    Provides high-level API for common web automation tasks
    including navigation, form filling, clicking, and data extraction.
    """
    
    def __init__(
        self,
        headless: bool = False,
        browser_type: str = "chromium",
    ):
        """
        Initialize the browser agent.
        
        Args:
            headless: Run browser in headless mode
            browser_type: "chromium", "firefox", or "webkit"
        """
        self.headless = headless
        self.browser_type = browser_type
        
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
        logger.info(f"Browser Agent initialized (headless: {headless})")
    
    async def start(self):
        """Start the browser."""
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            browser_launcher = getattr(self._playwright, self.browser_type)
            self._browser = await browser_launcher.launch(headless=self.headless)
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()
            
            logger.info("Browser started")
            
        except ImportError:
            raise ImportError("playwright not installed. Run: pip install playwright && playwright install")
    
    async def stop(self):
        """Stop the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser stopped")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.stop()
    
    # ==================== Navigation ====================
    
    async def goto(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: When to consider navigation done
                       ("load", "domcontentloaded", "networkidle")
            
        Returns:
            True if successful
        """
        try:
            await self._page.goto(url, wait_until=wait_until)
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def back(self):
        """Go back in browser history."""
        await self._page.go_back()
    
    async def forward(self):
        """Go forward in browser history."""
        await self._page.go_forward()
    
    async def reload(self):
        """Reload the current page."""
        await self._page.reload()
    
    async def get_url(self) -> str:
        """Get the current URL."""
        return self._page.url
    
    async def get_title(self) -> str:
        """Get the current page title."""
        return await self._page.title()
    
    async def get_state(self) -> BrowserState:
        """Get the current browser state."""
        cookies = await self._context.cookies()
        return BrowserState(
            url=self._page.url,
            title=await self._page.title(),
            is_loading=False,
            cookies=cookies,
        )
    
    # ==================== Element Interaction ====================
    
    async def click(self, selector: str, timeout: float = 5000):
        """
        Click an element.
        
        Args:
            selector: CSS selector or text
            timeout: Maximum time to wait for element
        """
        await self._page.click(selector, timeout=timeout)
        logger.debug(f"Clicked: {selector}")
    
    async def type(self, selector: str, text: str, delay: float = 50):
        """
        Type text into an input element.
        
        Args:
            selector: CSS selector
            text: Text to type
            delay: Delay between keystrokes (ms)
        """
        await self._page.type(selector, text, delay=delay)
        logger.debug(f"Typed into {selector}: {text[:20]}...")
    
    async def fill(self, selector: str, text: str):
        """
        Fill an input element (clears first).
        
        Args:
            selector: CSS selector
            text: Text to fill
        """
        await self._page.fill(selector, text)
        logger.debug(f"Filled {selector}: {text[:20]}...")
    
    async def select_option(self, selector: str, value: str):
        """Select an option from a dropdown."""
        await self._page.select_option(selector, value)
    
    async def check(self, selector: str):
        """Check a checkbox."""
        await self._page.check(selector)
    
    async def uncheck(self, selector: str):
        """Uncheck a checkbox."""
        await self._page.uncheck(selector)
    
    async def hover(self, selector: str):
        """Hover over an element."""
        await self._page.hover(selector)
    
    async def scroll_to(self, selector: str):
        """Scroll an element into view."""
        await self._page.locator(selector).scroll_into_view_if_needed()
    
    async def scroll_page(self, direction: str = "down", amount: int = 500):
        """
        Scroll the page.
        
        Args:
            direction: "up" or "down"
            amount: Pixels to scroll
        """
        if direction == "up":
            amount = -amount
        await self._page.evaluate(f"window.scrollBy(0, {amount})")
    
    # ==================== Waiting ====================
    
    async def wait_for_selector(self, selector: str, timeout: float = 30000):
        """Wait for an element to appear."""
        await self._page.wait_for_selector(selector, timeout=timeout)
    
    async def wait_for_navigation(self, timeout: float = 30000):
        """Wait for navigation to complete."""
        await self._page.wait_for_load_state("networkidle", timeout=timeout)
    
    async def wait_for_text(self, text: str, timeout: float = 30000):
        """Wait for specific text to appear on the page."""
        await self._page.wait_for_selector(f"text={text}", timeout=timeout)
    
    async def wait(self, milliseconds: int):
        """Wait for a specified time."""
        await self._page.wait_for_timeout(milliseconds)
    
    # ==================== Data Extraction ====================
    
    async def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return await self._page.text_content(selector)
    
    async def get_inner_text(self, selector: str) -> str:
        """Get inner text of an element."""
        return await self._page.inner_text(selector)
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value from an element."""
        return await self._page.get_attribute(selector, attribute)
    
    async def get_all_text(self, selector: str) -> List[str]:
        """Get text from all matching elements."""
        elements = await self._page.query_selector_all(selector)
        return [await el.text_content() for el in elements]
    
    async def get_html(self) -> str:
        """Get the page HTML content."""
        return await self._page.content()
    
    async def get_element_info(self, selector: str) -> Optional[ElementInfo]:
        """Get detailed information about an element."""
        try:
            element = await self._page.query_selector(selector)
            if not element:
                return None
            
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            text = await element.text_content() or ""
            is_visible = await element.is_visible()
            box = await element.bounding_box()
            
            # Get all attributes
            attrs = await element.evaluate("""el => {
                const attrs = {};
                for (const attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                return attrs;
            }""")
            
            return ElementInfo(
                selector=selector,
                tag_name=tag_name,
                text=text.strip(),
                attributes=attrs,
                is_visible=is_visible,
                bounding_box=box,
            )
        except Exception as e:
            logger.error(f"Failed to get element info: {e}")
            return None
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript and return the result."""
        return await self._page.evaluate(script)
    
    # ==================== Screenshots ====================
    
    async def screenshot(self, path: str = None, full_page: bool = False) -> bytes:
        """
        Take a screenshot.
        
        Args:
            path: Optional path to save the screenshot
            full_page: Capture the full scrollable page
            
        Returns:
            Screenshot bytes
        """
        return await self._page.screenshot(path=path, full_page=full_page)
    
    async def screenshot_element(self, selector: str, path: str = None) -> bytes:
        """Take a screenshot of a specific element."""
        element = await self._page.query_selector(selector)
        if element:
            return await element.screenshot(path=path)
        raise ValueError(f"Element not found: {selector}")
    
    # ==================== Convenience Methods ====================
    
    async def search(self, query: str, engine: str = "google"):
        """
        Perform a web search.
        
        Args:
            query: Search query
            engine: Search engine ("google", "duckduckgo", "bing")
        """
        engines = {
            "google": f"https://www.google.com/search?q={query}",
            "duckduckgo": f"https://duckduckgo.com/?q={query}",
            "bing": f"https://www.bing.com/search?q={query}",
        }
        
        url = engines.get(engine.lower(), engines["google"])
        await self.goto(url)
    
    async def fill_form(self, form_data: Dict[str, str]):
        """
        Fill a form with multiple fields.
        
        Args:
            form_data: Dictionary of selector -> value pairs
        """
        for selector, value in form_data.items():
            await self.fill(selector, value)
    
    async def submit_form(self, submit_selector: str = "button[type='submit']"):
        """Submit a form by clicking the submit button."""
        await self.click(submit_selector)
        await self.wait_for_navigation()


# Synchronous wrapper for easier use
class SyncBrowserAgent:
    """Synchronous wrapper for BrowserAgent."""
    
    def __init__(self, **kwargs):
        self._agent = BrowserAgent(**kwargs)
        self._loop = asyncio.new_event_loop()
    
    def _run(self, coro):
        return self._loop.run_until_complete(coro)
    
    def start(self):
        return self._run(self._agent.start())
    
    def stop(self):
        return self._run(self._agent.stop())
    
    def goto(self, url: str):
        return self._run(self._agent.goto(url))
    
    def click(self, selector: str):
        return self._run(self._agent.click(selector))
    
    def type(self, selector: str, text: str):
        return self._run(self._agent.type(selector, text))
    
    def fill(self, selector: str, text: str):
        return self._run(self._agent.fill(selector, text))
    
    def get_text(self, selector: str):
        return self._run(self._agent.get_text(selector))
    
    def screenshot(self, path: str = None):
        return self._run(self._agent.screenshot(path))
    
    def search(self, query: str, engine: str = "google"):
        return self._run(self._agent.search(query, engine))
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
