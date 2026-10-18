"""Loopback-only development adapter for the shared application handler."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from app.handler import MAX_BODY, handler, response


class LocalHandler(BaseHTTPRequestHandler):
    def dispatch(self):
        # Reject unsupported framing before reading; never read an unbounded body.
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length < 0 or self.headers.get('Transfer-Encoding'):
                raise ValueError
        except ValueError:
            result = response(400, {'error': 'Invalid request framing'})
        else:
            if length > MAX_BODY:
                result = response(413, {'error': 'Body too large'})
            else:
                try:
                    body = self.rfile.read(length).decode('utf-8')
                    result = handler({'requestContext': {'http': {'method': self.command}},
                                      'rawPath': urlsplit(self.path).path, 'body': body}, None)
                except UnicodeError:
                    result = response(400, {'error': 'Invalid UTF-8'})
        payload = result['body'].encode('utf-8')
        self.send_response(result['statusCode'])
        for key, value in result['headers'].items():
            self.send_header(key, value)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(payload)
        self.close_connection = True

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = do_OPTIONS = dispatch


def make_server(port=8000):
    return ThreadingHTTPServer(('127.0.0.1', port), LocalHandler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    with make_server(args.port) as server:
        print(f'Release Gate: http://127.0.0.1:{server.server_port} (Ctrl-C to stop)', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
