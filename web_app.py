
from flask import Flask
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return "¡Bienvenido a PUCP Cloud Orchestrator Web!"

@app.route('/topologia')
def topologia():
    result = subprocess.run(["python3", "topologia_app.py"], capture_output=True, text=True)
    return f"<pre>{result.stdout}</pre>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3080)
