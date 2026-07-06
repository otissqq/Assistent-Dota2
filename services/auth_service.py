"""
Local authentication service backed by SQLite (database.py: users table).

Passwords are hashed with PBKDF2-HMAC-SHA256 + a random per-user salt --
nothing is ever stored or transmitted in plain text. There is no remote
auth server in this desktop app, so "Продовжити з Google" is presented as
a UI affordance but not wired to a real OAuth flow (would require a
registered OAuth client + redirect handling, out of scope for a local
desktop demo). It's left visibly clickable but informs the user this
needs real OAuth credentials to function.
"""
import hashlib
import os
import re
import time

import database as db


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()


def password_requirements(password: str) -> dict:
    return {
        "length": len(password) >= 8,
        "lower": bool(re.search(r"[a-z]", password)),
        "upper": bool(re.search(r"[A-Z]", password)),
        "digit": bool(re.search(r"[0-9]", password)),
    }


def password_is_valid(password: str) -> bool:
    return all(password_requirements(password).values())


def email_is_valid(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def register_user(first_name, last_name, email, password) -> tuple[bool, str]:
    email = email.strip().lower()
    if not email_is_valid(email):
        return False, "Введіть коректну email адресу"
    if not password_is_valid(password):
        return False, "Пароль не відповідає вимогам"

    conn = db.get_conn()
    existing = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        conn.close()
        return False, "Користувач з таким email вже існує"

    salt = os.urandom(16).hex()
    pw_hash = _hash_password(password, salt)
    conn.execute(
        "INSERT INTO users (first_name, last_name, email, password_hash, salt, created_at) VALUES (?,?,?,?,?,?)",
        (first_name.strip(), last_name.strip(), email, pw_hash, salt, time.strftime("%d.%m.%Y %H:%M")),
    )
    conn.commit()
    conn.close()
    return True, "Акаунт успішно створено"


def login_user(identifier: str, password: str) -> tuple[bool, str, dict | None]:
    identifier = identifier.strip().lower()
    conn = db.get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE email=? OR LOWER(first_name)=?", (identifier, identifier)
    ).fetchone()
    conn.close()
    if not row:
        return False, "Користувача не знайдено", None
    pw_hash = _hash_password(password, row["salt"])
    if pw_hash != row["password_hash"]:
        return False, "Невірний пароль", None
    user = dict(row)
    del user["password_hash"]
    del user["salt"]
    return True, "Вхід успішний", user


def get_remembered_user():
    email = db.get_setting("remembered_email", "")
    if not email:
        return None
    conn = db.get_conn()
    row = conn.execute("SELECT id, first_name, last_name, email FROM users WHERE email=?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def remember_user(email: str | None):
    db.set_setting("remembered_email", email or "")
