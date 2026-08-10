"""Password hashing and signed session-token helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
from dataclasses import dataclass
from time import time

from app.config import settings

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HASH_NAME = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 390_000


def normalize_email(email: str) -> str:
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(normalize_email(email)))


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        DEFAULT_ITERATIONS,
    )
    return f"{HASH_NAME}${DEFAULT_ITERATIONS}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        name, iterations_raw, salt_raw, digest_raw = stored_hash.split("$", 3)
        if name != HASH_NAME:
            return False
        iterations = int(iterations_raw)
        salt = _b64decode(salt_raw)
        expected = _b64decode(digest_raw)
    except Exception:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate, expected)


def _sign(payload: str) -> str:
    signature = hmac.new(
        settings.session_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _b64encode(signature)


def create_session_token(user_id: int) -> str:
    expires_at = int(time()) + settings.session_max_age_seconds
    nonce = secrets.token_urlsafe(16)
    payload = f"{user_id}.{expires_at}.{nonce}"
    return f"{payload}.{_sign(payload)}"


@dataclass(frozen=True)
class SessionToken:
    user_id: int
    expires_at: int


def verify_session_token(token: str | None) -> SessionToken | None:
    if not token:
        return None
    try:
        user_id_raw, expires_raw, nonce, signature = token.split(".", 3)
        payload = f"{user_id_raw}.{expires_raw}.{nonce}"
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        expires_at = int(expires_raw)
        if expires_at < int(time()):
            return None
        return SessionToken(user_id=int(user_id_raw), expires_at=expires_at)
    except Exception:
        return None
