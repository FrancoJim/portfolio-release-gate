import base64
import json
import unittest
from app.handler import handler, CHECKS


def invoke(data=None, method='POST', path='/api/check', **extra):
    return handler({'requestContext': {'http': {'method': method}}, 'rawPath': path,
                    'body': json.dumps(data), **extra}, None)


class HandlerTests(unittest.TestCase):
    def test_ready(self):
        result = invoke(dict.fromkeys(CHECKS, True))
        self.assertEqual(result['statusCode'], 200)
        self.assertTrue(json.loads(result['body'])['ready'])

    def test_missing(self):
        data = dict.fromkeys(CHECKS, True)
        data['rollback_ready'] = False
        self.assertEqual(json.loads(invoke(data)['body'])['missing'], ['rollback_ready'])

    def test_rejects_invalid_shapes_and_types(self):
        for data in (None, [], {}, dict.fromkeys(CHECKS, 'true'), dict.fromkeys(CHECKS, 1), {**dict.fromkeys(CHECKS, True), 'extra': True}):
            with self.subTest(data=data):
                self.assertEqual(invoke(data)['statusCode'], 400)

    def test_invalid_encoding(self):
        for body in ('{', '%%%'):
            self.assertEqual(invoke(body=body, isBase64Encoded=True)['statusCode'], 400)

    def test_base64_request(self):
        body = base64.b64encode(json.dumps(dict.fromkeys(CHECKS, True)).encode()).decode()
        self.assertEqual(invoke(body=body, isBase64Encoded=True)['statusCode'], 200)

    def test_large_body(self):
        self.assertEqual(invoke(body='x' * 9000)['statusCode'], 413)

    def test_routes(self):
        for path in ('/', '/app.js', '/health'):
            self.assertEqual(invoke(method='GET', path=path)['statusCode'], 200)
        self.assertEqual(invoke(method='GET')['statusCode'], 405)
        self.assertEqual(invoke(path='/missing')['statusCode'], 404)
        self.assertEqual(invoke(method='POST', path='/')['statusCode'], 404)
