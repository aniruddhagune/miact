import asyncio
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
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            logger.info("SCRAPER", "Playwright browser launched successfully")

    async def stop(self):
        if self.browser:
            await self.browser.close()
            await self.playwright.stop()
            self.browser = None
            logger.info("SCRAPER", "Playwright browser closed")

    async def scrape_url(self, url: str, timeout: int = 30000):
        """
        Scrape a URL using Playwright for dynamic content.
        """
        await self.start()
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
            logger.error("SCRAPER", f"Playwright failed for {url}: {e}")
            return None
        finally:
            await page.close()

# Global singleton
playwright_service = PlaywrightService()

async def scrape_dynamic(url: str):
    return await playwright_service.scrape_url(url)
