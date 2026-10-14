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
        await page.route('**/*.{png,jpg,jpeg,webp,gif,svg,woff2,ttf,mp4,webm}', lambda r: r.abort())
        
        print('Navigating to https://claude.ai/new ...')
        await page.goto('https://claude.ai/new', wait_until='domcontentloaded', timeout=60000)
        
        prompt_selector = 'div[contenteditable= true], textarea'
        print('Waiting for prompt box...')
        await page.wait_for_selector(prompt_selector, timeout=30000)
        
        box = page.locator(prompt_selector).first
        prompt_text = 'Reply with only the word PING_OK and nothing else.'
        print('Sending prompt:', prompt_text)
        try:
            await box.fill(prompt_text)
        except Exception:
            await page.evaluate('(text) => { const el = document.querySelector(\'div[contenteditable=true], textarea\'); if (el) { el.focus(); document.execCommand(insertText, false, text); } }', prompt_text)
        await asyncio.sleep(0.5)
        await page.keyboard.press('Enter')
        
        response_selector = '.font-claude-message, .prose, div[data-message-author-role=assistant]'
        print('Waiting for assistant response...')
        await page.wait_for_selector(response_selector, timeout=45000)
        
        elements = await page.query_selector_all(response_selector)
        latest_response = elements[-1]
        
        previous_text = ''
        same_count = 0
        current_text = ''
        for _ in range(60):
            await asyncio.sleep(1.0)
            current_text = await latest_response.inner_text()
            if current_text and current_text == previous_text:
                same_count += 1
                if same_count >= 2:
                    break
            else:
                same_count = 0
                previous_text = current_text
                
        print('=== CLAUDE RESPONSE ===')
        print(current_text)
        print('=== END RESPONSE ===')
        await browser.close()

asyncio.run(main())
