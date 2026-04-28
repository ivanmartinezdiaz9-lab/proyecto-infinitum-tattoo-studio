from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

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
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "1uch-_b3nIl4cjevg6LCqIIhaxo8Xz4qMMsXQAQjMpTM")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
DROP_ID = os.environ.get("DROP_ID", "infinitum_merch_drop_001")

# Origen guarda el ref real: instagram, tiktok, whatsapp, direct, etc.
HEADERS = ["Fecha", "Email", "Instagram", "Alias", "Origen", "Token", "Estado", "Wave", "Prioridad", "Expira", "Drop ID"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_sheet():
    if not GOOGLE_SHEET_ID:
        raise RuntimeError("Falta configurar GOOGLE_SHEET_ID.")
    if not GOOGLE_CREDENTIALS_JSON:
        raise RuntimeError("Falta configurar GOOGLE_CREDENTIALS_JSON.")

    credentials_info = json.loads(GOOGLE_CREDENTIALS_JSON)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1


def ensure_sheet_headers(sheet) -> list[str]:
    """Garantiza los encabezados sin romper hojas existentes."""
    values = sheet.get_all_values()
    if not values:
        sheet.append_row(HEADERS)
        return HEADERS

    current_headers = [h.strip() for h in values[0]]
    missing = [header for header in HEADERS if header not in current_headers]
    if missing:
        current_headers = current_headers + missing
        end_col = chr(ord("A") + len(current_headers) - 1)
        sheet.update(f"A1:{end_col}1", [current_headers])
    return current_headers


def row_to_dict(headers: list[str], row: list[str]) -> dict[str, str]:
    return {header: row[i] if i < len(row) else "" for i, header in enumerate(headers)}


def make_token(email: str) -> str:
    raw = f"{email}:{utc_now().timestamp()}:{secrets.token_urlsafe(16)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()


def calculate_priority(instagram: str = "", alias: str = "", origin: str = "") -> int:
    score = 100
    if instagram.strip():
        score += 25
    if alias.strip():
        score += 10
    if origin.strip() and origin.strip().lower() not in {"direct", "unknown"}:
        score += 20
    return score


def calculate_wave(position: int, priority: int) -> str:
    effective_position = max(1, position - max(0, priority - 100))
    if effective_position <= 50:
        return "WAVE_01"
    if effective_position <= 250:
        return "WAVE_02"
    if effective_position <= 500:
        return "WAVE_03"
    return "PENDING"


def calculate_state(wave: str) -> str:
    if wave == "WAVE_01":
        return "APPROVED"
    if wave in {"WAVE_02", "WAVE_03"}:
        return "REVIEWING"
    return "PENDING"


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def update_existing_access(sheet, row_number: int, headers: list[str], record: dict[str, str], access: dict[str, object], origin: str) -> None:
    """Completa campos nuevos en registros viejos sin duplicar el email."""
    updates = {
        "Origen": origin or record.get("Origen") or "direct",
        "Token": str(access["token"]),
        "Estado": str(access["state"]),
        "Wave": str(access["wave"]),
        "Prioridad": str(access["priority"]),
        "Expira": str(access["expires_at"]),
        "Drop ID": DROP_ID,
    }

    cells = []
    for header, value in updates.items():
        if header in headers and not record.get(header):
            col = headers.index(header) + 1
            cells.append(gspread.Cell(row_number, col, value))

    if cells:
        sheet.update_cells(cells)


def append_waitlist_row(email: str, instagram: str = "", alias: str = "", origin: str = "direct") -> dict[str, object]:
    sheet = get_sheet()
    headers = ensure_sheet_headers(sheet)

    values = sheet.get_all_values()
    rows = values[1:]

    normalized_email = email.strip().lower()
    clean_origin = (origin.strip() or "direct")[:120]
    existing_records = [row_to_dict(headers, row) for row in rows]

    for idx, record in enumerate(existing_records, start=1):
        if record.get("Email", "").strip().lower() == normalized_email:
            priority = safe_int(record.get("Prioridad"), calculate_priority(
                instagram=record.get("Instagram", instagram),
                alias=record.get("Alias", alias),
                origin=record.get("Origen", clean_origin),
            ))
            wave = record.get("Wave") or calculate_wave(idx, priority)
            state = record.get("Estado") or calculate_state(wave)
            token = record.get("Token") or make_token(normalized_email)
            expires_at = record.get("Expira") or iso_z(utc_now() + timedelta(days=7))
            access = {
                "position": idx,
                "token": token,
                "wave": wave,
                "state": state,
                "priority": priority,
                "expires_at": expires_at,
                "already_registered": True,
            }
            update_existing_access(sheet, idx + 1, headers, record, access, clean_origin)
            return access

    position = len(existing_records) + 1
    priority = calculate_priority(instagram=instagram, alias=alias, origin=clean_origin)
    wave = calculate_wave(position, priority)
    state = calculate_state(wave)
    token = make_token(normalized_email)
    expires_at = iso_z(utc_now() + timedelta(days=7))

    sheet.append_row([
        iso_z(utc_now()),
        normalized_email,
        instagram.strip(),
        alias.strip(),
        clean_origin,
        token,
        state,
        wave,
        priority,
        expires_at,
        DROP_ID,
    ])

    return {
        "position": position,
        "token": token,
        "wave": wave,
        "state": state,
        "priority": priority,
        "expires_at": expires_at,
        "already_registered": False,
    }


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
    origin = str(data.get("ref") or data.get("origin") or request.args.get("ref") or "direct").strip()

    if not EMAIL_RE.match(email):
        return jsonify({"status": "error", "message": "Email inválido."}), 400

    try:
        access = append_waitlist_row(email=email, instagram=instagram, alias=alias, origin=origin)
    except Exception as exc:
        print("Error guardando en Google Sheets:", exc)
        return jsonify({
            "status": "error",
            "message": "No se pudo guardar la solicitud.",
        }), 500

    message = "Solicitud recuperada." if access["already_registered"] else "Solicitud recibida."

    return jsonify({
        "status": "ok",
        "message": message,
        "position": access["position"],
        "token": access["token"],
        "wave": access["wave"],
        "state": access["state"],
        "priority": access["priority"],
        "expires_at": access["expires_at"],
        "already_registered": access["already_registered"],
    })


@app.route("/access/<token>")
def access_status(token: str):
    sheet = get_sheet()
    headers = ensure_sheet_headers(sheet)

    values = sheet.get_all_values()

    for idx, row in enumerate(values[1:], start=1):
        record = row_to_dict(headers, row)
        if record.get("Token", "").strip().upper() == token.strip().upper():
            priority = safe_int(record.get("Prioridad"), 100)
            wave = record.get("Wave") or calculate_wave(idx, priority)
            return jsonify({
                "status": "ok",
                "position": idx,
                "wave": wave,
                "state": record.get("Estado") or calculate_state(wave),
                "expires_at": record.get("Expira") or "",
            })

    return jsonify({"status": "error", "message": "Token no encontrado."}), 404


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
