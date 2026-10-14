import json
from curl_cffi import requests

with open('/root/claude-api/cookies/cookie_20.json', 'r') as f:
    raw_cookies = json.load(f)

cookie_dict = {}
for c in raw_cookies:
    cookie_dict[c['name']] = c['value']

print('Loaded cookies:', len(cookie_dict))
print('sessionKey present:', 'sessionKey' in cookie_dict)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://claude.ai/new',
    'Origin': 'https://claude.ai',
}

try:
    resp = requests.get(
        'https://claude.ai/api/organizations',
        cookies=cookie_dict,
        headers=headers,
        impersonate='chrome124',
        timeout=15
    )
    print('Status Code:', resp.status_code)
    print('Response Headers:', resp.headers.get('content-type'))
    print('Response Text Preview:', resp.text[:500])
except Exception as e:
    print('Request error:', e)
