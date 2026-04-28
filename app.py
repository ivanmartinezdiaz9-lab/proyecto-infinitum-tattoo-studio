from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta

import gspread
from flask import Flask, jsonify, render_template, request
from flask_compress import Compress
from google.oauth2.service_account import Credentials

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["COMPRESS_MIMETYPES"] = [
    "text/html",
    "text/css",
    "text/xml",
    "application/json",
    "application/javascript",
    "image/svg+xml",
]
app.config["COMPRESS_LEVEL"] = 6
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = timedelta(days=30)
Compress(app)

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ID de tu Google Sheet:
# https://docs.google.com/spreadsheets/d/1uch-_b3nIl4cjevg6LCqIIhaxo8Xz4qMMsXQAQjMpTM/edit
GOOGLE_SHEET_ID = os.environ.get(
    "GOOGLE_SHEET_ID",
    "1uch-_b3nIl4cjevg6LCqIIhaxo8Xz4qMMsXQAQjMpTM",
)
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")


def get_sheet():
    """Conecta con Google Sheets usando la service account guardada en variables de entorno."""
    if not GOOGLE_SHEET_ID:
        raise RuntimeError("Falta configurar GOOGLE_SHEET_ID.")

    if not GOOGLE_CREDENTIALS_JSON:
        raise RuntimeError("Falta configurar GOOGLE_CREDENTIALS_JSON.")

    credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        credentials_info,
        scopes=scopes,
    )

    client = gspread.authorize(credentials)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1


def ensure_sheet_headers(sheet) -> None:
    """Crea los encabezados si la hoja está vacía."""
    values = sheet.get_all_values()

    if not values:
        sheet.append_row(["Fecha", "Email", "Instagram", "Alias", "Origen"])


def append_waitlist_row(email: str, instagram: str = "", alias: str = "") -> int:
    """Guarda un registro de waitlist en Google Sheets y devuelve la posición aproximada."""
    sheet = get_sheet()
    ensure_sheet_headers(sheet)

    values = sheet.get_all_values()

    existing_emails = {
        row[1].strip().lower()
        for row in values[1:]
        if len(row) > 1 and row[1].strip()
    }

    normalized_email = email.strip().lower()

    if normalized_email not in existing_emails:
        sheet.append_row([
            datetime.utcnow().isoformat(timespec="seconds") + "Z",
            normalized_email,
            instagram.strip(),
            alias.strip(),
            "infinitum_merch_drop_001",
        ])
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

    try:
        position = append_waitlist_row(email=email, instagram=instagram, alias=alias)
    except Exception as exc:
        print("Error guardando en Google Sheets:", exc)
        return jsonify({
            "status": "error",
            "message": "No se pudo guardar la solicitud.",
        }), 500

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
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
