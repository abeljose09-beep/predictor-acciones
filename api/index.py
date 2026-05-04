from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess, json, sys, os

app = Flask(__name__)
CORS(app)

@app.route('/api/index')
@app.route('/analizar')
def analizar():
    ticker = request.args.get('ticker', 'AAPL')
    try:
        # En Vercel, el ejecutable de python puede variar, pero 'python3' o sys.executable suelen funcionar
        result = subprocess.run(
            [sys.executable, 'modelo.py', ticker],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500
            
        data = json.loads(result.stdout)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Esto permite correrlo localmente también
if __name__ == '__main__':
    app.run(debug=True, port=5000)
