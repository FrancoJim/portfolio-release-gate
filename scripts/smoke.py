"""Verify the deployed routes, including a real application calculation."""
import json
import sys
import time
import urllib.request

url = sys.argv[1].rstrip('/')
for attempt in range(6):
    try:
        with urllib.request.urlopen(url + '/health', timeout=10) as response:
            assert json.load(response) == {'status': 'ok'}
        with urllib.request.urlopen(url + '/', timeout=10) as response:
            assert b'Ready to release?' in response.read()
        body = json.dumps(dict.fromkeys(('tests_passed', 'rollback_ready', 'backup_verified', 'owner_assigned'), True)).encode()
        request = urllib.request.Request(url + '/api/check', data=body, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
            assert result['ready'] is True and result['passed'] == 4
        print('Live smoke checks passed:', url)
        break
    except Exception:
        if attempt == 5:
            raise
        time.sleep(5)
