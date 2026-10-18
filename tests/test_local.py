import json
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request

from app.local import make_server


class LocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_loopback_and_smoke(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        subprocess.run([sys.executable, 'scripts/smoke.py', self.url], check=True)

    def test_transport_errors_and_headers(self):
        for body, status in [(b'x' * 4097, 413), (b'\xff', 400)]:
            with self.subTest(status=status):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(self.url + '/api/check', data=body, timeout=5)
                self.assertEqual(caught.exception.code, status)
        with urllib.request.urlopen(self.url + '/app.js', timeout=5) as result:
            self.assertEqual(result.headers['X-Content-Type-Options'], 'nosniff')
            self.assertIn(b'fetch', result.read())
        request = urllib.request.Request(self.url + '/api/check', method='PUT')
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 405)
