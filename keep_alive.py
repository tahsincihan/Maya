import os
import logging
from flask import Flask
from threading import Thread

# Disable Flask default logs to keep console clean
flask_log = logging.getLogger('werkzeug')
flask_log.setLevel(logging.ERROR)

app = Flask(__name__)
log = logging.getLogger(__name__)

@app.route('/')
def home():
    return "I am alive!"

def run():
    # Render sets a PORT environment variable. We default to 8080.
    port = int(os.environ.get("PORT", 8080))
    log.info(f"Starting keep-alive Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """Starts the Flask server on a separate daemon thread."""
    t = Thread(target=run, daemon=True)
    t.start()
    log.info("Keep-alive thread started.")
