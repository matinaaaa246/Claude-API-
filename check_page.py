import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            storage_state='/root/claude-api/cookies/cookie_20.json',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=45000)
        await asyncio.sleep(5)
        print('URL:', page.url)
        print('TITLE:', await page.title())
        content = await page.content()
        with open('/root/claude-api/page_20.html', 'w', encoding='utf-8') as f:
            f.write(content)
        await browser.close()

asyncio.run(test())
