import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    with open('/root/claude-api/cookies/cookie_20.json', 'r') as f:
        cookies = json.load(f)
    
    # fix samesite
    for cookie in cookies:
        if 'sameSite' in cookie:
            val = str(cookie['sameSite']).lower()
            if 'none' in val:
                cookie['sameSite'] = 'None'
            elif 'lax' in val:
                cookie['sameSite'] = 'Lax'
            elif 'strict' in val:
                cookie['sameSite'] = 'Strict'
            else:
                cookie['sameSite'] = 'None'

    storage_state = {
        'cookies': cookies,
        'origins': []
    }

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
            storage_state=storage_state,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1366, 'height': 768}
        )
        page = await context.new_page()
        print('Navigating to https://claude.ai/new ...')
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(8)
        print('Final URL:', page.url)
        print('Final Title:', await page.title())
        box = await page.query_selector('div[contenteditable= true], textarea')
        print('Found prompt box?:', box is not None)
        await page.screenshot(path='/root/claude-api/stealth3.png')
        await browser.close()

asyncio.run(main())
