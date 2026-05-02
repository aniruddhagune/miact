import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        errors = []
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: errors.append(f"[ERROR] {err}"))
        
        print("Navigating to http://localhost:5173...")
        await page.goto("http://localhost:5173")
        await page.wait_for_timeout(1000)
        
        print("Typing oneplus 9...")
        await page.fill('input[placeholder="Search, compare devices, or analyze news..."]', "oneplus 9")
        await page.press('input[placeholder="Search, compare devices, or analyze news..."]', "Enter")
        
        print("Waiting 15 seconds for pipeline...")
        await page.wait_for_timeout(15000)
        
        print("Typing oneplus 9 AGAIN...")
        await page.fill('input[placeholder="Search, compare devices, or analyze news..."]', "oneplus 9")
        await page.press('input[placeholder="Search, compare devices, or analyze news..."]', "Enter")
        
        print("Waiting 10 seconds...")
        await page.wait_for_timeout(10000)
        
        print("--- ERRORS CAPTURED ---")
        for err in errors:
            print(err)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
