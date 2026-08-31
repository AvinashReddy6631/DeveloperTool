import hashlib
import os
import re
import secrets
import uuid

from database import get_connection

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PBKDF2_ITERATIONS = 120_000


def _hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if not stored or "$" not in stored:
        return False
    salt, _digest = stored.split("$", 1)
    return secrets.compare_digest(stored, _hash_password(password, salt))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def ensure_auth_tables():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                id UUID PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_tokens (
                token_hash VARCHAR(64) PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def register_user(email: str, password: str) -> dict:
    email = normalize_email(email)
    password = str(password or "")

    if not EMAIL_PATTERN.match(email):
        raise ValueError("Enter a valid email address.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    user_id = str(uuid.uuid4())
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO app_users (id, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (user_id, email, _hash_password(password)),
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            raise ValueError("An account with that email already exists.") from exc
        raise
    finally:
        cursor.close()
        connection.close()

    return {"id": user_id, "email": email}


def authenticate_user(email: str, password: str) -> dict:
    email = normalize_email(email)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, email, password_hash
            FROM app_users
            WHERE email = %s
            """,
            (email,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if not row or not _verify_password(password, row[2]):
        raise ValueError("Invalid email or password.")

    return {"id": str(row[0]), "email": row[1]}


def issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO auth_tokens (token_hash, user_id)
            VALUES (%s, %s)
            """,
            (_hash_token(token), user_id),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    return token


def revoke_token(token: str) -> None:
    if not token:
        return
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM auth_tokens WHERE token_hash = %s",
            (_hash_token(token),),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def user_from_token(token: str) -> dict | None:
    if not token:
        return None

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT app_users.id, app_users.email
            FROM auth_tokens
            JOIN app_users ON app_users.id = auth_tokens.user_id
            WHERE token_hash = %s
            """,
            (_hash_token(token),),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        connection.close()

    if not row:
        return None

    return {"id": str(row[0]), "email": row[1]}


def parse_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def auth_required() -> bool:
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return os.getenv("AUTH_REQUIRED", "1").lower() not in {"0", "false", "no"}
