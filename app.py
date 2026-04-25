from __future__ import annotations

import os
from datetime import timedelta
from flask import Flask, render_template, send_from_directory, request
from flask_compress import Compress

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["COMPRESS_MIMETYPES"] = [
    "text/html", "text/css", "text/xml", "application/json", "application/javascript", "image/svg+xml"
]
app.config["COMPRESS_LEVEL"] = 6
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(days=30)
Compress(app)

@app.after_request
def add_cache_headers(response):
    path = request.path
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response.headers["Cache-Control"] = "public, max-age=300"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
