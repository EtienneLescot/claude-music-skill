# Static server for the ear: the project folder (tracks, renders) plus ear.html from this skill folder,
# and PUT of .wav files so the page can save its renders next to the tracks.
# Usage, from the project root: python /path/to/serve.py [port]
import http.server
import sys
import urllib.parse
from pathlib import Path

EAR = Path(__file__).with_name('ear.html')


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if urllib.parse.urlsplit(path).path == '/ear.html':
            return str(EAR)
        return super().translate_path(path)  # stays inside the served folder

    def do_PUT(self):
        path = self.translate_path(self.path)
        if not path.endswith('.wav'):
            return self.send_error(403, 'only .wav files can be written')
        with open(path, 'wb') as f:
            f.write(self.rfile.read(int(self.headers['Content-Length'])))
        self.send_response(201)
        self.end_headers()


def make_server(port=8765):
    return http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    make_server(int(sys.argv[1]) if len(sys.argv) > 1 else 8765).serve_forever()
