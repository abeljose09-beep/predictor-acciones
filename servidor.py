from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess, json, sys

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/analizar':
            ticker = parse_qs(parsed.query).get('ticker', ['AAPL'])[0]
            try:
                result = subprocess.run(
                    [sys.executable, 'modelo.py', ticker],
                    capture_output=True, text=True, timeout=120
                )
                data = json.loads(result.stdout)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass

print("🚀 Servidor corriendo en http://localhost:5000")
HTTPServer(('localhost', 5000), Handler).serve_forever()