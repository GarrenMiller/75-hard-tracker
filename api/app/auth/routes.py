import re

from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import get_db
from ..errors import ApiError
from .utils import bearer_token, create_session, require_auth, revoke_session

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _user_payload(user):
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
    }


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip()

    if not EMAIL_RE.match(email):
        raise ApiError("A valid email is required", 400)
    if len(password) < 8:
        raise ApiError("Password must be at least 8 characters", 400)
    if not display_name:
        raise ApiError("Display name is required", 400)

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        raise ApiError("Email already registered", 409)

    password_hash = generate_password_hash(password)
    cur = db.execute(
        "INSERT INTO users (email, password_hash, display_name) VALUES (?, ?, ?)",
        (email, password_hash, display_name),
    )
    db.commit()

    token = create_session(cur.lastrowid)
    user = db.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify({"token": token, "user": _user_payload(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        raise ApiError("Invalid email or password", 401)

    token = create_session(user["id"])
    return jsonify({"token": token, "user": _user_payload(user)})


@auth_bp.post("/logout")
@require_auth
def logout():
    token = bearer_token()
    if token:
        revoke_session(token)
    return jsonify({"ok": True})


@auth_bp.get("/me")
@require_auth
def me():
    return jsonify({"user": _user_payload(g.user)})
