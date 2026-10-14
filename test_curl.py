import requests

cookies = {
    'sessionKey': 'sk-ant-sid01-xxx' # test structure
}
r = requests.get('https://claude.ai/api/organizations', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
})
print('Status:', r.status_code)
print('Response text snippet:', r.text[:200])
