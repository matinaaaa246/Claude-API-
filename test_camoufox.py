import asyncio
import json
from camoufox.async_api import AsyncCamoufox

async def main():
    with open('/root/claude-api/cookies/cookie_20.json', 'r') as f:
        cookies = json.load(f)
    for c in cookies:
        if 'sameSite' in c:
            v = str(c['sameSite']).lower()
            c['sameSite'] = 'None' if 'none' in v else ('Lax' if 'lax' in v else ('Strict' if 'strict' in v else 'None'))

    storage_state = {
        'cookies': cookies,
        'origins': []
    }

    print('Launching AsyncCamoufox...')
    async with AsyncCamoufox(headless=True, geoip=True) as browser:
        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        print('Navigating to https://claude.ai/new ...')
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=60000)
        
        for i in range(15):
            await asyncio.sleep(1)
            title = await page.title()
            print(f'Second {i+1}: URL={page.url} | Title={title}')
            if 'Just a moment' not in title and 'challenge' not in page.url:
                print('Bypassed successfully!')
                break
        
        box = await page.query_selector('div[contenteditable= true], textarea')
        print('Found prompt box?:', box is not None)
        await page.screenshot(path='/root/claude-api/camoufox.png')
        await browser.close()

asyncio.run(main())
