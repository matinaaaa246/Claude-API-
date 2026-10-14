import json

with open('/root/claude-api/cookies/cookie_20.json') as f:
    d = json.load(f)

print('Type:', type(d))
if isinstance(d, list):
    names = [c.get('name') for c in d]
    print('Cookie names:', names)
    print('Has sessionKey:', 'sessionKey' in names)
