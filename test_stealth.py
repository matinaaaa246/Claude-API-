import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        context = await browser.new_context(
            storage_state='/root/claude-api/cookies/cookie_20.json',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        page = await context.new_page()
        print('Navigating with Stealth().use_async...')
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(8)
        print('Final URL:', page.url)
        print('Final Title:', await page.title())
        box = await page.query_selector('div[contenteditable="true"], textarea')
        print('Found prompt box?:', box is not None)
        await browser.close()

asyncio.run(main())
