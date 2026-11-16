"""Zero-Dependency Cryptographic User Authentication & RBAC Engine for NOUS (Phase 10).

Features:
- Pure Python PBKDF2-HMAC-SHA256 Password Hashing (100,000 rounds, 32-byte salt).
- Native HMAC-SHA256 JSON Web Token (JWT) Encoder & Verifier.
- Role-Based Access Control (RBAC): admin, user, guest.
- Durability in SQLite WAL mode (nous_auth.db).
- Zero third-party compilation dependencies (runs natively across Windows/Linux/Mac).
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import secrets
import sqlite3
import time
from typing import Any, Generator, Optional
from pydantic import BaseModel, Field

from backend.app.config import settings

logger = logging.getLogger("nous.security.auth")

AUTH_DB_PATH: Path = settings.PROJECT_ROOT / "data" / "database" / "nous_auth.db"
# Secret key derived from machine or environment
JWT_SECRET_KEY = os.getenv("NOUS_JWT_SECRET", "nous_production_jwt_master_secret_key_987654321")


# ---------------- 1. PASSWORD CRYPTOGRAPHY (PBKDF2-HMAC-SHA256) ----------------

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password using 100,000 iterations of PBKDF2-HMAC-SHA256."""
    salt_bytes = bytes.fromhex(salt) if salt else secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations=100_000)
    return key.hex(), salt_bytes.hex()


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
    salt_bytes = bytes.fromhex(salt_hex)
    expected_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations=100_000)
    return hmac.compare_digest(expected_key.hex(), hash_hex)


# ---------------- 2. NATIVE JWT ENCODER & VERIFIER ----------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(data: dict[str, Any], expires_delta_seconds: float = 86400.0) -> str:
    """Create a signed JWT token using HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = time.time() + expires_delta_seconds
    payload["iat"] = time.time()

    hdr_enc = _b64url_encode(json.dumps(header).encode("utf-8"))
    pay_enc = _b64url_encode(json.dumps(payload).encode("utf-8"))
    msg = f"{hdr_enc}.{pay_enc}".encode("utf-8")

    sig = hmac.new(JWT_SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
    sig_enc = _b64url_encode(sig)

    return f"{hdr_enc}.{pay_enc}.{sig_enc}"


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify an HMAC-SHA256 JWT token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format.")

    hdr_enc, pay_enc, sig_enc = parts
    msg = f"{hdr_enc}.{pay_enc}".encode("utf-8")
    expected_sig = hmac.new(JWT_SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_enc)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid JWT signature.")

    payload = json.loads(_b64url_decode(pay_enc).decode("utf-8"))
    if time.time() > payload.get("exp", 0):
        raise ValueError("JWT token has expired.")

    return payload


# ---------------- 3. USER MODELS & SQLITE PERSISTENCE ----------------

class User(BaseModel):
    id: str
    username: str
    email: str
    role: str = "user"  # admin, user, guest
    is_active: bool = True
    created_at: float


def init_auth_db(db_path: Optional[Path] = None) -> None:
    """Initialize auth SQLite schema in WAL mode."""
    target = db_path or AUTH_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(target)) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        conn.commit()


@contextlib.contextmanager
def get_auth_db(db_path: Optional[Path] = None) -> Generator[sqlite3.Connection, None, None]:
    target = db_path or AUTH_DB_PATH
    if not target.exists():
        init_auth_db(target)
    conn = sqlite3.connect(str(target), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class AuthManager:
    """Coordinates user registration, login, and token generation."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or AUTH_DB_PATH
        init_auth_db(self.db_path)

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """Register a new user with PBKDF2 password hashing."""
        clean_user = username.strip().lower()
        clean_email = email.strip().lower()
        hash_hex, salt_hex = hash_password(password)
        now = time.time()
        user_id = f"usr_{secrets.token_hex(8)}"

        with get_auth_db(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (id, username, email, password_hash, salt, role, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?);
                """, (user_id, clean_user, clean_email, hash_hex, salt_hex, role, now))
                conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(f"User with username '{clean_user}' or email '{clean_email}' already exists.")

        return User(
            id=user_id,
            username=clean_user,
            email=clean_email,
            role=role,
            is_active=True,
            created_at=now,
        )

    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user by username or email and verify password hash."""
        clean_identifier = username_or_email.strip().lower()

        with get_auth_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, password_hash, salt, role, is_active, created_at
                FROM users
                WHERE (username = ? OR email = ?) AND is_active = 1;
            """, (clean_identifier, clean_identifier))
            row = cursor.fetchone()
            if not row:
                return None

            if not verify_password(password, row["password_hash"], row["salt"]):
                return None

            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by id."""
        with get_auth_db(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, email, role, is_active, created_at
                FROM users WHERE id = ?;
            """, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                role=row["role"],
                is_active=bool(row["is_active"]),
                created_at=row["created_at"],
            )


auth_manager = AuthManager()
