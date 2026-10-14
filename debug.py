import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state="/root/claude-api/cookies/cookie_5.json",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating...")
        await page.goto("https://claude.ai/new", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)
        print("Current URL:", page.url)
        content = await page.content()
        with open("/root/claude-api/debug.html", "w", encoding="utf-8") as f:
            f.write(content)
        await page.screenshot(path="/root/claude-api/debug.png")
        await browser.close()
        print("Done!")

asyncio.run(main())
