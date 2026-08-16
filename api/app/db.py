import os
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE_PATH"]
        if path == ":memory:":
            conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    path = app.config["DATABASE_PATH"]
    if path != ":memory:":
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with app.app_context():
        db = get_db()
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path) as f:
            db.executescript(f.read())
        db.commit()
