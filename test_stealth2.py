import asyncio
from playwright.async_api import async_playwright
from playwright_stealth.context_managers import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        context = await browser.new_context(
            storage_state='/root/claude-api/cookies/cookie_20.json',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        await stealth_async(page)
        print('Navigating...')
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(8)
        print('URL:', page.url)
        print('Title:', await page.title())
        box = await page.query_selector('div[contenteditable=" true\], textarea')
 print('Found prompt box?:', box is not None)
 await browser.close()

asyncio.run(main())
