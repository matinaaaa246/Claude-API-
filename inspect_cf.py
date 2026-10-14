import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    with open('/root/claude-api/cookies/cookie_20.json', 'r') as f:
        cookies = json.load(f)
    for c in cookies:
        if 'sameSite' in c:
            v = str(c['sameSite']).lower()
            c['sameSite'] = 'None' if 'none' in v else ('Lax' if 'lax' in v else ('Strict' if 'strict' in v else 'None'))

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        context = await browser.new_context(
            storage_state={'cookies': cookies, 'origins': []},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        await page.goto('https://claude.ai/new', wait_until='networkidle', timeout=60000)
        print('Current URL:', page.url)
        print('Page title:', await page.title())
        content = await page.content()
        with open('/root/claude-api/cf_dump.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('Dumped HTML, length:', len(content))
        # Wait up to 15 seconds to see if it solves automatically
        for i in range(15):
            await asyncio.sleep(1)
            if 'challenge' not in page.url:
                print(f'Bypassed at second {i+1}! New URL: {page.url}')
                break
        print('After 15s URL:', page.url)
        print('After 15s Title:', await page.title())
        await browser.close()

asyncio.run(main())
