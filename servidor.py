from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import subprocess, json, sys

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('interfaz.html', 'rb') as f:
                self.wfile.write(f.read())
        elif parsed.path == '/analizar':
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

import socket
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(('8.8.8.8', 1)); ip = s.getsockname()[0]
    except: ip = '127.0.0.1'
    finally: s.close()
    return ip

import os
port = int(os.environ.get('PORT', 5000))
ip = get_ip()
print(f"🚀 Servidor activo")
print(f"🔗 Local: http://localhost:{port}")
print(f"📱 Red: http://{ip}:{port}")
HTTPServer(('0.0.0.0', port), Handler).serve_forever()