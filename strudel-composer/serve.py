# Static server for the ear, plus PUT of .wav files so the page can save its renders next to the tracks.
# Usage, from the project root: python serve.py [port]
import http.server
import sys


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_PUT(self):
        path = self.translate_path(self.path)  # stays inside the served folder
        if not path.endswith('.wav'):
            return self.send_error(403, 'only .wav files can be written')
        with open(path, 'wb') as f:
            f.write(self.rfile.read(int(self.headers['Content-Length'])))
        self.send_response(201)
        self.end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
http.server.ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
