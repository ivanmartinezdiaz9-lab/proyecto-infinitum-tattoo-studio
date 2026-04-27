from __future__ import annotations

import os
import csv
import re
from datetime import datetime, timedelta
from flask import Flask, render_template, send_from_directory, request, jsonify
from flask_compress import Compress

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["COMPRESS_MIMETYPES"] = [
    "text/html", "text/css", "text/xml", "application/json", "application/javascript", "image/svg+xml"
]
app.config["COMPRESS_LEVEL"] = 6
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(days=30)
Compress(app)


WAITLIST_FILE = os.environ.get("WAITLIST_FILE", "waitlist.csv")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def append_waitlist_row(email: str, instagram: str = "", alias: str = "") -> int:
    """Guarda un registro simple de waitlist y devuelve posición aproximada."""
    file_exists = os.path.exists(WAITLIST_FILE)
    existing_emails = set()
    if file_exists:
        with open(WAITLIST_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("email"):
                    existing_emails.add(row["email"].strip().lower())

    normalized_email = email.strip().lower()
    if normalized_email not in existing_emails:
        with open(WAITLIST_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["created_at", "email", "instagram", "alias", "source"])
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                "email": normalized_email,
                "instagram": instagram.strip(),
                "alias": alias.strip(),
                "source": "infinitum_merch_drop_001",
            })
            existing_emails.add(normalized_email)

    return max(1, len(existing_emails))

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



@app.route("/waitlist", methods=["POST"])
def waitlist():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip()
    instagram = str(data.get("instagram", "")).strip()
    alias = str(data.get("alias", "")).strip()

    if not EMAIL_RE.match(email):
        return jsonify({"status": "error", "message": "Email inválido."}), 400

    position = append_waitlist_row(email=email, instagram=instagram, alias=alias)
    return jsonify({
        "status": "ok",
        "message": "Solicitud recibida.",
        "position": position,
        "wave": "PENDING",
    })

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
