import asyncio
import httpx
import json

async def test():
    data = json.load(open('/root/claude-api/cookies/cookie_20.json'))
    cookies = {}
    for c in data:
        cookies[c['name']] = c['value']
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://claude.ai/'
    }
    async with httpx.AsyncClient(cookies=cookies, headers=headers, follow_redirects=True) as client:
        r = await client.get('https://claude.ai/api/organizations')
        print('HTTPX Status:', r.status_code)
        print('HTTPX Body:', r.text[:300])

asyncio.run(test())
