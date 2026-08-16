import functools
import secrets
from datetime import datetime, timedelta, timezone

from flask import g, jsonify, request

from ..db import get_db
from ..errors import ApiError

SESSION_DAYS = 30


def create_session(user_id):
    token = secrets.token_hex(32)
    expires = (
        datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=SESSION_DAYS)
    ).strftime("%Y-%m-%d %H:%M:%S")
    db = get_db()
    db.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires),
    )
    db.commit()
    return token


def revoke_session(token):
    db = get_db()
    db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    db.commit()


def get_current_user():
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth[len("Bearer "):]
    if not token:
        return None
    db = get_db()
    row = db.execute(
        "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token = ? AND s.expires_at > datetime('now')",
        (token,),
    ).fetchone()
    return row


def require_auth(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            raise ApiError("Unauthorized", 401)
        g.user = user
        return fn(*args, **kwargs)

    return wrapper


def bearer_token():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):]
    return None
