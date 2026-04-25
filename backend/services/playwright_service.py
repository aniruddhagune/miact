import asyncio
import traceback
import sys
from playwright.async_api import async_playwright
from backend.utils.logger import logger

class PlaywrightService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PlaywrightService, cls).__new__(cls)
            cls._instance.browser = None
            cls._instance.playwright = None
        return cls._instance

    async def start(self):
        # On Windows, create_subprocess_exec requires ProactorEventLoop
        if sys.platform == 'win32':
            try:
                if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except Exception as e:
                logger.debug("SCRAPER", f"Could not set ProactorEventLoopPolicy: {e}")

        if not self.browser:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=True)
                logger.info("SCRAPER", "Playwright browser launched successfully")
            except Exception as e:
                logger.error("SCRAPER", f"Failed to start Playwright: {e}\n{traceback.format_exc()}")
                raise

    async def stop(self):
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            logger.info("SCRAPER", "Playwright browser closed")

    async def scrape_url(self, url: str, timeout: int = 45000):
        """
        Scrape a URL using Playwright for dynamic content.
        """
        try:
            await self.start()
        except Exception:
            return None

        page = await self.browser.new_page()
        try:
            logger.debug("SCRAPER", f"Playwright navigating to: {url}")
            await page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Extract content
            content = await page.content()
            title = await page.title()
            
            # Simple text extraction as fallback
            text = await page.evaluate("() => document.body.innerText")
            
            logger.info("SCRAPER", f"Playwright successfully scraped {url}")
            return {
                "title": title,
                "text": text,
                "html": content,
                "method": "playwright",
                "source": url
            }
        except Exception as e:
            logger.error("SCRAPER", f"Playwright failed for {url}: {e}\n{traceback.format_exc()}")
            return None
        finally:
            await page.close()

# Global singleton
playwright_service = PlaywrightService()

async def scrape_dynamic(url: str):
    return await playwright_service.scrape_url(url)
