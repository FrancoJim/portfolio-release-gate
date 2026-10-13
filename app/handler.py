"""Stateless release checklist demo; no external calls or customer data."""
import base64
import json
from pathlib import Path

CHECKS = ('tests_passed', 'rollback_ready', 'backup_verified', 'owner_assigned')
MAX_BODY = 4096


def response(status, body, content_type='application/json'):
    return {'statusCode': status, 'headers': {'content-type': content_type,
            'cache-control': 'no-store', 'x-content-type-options': 'nosniff',
            'content-security-policy': "default-src 'self'; style-src 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'"},
            'body': body if isinstance(body, str) else json.dumps(body)}


def handler(event, context):
    method = event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    path = event.get('rawPath', '/')
    if method == 'GET' and path == '/health':
        return response(200, {'status': 'ok'})
    if method == 'GET' and path in ('/', '/app.js'):
        filename, mime = ('index.html', 'text/html; charset=utf-8') if path == '/' else ('app.js', 'text/javascript')
        return response(200, Path(__file__).with_name(filename).read_text(), mime)
    if path != '/api/check':
        return response(404, {'error': 'Not found'})
    if method != 'POST':
        return response(405, {'error': 'Use POST'})
    raw = event.get('body') or ''
    if len(raw) > MAX_BODY * 2:
        return response(413, {'error': 'Body too large'})
    try:
        if event.get('isBase64Encoded'):
            raw = base64.b64decode(raw, validate=True).decode('utf-8')
        if len(raw.encode('utf-8')) > MAX_BODY:
            return response(413, {'error': 'Body too large'})
        data = json.loads(raw)
        if not isinstance(data, dict) or set(data) != set(CHECKS):
            raise ValueError('Expected exactly four checklist fields')
        if any(type(data[key]) is not bool for key in CHECKS):
            raise ValueError('Checklist values must be booleans')
    except (ValueError, UnicodeError):
        return response(400, {'error': 'Provide exactly four boolean checklist fields'})
    missing = [key for key in CHECKS if not data[key]]
    return response(200, {'ready': not missing, 'passed': 4 - len(missing), 'total': 4,
                          'missing': missing, 'note': 'Demo checklist only; not a production release approval.'})
