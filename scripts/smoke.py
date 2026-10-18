"""Verify local or deployed routes and valid, incomplete, and invalid submissions."""
import json
import sys
import time
import urllib.request
import urllib.error

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
        incomplete = dict.fromkeys(('tests_passed', 'rollback_ready', 'backup_verified', 'owner_assigned'), True)
        incomplete['rollback_ready'] = False
        request = urllib.request.Request(url + '/api/check', data=json.dumps(incomplete).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
            assert result['ready'] is False and result['passed'] == 3
            assert result['missing'] == ['rollback_ready']
        request = urllib.request.Request(url + '/api/check', data=b'{"tests_passed":"true"}', headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as error:
            assert error.code == 400
            assert 'error' in json.load(error)
        else:
            raise AssertionError('Invalid input was accepted')
        print('Smoke checks passed (homepage, health, valid, incomplete, invalid):', url)
        break
    except Exception:
        if attempt == 5:
            raise
        time.sleep(5)
