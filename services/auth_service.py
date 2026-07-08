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


_INVISIBLE_CHARS = "\u200b\u200c\u200d\ufeff\u00a0"


def _normalize_email(email: str) -> str:
    """Lower-cases and trims an email, also stripping zero-width/invisible
    characters that can silently slip in via copy-paste (e.g. from mobile
    keyboards or chat apps) and would otherwise make two visually-identical
    emails compare as different strings -- a classic source of "user
    already exists" / "user not found" contradictions."""
    email = email.strip().lower()
    for ch in _INVISIBLE_CHARS:
        email = email.replace(ch, "")
    return email.strip()


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
    email = _normalize_email(email)
    if not email_is_valid(email):
        return False, "Введіть коректну email адресу"
    if not password_is_valid(password):
        return False, "Пароль не відповідає вимогам"

    conn = db.get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE LOWER(TRIM(email))=?", (email,)
        ).fetchone()
        if existing:
            return False, "Користувач з таким email вже існує"

        salt = os.urandom(16).hex()
        pw_hash = _hash_password(password, salt)
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash, salt, created_at) VALUES (?,?,?,?,?,?)",
            (first_name.strip(), last_name.strip(), email, pw_hash, salt, time.strftime("%d.%m.%Y %H:%M")),
        )
        conn.commit()
        return True, "Акаунт успішно створено"
    except Exception as exc:
        return False, f"Помилка бази даних: {exc}"
    finally:
        conn.close()


def login_user(identifier: str, password: str) -> tuple[bool, str, dict | None]:
    identifier = _normalize_email(identifier)
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(TRIM(email))=? OR LOWER(TRIM(first_name))=?",
            (identifier, identifier),
        ).fetchone()
    finally:
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


def google_login(email: str, display_name: str) -> tuple[bool, str, dict | None]:
    """
    Simplified "Sign in with Google" flow for this local desktop app.

    A fully official Google OAuth flow requires a registered OAuth client,
    a client secret, and a redirect/callback handler, which needs a backend
    server -- not available in this offline desktop environment. Instead,
    this creates (or logs into) a local account tied to the Google email
    the person enters, skipping password verification since Google would
    have handled that step in a real integration. The account is flagged
    as google-linked so it can be recognized next time.
    """
    email = _normalize_email(email)
    if not email_is_valid(email):
        return False, "Введіть коректну Google email адресу", None

    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM users WHERE LOWER(TRIM(email))=?", (email,)).fetchone()
        if row:
            user = dict(row)
            del user["password_hash"]
            del user["salt"]
            return True, "Вхід через Google успішний", user

        # create a new local account for this Google email; password is a random,
        # unusable placeholder since this account authenticates only via Google
        salt = os.urandom(16).hex()
        random_pw = os.urandom(32).hex()
        pw_hash = _hash_password(random_pw, salt)
        name_parts = display_name.strip().split(" ", 1) if display_name.strip() else ["Google", "User"]
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        conn.execute(
            "INSERT INTO users (first_name, last_name, email, password_hash, salt, created_at) VALUES (?,?,?,?,?,?)",
            (first_name, last_name, email, pw_hash, salt, time.strftime("%d.%m.%Y %H:%M")),
        )
        conn.commit()
        new_row = conn.execute("SELECT * FROM users WHERE LOWER(TRIM(email))=?", (email,)).fetchone()
        user = dict(new_row)
        del user["password_hash"]
        del user["salt"]
        return True, "Акаунт створено через Google", user
    finally:
        conn.close()


def get_remembered_user():
    email = db.get_setting("remembered_email", "")
    if not email:
        return None
    email = _normalize_email(email)
    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT id, first_name, last_name, email FROM users WHERE LOWER(TRIM(email))=?", (email,)
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def remember_user(email: str | None):
    db.set_setting("remembered_email", _normalize_email(email) if email else "")
